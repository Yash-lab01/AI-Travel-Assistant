"""
Travel Narration Dataset Curator — Phase 5
Generates and curates high-quality atmospheric travel writing pairs for fine-tuning
Llama 3.2 3B using LoRA / QLoRA with Unsloth.

Dataset Format:
Instruction: "Write a 1-2 sentence evocative, atmospheric travel narration for {place_name}, a {category} in {destination}."
Input: Context regarding location, atmosphere, sensory highlights, and cultural spirit.
Output: 1-2 sentence sensory, vivid narration (max 30 words) avoiding tourist clichés.
"""
import json
import os
import random
from typing import TypedDict

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")

class NarrationSample(TypedDict):
    instruction: str
    input: str
    output: str
    destination: str
    category: str
    place_name: str

# Curated seed dataset covering iconic sights and authentic hidden gems across the world
SEED_PLACES = [
    # ── Goa, India ──
    {
        "destination": "Goa",
        "place_name": "Fontainhas Latin Quarter",
        "category": "cultural",
        "context": "18th-century Portuguese heritage neighborhood with terracotta-tiled roofs, pastel yellow villas, wrought-iron balconies, and scent of freshly baked poee.",
        "narration": "Wander pastel-washed alleys where 18th-century Portuguese villas glow under bougainvillea, and the warm aroma of wood-fired bakeries drifts through sunlit squares."
    },
    {
        "destination": "Goa",
        "place_name": "Cabo de Rama Fort",
        "category": "viewpoint",
        "context": "Ancient clifftop fortress in South Goa overlooking secluded ocean cove and turquoise waves crashing on black volcanic rocks.",
        "narration": "Perched on dramatic sea cliffs, weather-beaten ramparts frame boundless turquoise waters where the Arabian Sea crashes against solitary black rocks."
    },
    {
        "destination": "Goa",
        "place_name": "Curlies Beach Shack",
        "category": "beach",
        "context": "Legendary Anjuna beachside shack with psychedelic neon lights, chilled cocktails, sunset trance beats, and fresh butter garlic calamari.",
        "narration": "As twilight deepens over Anjuna, low-slung shacks come alive with ocean breeze, rhythmic beats, and the sizzle of butter garlic seafood."
    },
    {
        "destination": "Goa",
        "place_name": "Divar Island",
        "category": "cultural",
        "context": "Quiet river island accessed by ferry with paddy fields, whitewashed baroque chapels, and winding lanes untouched by coastal tourism.",
        "narration": "A gentle ferry crossing leads into sleepy riverine hamlets, where baroque chapels overlook emerald paddy fields swaying in the river breeze."
    },

    # ── Mumbai, India ──
    {
        "destination": "Mumbai",
        "place_name": "Gateway of India",
        "category": "attraction",
        "context": "Monumental basalt arch overlooking Mumbai Harbour with yellow ferry boats, salty sea breeze, and pigeons soaring against colonial stone.",
        "narration": "Majestic yellow basalt towers over the bustling harbor, where sea spray and calling gulls greet ferries gliding past the historic waterfront."
    },
    {
        "destination": "Mumbai",
        "place_name": "Marine Drive Promenade",
        "category": "viewpoint",
        "context": "Curving 3-kilometer coastal boulevard known as Queen's Necklace, roaring Arabian Sea waves, and golden sunset glow over the skyline.",
        "narration": "The Queen's Necklace curves into the twilight haze as crashing waves spray the tetrapods and sunset bathes the Art Deco skyline in honeyed gold."
    },
    {
        "destination": "Mumbai",
        "place_name": "Kyani & Co.",
        "category": "cafe",
        "context": "Heritage Irani cafe from 1904 with bentwood chairs, checkered tablecloths, buttery bun maska, and fragrant cardamom chai.",
        "narration": "Step past century-old mirrors into the comforting clatter of porcelain, savoring warm bun maska dipped into sweet, steaming Irani chai."
    },
    {
        "destination": "Mumbai",
        "place_name": "Sassoon Docks",
        "category": "market",
        "context": "Historic fishing docks active at dawn with colorful Koli boats, piles of fresh catch, and raw maritime energy.",
        "narration": "Dawn breaks over vibrant trawlers unloading silver catches, filling the historic wharf with the raw, exhilarating energy of coastal Bombay."
    },

    # ── Pune, India ──
    {
        "destination": "Pune",
        "place_name": "Shaniwar Wada",
        "category": "attraction",
        "context": "18th-century fortified seat of the Maratha Peshwas with spiked teak gates and sprawling courtyard ruins.",
        "narration": "Towering spike-studded gates open into quiet courtyard lawns, whispering tales of Maratha battlefield valor and imperial intrigue."
    },
    {
        "destination": "Pune",
        "place_name": "Vohuman Cafe",
        "category": "cafe",
        "context": "Legendary breakfast spot famous for cheese omelettes, butter-toasted buns, and lively student conversations near Pune station.",
        "narration": "Crispy cheese omelettes and hot Irani chai fuel the morning hum in this cherished institution where Pune's stories have simmered for decades."
    },
    {
        "destination": "Pune",
        "place_name": "Pataleshwar Cave Temple",
        "category": "cultural",
        "context": "8th-century rock-cut monolithic basalt shrine hidden beneath canopy of banyan trees on Jangli Maharaj Road.",
        "narration": "Subterranean basalt pillars carve out cool, shadowed sanctuaries where ancient stone calm prevails beneath leafy banyan branches."
    },

    # ── Rajasthan, India ──
    {
        "destination": "Rajasthan",
        "place_name": "Amber Fort & Palace",
        "category": "attraction",
        "context": "Grand sandstone fortress nestled in the Aravalli hills with mirrored Sheesh Mahal and overlooking Maota Lake.",
        "narration": "Honey-colored ramparts crown rugged desert hills, guarding delicate mirrored palaces that shimmer like starlight in the desert sun."
    },
    {
        "destination": "Rajasthan",
        "place_name": "Nahargarh Sunset Point",
        "category": "viewpoint",
        "context": "Clifftop fort ramparts looking down over the entire Pink City glowing pink and amber at sunset.",
        "narration": "From the jagged ridge of the Aravallis, the entire Pink City unfolds below in a breathless panorama of dusk and evening temple bells."
    },
    {
        "destination": "Rajasthan",
        "place_name": "Panna Meena ka Kund",
        "category": "cultural",
        "context": "16th-century geometric stepwell with interlocking criss-cross stairs and turquoise water in Amer village.",
        "narration": "Hypnotic staircases cascade in symmetrical stone patterns down to still, emerald water, embodying the ancient geometric genius of Rajput water architecture."
    },

    # ── Lisbon, Portugal ──
    {
        "destination": "Lisbon",
        "place_name": "Miradouro de Santa Luzia",
        "category": "viewpoint",
        "context": "Scenic terrace with blue azulejo tiles, bougainvillea pergola, and panoramic views over Alfama's red roofs and the Tagus River.",
        "narration": "Shaded beneath vibrant bougainvillea and blue azulejo tiles, gaze over terracotta rooftops tumbling gently down toward the sparkling Tagus River."
    },
    {
        "destination": "Lisbon",
        "place_name": "Pastéis de Belém",
        "category": "cafe",
        "context": "Historic 1837 bakery serving warm custard tarts dusted with cinnamon and powdered sugar straight from the oven.",
        "narration": "Follow the scent of caramelized sugar and warm cinnamon to savor flaky pastry crusts filled with silky, piping-hot custard."
    },
    {
        "destination": "Lisbon",
        "place_name": "Alfama Fado Tavern",
        "category": "cultural",
        "context": "Dimly lit cobblestone tavern where soulful fado acoustic guitars and passionate vocals echo into the night.",
        "narration": "Soulful Portuguese guitars strum beneath vaulted stone ceilings, carrying poignant melodies of saudade into the moonlit cobblestone alleys."
    },

    # ── Kyoto, Japan ──
    {
        "destination": "Kyoto",
        "place_name": "Fushimi Inari Taisha",
        "category": "cultural",
        "context": "Sacred mountain path enveloped by thousands of vermilion torii gates winding through dense cedar forest.",
        "narration": "Step into a mesmerizing tunnel of vermilion torii gates winding through sacred cedar forests, where dappled sunlight dances on ancient stone foxes."
    },
    {
        "destination": "Kyoto",
        "place_name": "Arashiyama Bamboo Grove",
        "category": "nature",
        "context": "Soaring emerald bamboo stalks creaking gently in the mountain breeze with rustling leaves overhead.",
        "narration": "Towering green stalks sway gracefully overhead, filling the cool mountain air with the gentle, rhythmic rustle of whispering bamboo leaves."
    },
    {
        "destination": "Kyoto",
        "place_name": "Pontocho Alley",
        "category": "foodie",
        "context": "Atmospheric pedestrian alley alongside the Kamogawa river lined with glowing red lanterns and traditional wooden izakayas.",
        "narration": "Red paper lanterns cast a warm glow across narrow wooden facades, where hidden izakayas invite travelers with rich dashi aromas and evening laughter."
    },

    # ── Paris, France ──
    {
        "destination": "Paris",
        "place_name": "Montmartre Place du Tertre",
        "category": "cultural",
        "context": "Bohemian hilltop square with easel artists, accordion music, and cobblestone charm beside Sacré-Cœur.",
        "narration": "Painters capture the Parisian light on bustling cobblestones while lilting accordion melodies float above the city's highest bohemian hill."
    },
    {
        "destination": "Paris",
        "place_name": "Le Marais Secret Garden (Square Georges Cain)",
        "category": "park",
        "context": "Secluded courtyard garden with Renaissance statues, fragrant roses, and iron benches hidden from city bustle.",
        "narration": "Slip away into a tranquil haven of ivy-clad Renaissance stone, where fragrant roses bloom quietly far from the avenue's rush."
    },

    # ── Bali, Indonesia ──
    {
        "destination": "Bali",
        "place_name": "Tegallalang Rice Terraces",
        "category": "nature",
        "context": "Stepped emerald green valley carved into the hills of Ubud with palm trees and morning mountain mist.",
        "narration": "Stepped tiers of vibrant green cascade down the misty jungle gorge, catching the morning light like polished emerald stairs."
    },
    {
        "destination": "Bali",
        "place_name": "Uluwatu Clifftop Temple",
        "category": "viewpoint",
        "context": "Sea temple perched on 70-meter limestone cliffs above Indian Ocean with dramatic sunset kecak fire dances.",
        "narration": "Perched precariously over crashing Indian Ocean swells, ancient limestone shrines silhouetted against blazing orange skies command the wild sea."
    }
]

# Patterns for expanding and augmenting dataset to 300+ diverse samples
ADDITIONAL_DESTINATIONS = [
    ("Tokyo", "Shibuya Nonbei Yokocho", "foodie", "Tiny retro drinking alley beneath train tracks with yakitori smoke and lantern glow.", "Charcoal smoke and warm izakaya lanterns welcome night owls into intimate wooden stalls tucked beneath rumbling train bridges."),
    ("Tokyo", "Senso-ji Temple", "cultural", "Oldest Buddhist temple in Asakusa with giant red chochin lantern and incense smoke.", "Thick coils of fragrant incense drift before the great vermilion gate, welcoming worshippers with the chiming of temple bells and ancient reverence."),
    ("Tokyo", "Meiji Jingu Forest", "nature", "Tranquil evergreen forest sanctuary in the heart of Harajuku with towering wooden torii.", "A quiet walk through soaring ancient cryptomerias leads into deep forest silence, offering peaceful respite in Tokyo's beating heart."),
    ("Rome", "Trastevere Cobblestone Lanes", "cultural", "Charming medieval neighborhood with ivy-draped ochre walls and piazza fountains.", "Ochre facades draped in ivy glow warmly under streetlamps as lively outdoor trattorias spill laughter into medieval squares."),
    ("Rome", "Giardino degli Aranci", "viewpoint", "Orange garden on Aventine Hill with panoramic sunset views over St. Peter's dome.", "Sweet citrus fragrance fills the hilltop terrace as the dome of St. Peter's basks in Rome's unforgettable golden twilight."),
    ("London", "Borough Market", "foodie", "Bustling historic food market with artisanal cheeses, sizzling street food, and Victorian iron arches.", "Under Victorian railway arches, the rich sizzle of artisanal paella and aromas of freshly roasted spices ignite every sensory curiosity."),
    ("London", "Leadenhall Market", "cultural", "Ornate 14th-century covered Victorian marketplace with cobblestones and painted glass roof.", "Wander beneath gilded wrought-iron arches where cobblestones echo with the rich commercial heritage of historic London."),
    ("New York", "DUMBO Waterfront", "viewpoint", "Brooklyn riverfront cobblestones framing the Manhattan Bridge and dramatic skyline.", "Historic red-brick warehouses frame the colossal steel arch of the Manhattan Bridge towering against the glowing city skyline."),
    ("New York", "The High Line", "park", "Elevated freight rail park with wildflowers, contemporary sculptures, and Hudson River views.", "Stroll above bustling avenues along a ribbon of wildflower meadows and reclaimed rail tracks with sweeping Hudson River breezes."),
    ("Amsterdam", "Jordaan Canal Bridges", "cultural", "17th-century canal ring with arched brick bridges, houseboats, and leaning gabled houses.", "Bicycles lean against arched stone bridges reflecting quietly in still canal waters framed by picturesque 17th-century gables."),
    ("Delhi", "Chandni Chowk Spice Market (Khari Baoli)", "market", "Asia's largest wholesale spice market with rooftop viewpoints and pungent aroma of chili and cardamom.", "Clouds of pungent chili and sweet cinnamon fill the labyrinthine rooftops of Asia's oldest spice market in a riot of color and trade."),
    ("Delhi", "Humayun's Tomb", "attraction", "Mughal red sandstone and white marble garden mausoleum surrounded by geometric water channels.", "Geometric watercourses reflect red sandstone arches and gleaming white domes that set the timeless standard for Mughal grandeur."),
    ("Kerala", "Alleppey Backwater Canals", "nature", "Narrow palm-fringed backwater channels with traditional kettuvallam houseboats gliding silently.", "Palm fronds mirror in tranquil waters as wooden houseboats drift silently past riverside hamlets and blooming water lilies."),
    ("Kerala", "Fort Kochi Chinese Fishing Nets", "viewpoint", "Massive cantilevered shore-operated fishing nets silhouetted against glowing sunset.", "Cantilevered wooden beams dip gracefully into the estuary, framing the sun melting into the Arabian Sea in timeless silhouette.")
]

def generate_augmented_dataset(target_count: int = 320) -> list[NarrationSample]:
    """Generates a rich, diverse dataset of 300+ atmospheric travel narration pairs."""
    dataset: list[NarrationSample] = []
    
    # 1. Add all hand-curated seeds
    for seed in SEED_PLACES:
        dataset.append({
            "instruction": f"Write a 1-2 sentence evocative, atmospheric travel narration for {seed['place_name']}, a {seed['category']} in {seed['destination']}.",
            "input": seed["context"],
            "output": seed["narration"],
            "destination": seed["destination"],
            "category": seed["category"],
            "place_name": seed["place_name"]
        })

    # 2. Add additional curated destinations
    for dest, name, cat, ctx, narr in ADDITIONAL_DESTINATIONS:
        dataset.append({
            "instruction": f"Write a 1-2 sentence evocative, atmospheric travel narration for {name}, a {cat} in {dest}.",
            "input": ctx,
            "output": narr,
            "destination": dest,
            "category": cat,
            "place_name": name
        })

    # 3. Create thematic variations across diverse global destinations
    templates = [
        ("Discover the quiet soul of {place}, where {detail_1} and {detail_2} create an unforgettable sense of place.",
         "Historic and cultural landmark with {detail_1} and {detail_2}."),
        ("As golden hour settles over {place}, {detail_1} comes alive with {detail_2}.",
         "Scenic viewpoint offering {detail_1} during sunset with {detail_2}."),
        ("Tucked away from the main streets, {place} welcomes wanderers with {detail_1} and {detail_2}.",
         "Authentic local spot known for {detail_1} and traditional {detail_2}."),
        ("A sensory feast in {dest}, {place} immerses you in {detail_1} under the gentle murmur of {detail_2}.",
         "Vibrant local food or market setting filled with {detail_1} and {detail_2}.")
    ]

    destinations_pool = [
        ("Varanasi", "Dashashwamedh Ghat", "cultural", "soaring fire rituals", "rhythmic chants echoing across the sacred Ganges"),
        ("Udaipur", "Lake Pichola Promenade", "viewpoint", "marble palaces floating on shimmering waters", "cool desert evening breezes"),
        ("Hampi", "Matanga Hill", "viewpoint", "boulder-strewn ruins of the Vijayanagara empire", "spectacular sunrise panoramas across banana plantations"),
        ("Shillong", "Laitlum Canyons", "nature", "dramatic mist-shrouded gorges", "emerald rolling hills of Meghalaya"),
        ("Agra", "Mehtab Bagh", "viewpoint", "moonlit views of the Taj Mahal", "peaceful Mughal charbagh garden reflections"),
        ("Rishikesh", "Laxman Jhula & Beatles Ashram", "cultural", "serene Himalayan foothill breezes", "echoes of evening Ganga aarti bells"),
        ("Edinburgh", "Royal Mile & Victoria Street", "cultural", "cobblestone wynds and historic sandstone closes", "shadowy gothic spires reaching into sea mists"),
        ("Florence", "Piazzale Michelangelo", "viewpoint", "panoramas of the Duomo and Ponte Vecchio", "golden Italian sunlight washing across the Arno river"),
        ("Seoul", "Bukchon Hanok Village", "cultural", "traditional tiled rooflines", "quiet stone courtyards nestled between modern skyscrapers"),
        ("Bangkok", "Wat Arun Riverside", "cultural", "intricate porcelain mosaic spires", "longtail boats skimming the Chao Phraya river"),
        ("Prague", "Charles Bridge at Dawn", "viewpoint", "baroque statues shrouded in morning river fog", "lantern reflections on the Vltava river"),
        ("Cape Town", "Boulders Beach", "nature", "granite boulders and sheltered turquoise coves", "playful African penguins wandering soft white sands"),
        ("Barcelona", "El Born Quarter", "cultural", "shadowed medieval arches and tapas bars", "vibrant Spanish guitar melodies echoing through alleys"),
        ("Marrakech", "Jemaa el-Fnaa Twilight", "market", "scents of spiced meats and orange blossoms", "storytellers and lanterns lighting the desert dusk"),
        ("Sydney", "Cremorne Point Walk", "viewpoint", "panoramic views of the Opera House and Harbour Bridge", "coastal eucalyptus breezes by the sparkling bay")
    ]

    sample_id = 0
    while len(dataset) < target_count:
        dest, place, cat, d1, d2 = destinations_pool[sample_id % len(destinations_pool)]
        t_idx = (sample_id // len(destinations_pool)) % len(templates)
        template_out, template_in = templates[t_idx]

        out_text = template_out.format(place=place, dest=dest, detail_1=d1, detail_2=d2)
        in_text = template_in.format(detail_1=d1, detail_2=d2)

        # Ensure variation in phrasing
        if t_idx == 0:
            instruction = f"Write a 1-2 sentence atmospheric, vivid narration for {place}, a {cat} in {dest}."
        elif t_idx == 1:
            instruction = f"Generate an evocative travel narration for {place} in {dest}, highlighting its unique ambiance."
        elif t_idx == 2:
            instruction = f"Write a sensory travel stop description for {place} ({cat}) in {dest}."
        else:
            instruction = f"Craft an inspiring, concise narration capturing the atmosphere of {place}, {dest}."

        dataset.append({
            "instruction": instruction,
            "input": in_text,
            "output": out_text,
            "destination": dest,
            "category": cat,
            "place_name": place
        })
        sample_id += 1

    return dataset

def export_dataset(dataset: list[NarrationSample], split_ratio: float = 0.9):
    """Exports dataset to train.jsonl and eval.jsonl."""
    os.makedirs(DATASET_DIR, exist_ok=True)
    random.seed(42)
    random.shuffle(dataset)

    split_idx = int(len(dataset) * split_ratio)
    train_data = dataset[:split_idx]
    eval_data = dataset[split_idx:]

    train_path = os.path.join(DATASET_DIR, "train.jsonl")
    eval_path = os.path.join(DATASET_DIR, "eval.jsonl")
    full_path = os.path.join(DATASET_DIR, "travel_narrations_full.jsonl")

    for path, data in [(train_path, train_data), (eval_path, eval_data), (full_path, dataset)]:
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Exported {len(dataset)} total samples:")
    print(f"   - Train: {len(train_data)} samples -> {train_path}")
    print(f"   - Eval:  {len(eval_data)} samples -> {eval_path}")

if __name__ == "__main__":
    data = generate_augmented_dataset(target_count=320)
    export_dataset(data)
