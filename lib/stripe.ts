import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-12-18.acacia', // Use latest API version
  typescript: true,
});

// Helper to get absolute URL
export function getAbsoluteUrl(path: string) {
  // Check if running on Vercel
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}${path}`;
  }
  // Fallback for local dev
  return `http://localhost:3000${path}`;
}