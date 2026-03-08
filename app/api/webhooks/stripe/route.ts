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
            
            if (checkError) {
                 console.error(`[WEBHOOK_ERROR] DB Access Check Failed: ${checkError.message}. Key configured?`);
                 // Don't return 500 yet, try to proceed in case it's just a lookup issue
            }

            // PRO PLAN LOGIC
            const { error: updateError } = await supabaseAdmin.from('profiles').update({
                subscription_status: 'active',
                credits_remaining: 30 
            }).eq('user_id', userId);
            
            if (updateError) {
                console.error(`[WEBHOOK_ERROR] Update Failed: ${updateError.message}`);
                return new NextResponse("Database Update Failed", { status: 500 });
            }
            
            console.log(`[WEBHOOK] SUCCESS! Upgraded user ${userId} to Pro (30 credits).`);
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