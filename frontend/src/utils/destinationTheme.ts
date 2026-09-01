/**
 * Destination Reactive Theme Utility — Phase 8
 * Dynamically classifies destination archetype and injects reactive CSS variables to root.
 */

export interface DestinationTheme {
  archetype: 'tropical' | 'european' | 'desert' | 'mountain' | 'metropolis';
  accentPrimary: string;
  accentSecondary: string;
  accentGradient: string;
  accentMuted: string;
  accentDim: string;
  badgeGem: string;
  bgGlow: string;
}

const THEME_PRESETS: Record<DestinationTheme['archetype'], DestinationTheme> = {
  tropical: {
    archetype: 'tropical',
    accentPrimary: '#FF6B35', // Sunset Coral
    accentSecondary: '#00C897', // Lagoon
    accentGradient: 'linear-gradient(135deg, #FF6B35 0%, #FFA07A 100%)',
    accentMuted: 'rgba(255, 107, 53, 0.12)',
    accentDim: 'rgba(255, 107, 53, 0.25)',
    badgeGem: '#00E5A3',
    bgGlow: '#4A1500',
  },
  european: {
    archetype: 'european',
    accentPrimary: '#D4AF37', // Warm Gold
    accentSecondary: '#8B5CF6', // Twilight Violet
    accentGradient: 'linear-gradient(135deg, #D4AF37 0%, #F3E5AB 100%)',
    accentMuted: 'rgba(212, 175, 55, 0.12)',
    accentDim: 'rgba(212, 175, 55, 0.25)',
    badgeGem: '#A78BFA',
    bgGlow: '#2E1065',
  },
  desert: {
    archetype: 'desert',
    accentPrimary: '#F4A261', // Dune Amber
    accentSecondary: '#E63946', // Spice Red
    accentGradient: 'linear-gradient(135deg, #F4A261 0%, #E76F51 100%)',
    accentMuted: 'rgba(244, 162, 97, 0.12)',
    accentDim: 'rgba(244, 162, 97, 0.25)',
    badgeGem: '#FB923C',
    bgGlow: '#431407',
  },
  mountain: {
    archetype: 'mountain',
    accentPrimary: '#38BDF8', // Glacier Blue
    accentSecondary: '#10B981', // Pine Green
    accentGradient: 'linear-gradient(135deg, #38BDF8 0%, #0284C7 100%)',
    accentMuted: 'rgba(56, 189, 248, 0.12)',
    accentDim: 'rgba(56, 189, 248, 0.25)',
    badgeGem: '#34D399',
    bgGlow: '#082F49',
  },
  metropolis: {
    archetype: 'metropolis',
    accentPrimary: '#FFBF00', // Golden Amber (Original Nocturnal Voyager)
    accentSecondary: '#00DBE7', // Electric Cyan
    accentGradient: 'linear-gradient(135deg, #FFBF00 0%, #E8A838 100%)',
    accentMuted: 'rgba(255, 191, 0, 0.12)',
    accentDim: 'rgba(255, 191, 0, 0.25)',
    badgeGem: '#A855F7', // Violet
    bgGlow: '#1E1B4B',
  },
};

export function detectDestinationTheme(destination?: string): DestinationTheme {
  if (!destination) return THEME_PRESETS.metropolis;
  const d = destination.toLowerCase().trim();

  // Tropical
  if (
    ['goa', 'bali', 'phuket', 'maldives', 'hawaii', 'caribbean', 'seychelles', 'fiji', 'bahamas', 'krabi', 'langkawi', 'boracay', 'kerala', 'pondicherry', 'andaman'].some(
      (k) => d.includes(k)
    )
  ) {
    return THEME_PRESETS.tropical;
  }

  // Desert / Royal Heritage
  if (
    ['rajasthan', 'jaipur', 'udaipur', 'jodhpur', 'jaisalmer', 'dubai', 'cairo', 'marrakech', 'abu dhabi', 'doha', 'jordan', 'petra', 'egypt', 'morocco'].some(
      (k) => d.includes(k)
    )
  ) {
    return THEME_PRESETS.desert;
  }

  // Mountain / Alpine
  if (
    ['himachal', 'kashmir', 'ladakh', 'manali', 'shimla', 'alps', 'swiss', 'banff', 'aspen', 'kathmandu', 'nepal', 'zermatt', 'leh', 'rishikesh', 'munnar', 'darjeeling', 'sikkim', 'iceland'].some(
      (k) => d.includes(k)
    )
  ) {
    return THEME_PRESETS.mountain;
  }

  // European / Classic
  if (
    ['lisbon', 'paris', 'rome', 'barcelona', 'vienna', 'florence', 'prague', 'amsterdam', 'london', 'madrid', 'venice', 'edinburgh', 'munich', 'greece', 'santorini', 'italy', 'spain', 'france', 'portugal', 'switzerland'].some(
      (k) => d.includes(k)
    )
  ) {
    return THEME_PRESETS.european;
  }

  // Metropolis / Default
  return THEME_PRESETS.metropolis;
}

/**
 * Injects destination-reactive CSS variables onto the document root.
 */
export function applyDestinationTheme(destination?: string): DestinationTheme {
  const theme = detectDestinationTheme(destination);
  if (typeof document !== 'undefined') {
    const root = document.documentElement;
    root.style.setProperty('--amber', theme.accentPrimary);
    root.style.setProperty('--amber-gradient', theme.accentGradient);
    root.style.setProperty('--amber-muted', theme.accentMuted);
    root.style.setProperty('--amber-dim', theme.accentDim);
    root.style.setProperty('--teal', theme.accentSecondary);
    root.style.setProperty('--badge-gem', theme.badgeGem);
    root.style.setProperty('--aurora-glow', theme.bgGlow);
  }
  return theme;
}
