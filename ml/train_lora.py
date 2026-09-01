"""
LoRA Fine-Tuning Script for Travel Narration — Phase 5
Trains Llama 3.2 3B Instruct on atmospheric travel writing using Unsloth + PEFT + TRL.
Runs on single GPU (Google Colab free T4, A10G, RTX 3090/4090, or Apple Silicon).

Usage:
    python ml/train_lora.py
"""
import os
import json
import torch
from datasets import Dataset

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL_NAME = "unsloth/Llama-3.2-3B-Instruct-bnb-4bit"
MAX_SEQ_LENGTH = 512
LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.0
BATCH_SIZE = 2
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs", "lora_model")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset", "train.jsonl")
EVAL_PATH = os.path.join(os.path.dirname(__file__), "dataset", "eval.jsonl")

SYSTEM_PROMPT = (
    "You are an expert travel writer specializing in evocative, atmospheric, "
    "and sensory travel narrations for day-by-day itineraries. You avoid generic clichés "
    "and capture the authentic spirit of each place in 1-2 vivid sentences."
)

def formatting_prompts_func(examples):
    """Format instruction/input/output into Llama 3.2 ChatML format."""
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        user_content = f"{instruction}\n\nContext & Atmosphere: {input_text}" if input_text else instruction
        text = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
            f"{SYSTEM_PROMPT}<|eot_id|>\n"
            f"<|start_header_id|>user<|end_header_id|>\n\n"
            f"{user_content}<|eot_id|>\n"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            f"{output}<|eot_id|>"
        )
        texts.append(text)
    return {"text": texts}


def load_jsonl_dataset(path: str) -> Dataset:
    """Load JSONL into HuggingFace Dataset."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return Dataset.from_list(records)


def train():
    print(f"Loading base model: {MODEL_NAME} with max_seq_length={MAX_SEQ_LENGTH}...")

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError:
        print("Note: Unsloth or TRL not installed locally. To train, run in Google Colab with GPU:")
        print("  pip install unsloth trl datasets transformers peft bitsandbytes")
        return

    # 1. Load model with 4-bit quantization
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,               # Auto-detection (float16 for T4, bfloat16 for Ampere+)
        load_in_4bit=True,
    )

    # 2. Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # 3. Load & format dataset
    print(f"Loading training data from {DATASET_PATH}...")
    raw_train = load_jsonl_dataset(DATASET_PATH)
    train_dataset = raw_train.map(formatting_prompts_func, batched=True)

    raw_eval = load_jsonl_dataset(EVAL_PATH)
    eval_dataset = raw_eval.map(formatting_prompts_func, batched=True)

    print(f"Training on {len(train_dataset)} examples, evaluating on {len(eval_dataset)}...")

    # 4. Trainer setup
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
            warmup_ratio=0.05,
            num_train_epochs=NUM_EPOCHS,
            learning_rate=LEARNING_RATE,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            evaluation_strategy="steps",
            eval_steps=20,
            output_dir=OUTPUT_DIR,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
        ),
    )

    # 5. Train
    print("Starting LoRA fine-tuning...")
    trainer.train()

    # 6. Save LoRA weights & tokenizer
    print(f"Saving fine-tuned adapter to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # 7. Export to GGUF for Ollama
    gguf_output = os.path.join(os.path.dirname(__file__), "outputs", "travel-narrator-q4_k_m.gguf")
    print(f"Exporting GGUF for Ollama to {gguf_output}...")
    try:
        model.save_pretrained_gguf(
            os.path.join(os.path.dirname(__file__), "outputs", "gguf"),
            tokenizer,
            quantization_method="q4_k_m"
        )
        print("GGUF export successful!")
    except Exception as e:
        print(f"GGUF direct export notice: {e}")

    print("LoRA training pipeline complete!")

if __name__ == "__main__":
    train()
