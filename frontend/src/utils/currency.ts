/**
 * Currency Formatting Utility for WanderAI
 * Automatically uses ₹ (INR) for Indian destinations and $ (USD) for international journeys.
 */

const INDIAN_DESTINATION_KEYWORDS = [
  'india',
  'goa',
  'rajasthan',
  'jaipur',
  'mumbai',
  'delhi',
  'new delhi',
  'bengaluru',
  'bangalore',
  'kerala',
  'udaipur',
  'jodhpur',
  'jaisalmer',
  'varanasi',
  'agra',
  'manali',
  'ladakh',
  'rishikesh',
  'pondicherry',
  'puducherry',
  'hampi',
  'mysore',
  'mysuru',
  'kolkata',
  'chennai',
  'hyderabad',
  'amritsar',
  'shimla',
  'darjeeling',
  'munnar',
  'alleppey',
  'kochi',
  'coorg',
  'ooty',
  'andaman',
  'kashmir',
];

export function isIndianDestination(destination?: string): boolean {
  if (!destination) return false;
  const d = destination.toLowerCase().trim();
  return INDIAN_DESTINATION_KEYWORDS.some(k => d.includes(k));
}

export function formatCost(
  costUSD: number | undefined | null,
  destination?: string,
  includeEstSuffix: boolean = true,
): string {
  if (costUSD === undefined || costUSD === null) return '';
  if (costUSD === 0) return 'Free';

  if (isIndianDestination(destination)) {
    // 1 USD ~ 85 INR, rounded to nearest 50 for clean travel budgeting
    const inr = Math.max(50, Math.round((costUSD * 85) / 50) * 50);
    const formatted = `₹${inr.toLocaleString('en-IN')}`;
    return includeEstSuffix ? `${formatted} est.` : formatted;
  }

  const formatted = `$${Math.round(costUSD).toLocaleString('en-US')}`;
  return includeEstSuffix ? `${formatted} est.` : formatted;
}

export function formatTotalCost(
  costUSD: number | undefined | null,
  destination?: string,
): string {
  if (!costUSD) return isIndianDestination(destination) ? '₹0' : '$0';

  if (isIndianDestination(destination)) {
    const inr = Math.round((costUSD * 85) / 100) * 100;
    return `₹${inr.toLocaleString('en-IN')} INR`;
  }

  return `$${Math.round(costUSD).toLocaleString('en-US')} USD`;
}
