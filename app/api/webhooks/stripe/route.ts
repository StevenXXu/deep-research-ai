import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";
import Stripe from "stripe";

export async function POST(req: Request) {
  try {
    const body = await req.text();
    // Fix for Next.js 15+: headers() is async
    const headerList = await headers();
    const signature = headerList.get("Stripe-Signature") as string;

    let event: Stripe.Event;

    try {
      event = stripe.webhooks.constructEvent(
        body,
        signature,
        process.env.STRIPE_WEBHOOK_SECRET!
      );
    } catch (error: any) {
      console.error(`[WEBHOOK_ERROR] Signature verification failed: ${error.message}`);
      return new NextResponse(`Webhook Error: ${error.message}`, { status: 400 });
    }

    const session = event.data.object as Stripe.Checkout.Session;
    const eventType = event.type;
    console.log(`[WEBHOOK] Received event: ${eventType}`);

    // Handle Successful Payment
    if (eventType === "checkout.session.completed") {
        const userId = session.metadata?.userId;
        console.log(`[WEBHOOK] Processing Checkout for UserID: ${userId}`);
        
        if (userId) {
            // Fetch current profile to check existing credits
            const { data: profile, error: checkError } = await supabaseAdmin
                .from('profiles')
                .select('user_id, credits_remaining')
                .eq('user_id', userId)
                .single();
            
            if (checkError && checkError.code === 'PGRST116') {
                 // Profile does not exist yet (Clerk webhook might have failed or been delayed)
                 console.log(`[WEBHOOK] Profile not found. Creating fallback profile for ${userId}`);
                 const { error: insertError } = await supabaseAdmin.from('profiles').insert({
                     user_id: userId,
                     email: "stripe-fallback@unknown.com",
                     full_name: "User (Stripe Fallback)",
                     credits_remaining: 20,
                     subscription_status: 'active'
                 });
                 
                 if (insertError) {
                     console.error(`[WEBHOOK_ERROR] Insert Fallback Failed: ${insertError.message}`);
                     return new NextResponse("Database Insert Failed", { status: 500 });
                 }
                 
                 console.log(`[WEBHOOK] SUCCESS! Created and Upgraded user ${userId} to Pro (20 credits).`);
                 return new NextResponse(null, { status: 200 });
            }

            // PRO PLAN LOGIC (If profile exists)
            // We ADD 20 credits to whatever they currently have (allows rolling over and manual top-ups)
            const currentCredits = profile?.credits_remaining || 0;
            const newCredits = currentCredits + 20;

            const { error: updateError } = await supabaseAdmin.from('profiles').update({
                subscription_status: 'active',
                credits_remaining: newCredits
            }).eq('user_id', userId);
            
            if (updateError) {
                console.error(`[WEBHOOK_ERROR] Update Failed: ${updateError.message}`);
                return new NextResponse("Database Update Failed", { status: 500 });
            }
            
            console.log(`[WEBHOOK] SUCCESS! Added 20 credits to user ${userId}. New total: ${newCredits}`);
        } else {
            console.warn(`[WEBHOOK_WARN] No userId in session metadata.`);
        }
    }

    // Handle Recurring Subscription Payments (Monthly Renewal)
    if (eventType === "invoice.payment_succeeded") {
        const invoice = event.data.object as Stripe.Invoice;
        // The first invoice is paid during checkout.session.completed. 
        // We only want to process subsequent recurring invoices to avoid double-crediting.
        if (invoice.billing_reason === 'subscription_cycle') {
            const customerId = invoice.customer as string;
            console.log(`[WEBHOOK] Processing monthly renewal for CustomerID: ${customerId}`);
            
            if (customerId) {
                // Fetch user by stripe_customer_id
                const { data: profile } = await supabaseAdmin
                    .from('profiles')
                    .select('user_id, credits_remaining')
                    .eq('stripe_customer_id', customerId)
                    .single();

                if (profile) {
                    const newCredits = (profile.credits_remaining || 0) + 20;
                    await supabaseAdmin.from('profiles').update({
                        credits_remaining: newCredits
                    }).eq('user_id', profile.user_id);
                    console.log(`[WEBHOOK] SUCCESS! Monthly renewal: added 20 credits to ${profile.user_id}.`);
                } else {
                    console.warn(`[WEBHOOK_WARN] Could not find user with Stripe Customer ID: ${customerId}`);
                }
            }
        }
    }

    return new NextResponse(null, { status: 200 });
  } catch (err) {
      console.error(`[WEBHOOK_CRITICAL] ${err}`);
      return new NextResponse("Internal Server Error", { status: 500 });
  }
}