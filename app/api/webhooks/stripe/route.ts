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
            // Check if Admin Client is valid
            const { data: checkData, error: checkError } = await supabaseAdmin.from('profiles').select('user_id').eq('user_id', userId).single();
            
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
            const { error: updateError } = await supabaseAdmin.from('profiles').update({
                subscription_status: 'active',
                credits_remaining: 20  // Changed from 30 to 20 per month ($1.45/unit)
            }).eq('user_id', userId);
            
            if (updateError) {
                console.error(`[WEBHOOK_ERROR] Update Failed: ${updateError.message}`);
                return new NextResponse("Database Update Failed", { status: 500 });
            }
            
            console.log(`[WEBHOOK] SUCCESS! Upgraded user ${userId} to Pro (20 credits).`);
        } else {
            console.warn(`[WEBHOOK_WARN] No userId in session metadata.`);
        }
    }

    return new NextResponse(null, { status: 200 });
  } catch (err) {
      console.error(`[WEBHOOK_CRITICAL] ${err}`);
      return new NextResponse("Internal Server Error", { status: 500 });
  }
}