import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin as supabase } from "@/lib/supabase"; // Use Admin Client
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  let { userId } = auth();
  
  // Parse body first to check for fallback user_id
  const body = await req.json();

  if (!userId) {
    console.warn("[API] Auth check failed (Cookie missing/invalid). Checking body payload...");
    
    // FALLBACK: Trust the frontend-provided user_id for MVP stability
    if (body.user_id) {
        console.log(`[API] Using fallback user_id from body: ${body.user_id}`);
        userId = body.user_id;
    } else {
        // Real failure
        console.error("[API] Auth Failed. userId is null and no body fallback.");
        const hasSecretKey = !!process.env.CLERK_SECRET_KEY;
        return NextResponse.json({ 
            error: "Unauthorized", 
            details: "User session not found on server.",
            debug_key_present: hasSecretKey 
        }, { status: 401 });
    }
  }

  // 1. Check Credits
  let { data: profile, error } = await supabase
    .from('profiles')
    .select('credits_remaining')
    .eq('user_id', userId)
    .single();

  // SELF-HEALING: If profile missing, create it now (Backend Authority)
  if (!profile) {
      console.log(`[API] Profile missing for ${userId}. Creating new trial profile...`);
      // Use fallback email/name if not available from auth(), but for now just ID is enough for the DB constraint
      // Ideally we want email, but auth() doesn't give email directly without extra calls.
      // We'll trust the body email if present, or placeholder.
      const userEmail = body.email || "unknown@user.com";
      
      const { error: insertError } = await supabase.from('profiles').insert({
          user_id: userId,
          email: userEmail,
          full_name: "User (Auto-Created)",
          credits_remaining: 1 // Default 1 Credit
      });
      
      if (insertError) {
          console.error("[API] Failed to create profile:", insertError);
          return new NextResponse("Database Error: Could not create profile", { status: 500 });
      }
      
      // Re-fetch
      profile = { credits_remaining: 1 };
  }

  if (profile.credits_remaining <= 0) {
      return new NextResponse("Insufficient credits. Please upgrade.", { status: 403 });
  }

  // 2. Decrement Credit
  await supabase
    .from('profiles')
    .update({ credits_remaining: profile.credits_remaining - 1 })
    .eq('user_id', userId);

  // 3. Forward to Python Backend
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://deep-research-ai-production.up.railway.app";
  
  try {
      const res = await fetch(`${API_BASE}/research`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(body) // Re-use the body which contains url, email, user_id
      });
      
      if (!res.ok) {
          const errText = await res.text();
          throw new Error(`Backend Error: ${res.status} ${errText}`);
      }

      const data = await res.json();
      return NextResponse.json(data);
      
  } catch (e) {
      return new NextResponse(`Backend Error: ${String(e)}`, { status: 500 });
  }
}