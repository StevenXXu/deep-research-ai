import { auth, currentUser } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { stripe, getAbsoluteUrl } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";

const STRIPE_PRICE_ID = process.env.STRIPE_PRICE_ID; // Pro Plan ID

export async function GET(req: Request) {
  try {
    const { userId } = auth();
    const user = await currentUser();

    if (!userId || !user) {
      return new NextResponse("Unauthorized", { status: 401 });
    }

    // 1. Get or Create Stripe Customer ID
    let stripeCustomerId = user.privateMetadata.stripeCustomerId as string;

    // If missing in Clerk, check Supabase or Create New
    if (!stripeCustomerId) {
        const { data: profile } = await supabaseAdmin
            .from('profiles')
            .select('stripe_customer_id')
            .eq('user_id', userId)
            .single();
            
        if (profile?.stripe_customer_id) {
            stripeCustomerId = profile.stripe_customer_id;
        } else {
            // Create new customer in Stripe
            const customer = await stripe.customers.create({
                email: user.emailAddresses[0].emailAddress,
                metadata: {
                    userId: userId,
                }
            });
            stripeCustomerId = customer.id;
            
            // Save back to DB & Clerk
            await supabaseAdmin.from('profiles').update({ stripe_customer_id: stripeCustomerId }).eq('user_id', userId);
            // Clerk metadata update is optional but good for cache
        }
    }

    // 2. Create Checkout Session
    const settingsUrl = getAbsoluteUrl("/dashboard/billing");

    const session = await stripe.checkout.sessions.create({
      customer: stripeCustomerId,
      line_items: [
        {
          price: STRIPE_PRICE_ID,
          quantity: 1,
        },
      ],
      mode: "subscription", // or 'payment' for one-time
      success_url: `${settingsUrl}?success=true`,
      cancel_url: `${settingsUrl}?canceled=true`,
      metadata: {
        userId: userId,
      },
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    console.error("[STRIPE_ERROR]", error);
    return new NextResponse("Internal Error", { status: 500 });
  }
}