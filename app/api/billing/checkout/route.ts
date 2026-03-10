import { auth, currentUser } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { stripe, getAbsoluteUrl } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";

const STRIPE_PRICE_ID = process.env.STRIPE_PRICE_ID; // Pro Plan ID

export async function GET(req: Request) {
  try {
    let { userId } = auth();
    const user = await currentUser();

    // FALLBACK: Check header if cookie auth fails (Production Fix)
    if (!userId) {
        const userIdHeader = req.headers.get("X-User-ID");
        if (userIdHeader) {
            console.log(`[STRIPE] Using fallback user_id from header: ${userIdHeader}`);
            userId = userIdHeader;
        } else {
            return new NextResponse("Unauthorized: No session or header", { status: 401 });
        }
    }

    if (!user && !userId) {
      return new NextResponse("Unauthorized", { status: 401 });
    }
    
    // User Email Fallback (If currentUser() fails due to auth(), use header email if safe, or fail gracefully)
    // Actually, creating a customer REQUIRES an email.
    // If currentUser() is null, we can't get email easily without passing it from frontend.
    // Let's rely on DB lookup first.
    
    // 1. Get or Create Stripe Customer ID
    let stripeCustomerId = user?.privateMetadata?.stripeCustomerId as string;

    // If missing in Clerk, check Supabase
    if (!stripeCustomerId) {
        const { data: profile } = await supabaseAdmin
            .from('profiles')
            .select('stripe_customer_id, email')
            .eq('user_id', userId)
            .single();
            
        if (profile?.stripe_customer_id) {
            stripeCustomerId = profile.stripe_customer_id;
        } else {
            // Create new customer in Stripe
            // If user object is null (auth bypass), use email from DB profile
            const email = user?.emailAddresses?.[0]?.emailAddress || profile?.email;
            
            if (!email) {
                return new NextResponse("Error: User email not found", { status: 400 });
            }

            const customer = await stripe.customers.create({
                email: email,
                metadata: {
                    userId: userId,
                }
            });
            stripeCustomerId = customer.id;
            
            // Save back to DB
            await supabaseAdmin.from('profiles').update({ stripe_customer_id: stripeCustomerId }).eq('user_id', userId);
        }
    }

    // 2. Create Checkout Session
    const settingsUrl = getAbsoluteUrl("/dashboard/billing");

    if (!STRIPE_PRICE_ID) {
        console.error("[STRIPE_CRITICAL] STRIPE_PRICE_ID is not configured in environment variables!");
        return new NextResponse("Server Configuration Error: Missing Price ID", { status: 500 });
    }

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