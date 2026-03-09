import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_placeholder', {
  apiVersion: '2024-12-18.acacia', // Use latest API version
  typescript: true,
});

// Helper to get absolute URL
export function getAbsoluteUrl(path: string) {
  // Priority 1: Explicit Public Domain (Set this in Vercel!)
  if (process.env.NEXT_PUBLIC_APP_URL) {
      return `${process.env.NEXT_PUBLIC_APP_URL}${path}`;
  }
  
  // Priority 2: Vercel System URL (Fallback)
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}${path}`;
  }
  
  // Priority 3: Localhost
  return `http://localhost:3000${path}`;
}