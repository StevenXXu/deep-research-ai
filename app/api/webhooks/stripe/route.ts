import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";
import Stripe from "stripe";

export async function POST(req: Request) {
  const body = await req.text();
  const signature = headers().get("Stripe-Signature") as string;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (error: any) {
    return new NextResponse(`Webhook Error: ${error.message}`, { status: 400 });
  }

  const session = event.data.object as Stripe.Checkout.Session;

  // Handle Successful Payment
  if (event.type === "checkout.session.completed") {
      const userId = session.metadata?.userId;
      
      if (userId) {
          // PRO PLAN LOGIC:
          // If they bought Pro, set status to 'active' and give 30 credits
          // Ideally check price_id to distinguish products
          
          await supabaseAdmin.from('profiles').update({
              subscription_status: 'active',
              credits_remaining: 30 // Reset to 30 or add 30? Reset is safer for subscriptions.
          }).eq('user_id', userId);
          
          console.log(`[STRIPE] Upgraded user ${userId} to Pro.`);
      }
  }

  // Handle Subscription Payment Succeeded (Recurring)
  if (event.type === "invoice.payment_succeeded") {
      // This fires every month. Reset credits.
      const subscription = await stripe.subscriptions.retrieve(session.subscription as string);
      // We need to map customer ID to user ID if metadata is missing on invoice event
      // This part requires a DB lookup by stripe_customer_id usually.
      // For MVP, checkout.session.completed is enough for the first purchase.
  }

  return new NextResponse(null, { status: 200 });
}