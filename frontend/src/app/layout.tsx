import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Travel Assistant — Hidden Gem Itinerary Planner',
  description:
    'A multi-agent AI travel planner that surfaces hidden gems alongside popular attractions — powered by LangGraph, Gemini 2.5 Flash, and a fine-tuned narration model.',
  keywords: ['travel planner', 'AI itinerary', 'hidden gems', 'LangGraph', 'multi-agent'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
