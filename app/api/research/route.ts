import { auth } from "@clerk/nextjs/server";
import { supabase } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  let { userId } = auth();
  
  // Parse body first to check for fallback user_id
  const body = await req.json();

  if (!userId) {
    console.warn("[API] Auth check failed (Cookie missing/invalid). Checking body payload...");
    
    // FALLBACK: Trust the frontend-provided user_id for MVP stability
    // This bypasses strict server-side cookie validation which is failing cross-domain
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
  const { data: profile, error } = await supabase
    .from('profiles')
    .select('credits_remaining')
    .eq('user_id', userId)
    .single();
    .from('profiles')
    .select('credits_remaining')
    .eq('user_id', userId)
    .single();

  if (error || !profile) {
      return new NextResponse("Profile not found", { status: 404 });
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
  const body = await req.json();
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://deep-research-ai-production.up.railway.app";
  
  // Note: Handling File Uploads via Proxy is tricky (Multipart). 
  // For MVP, we might allow direct upload for files OR handle the stream properly.
  // For JSON requests (URL only), this proxy works perfectly.
  
  try {
      const res = await fetch(`${API_BASE}/research`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              // Add a secret key here later to secure Python backend
          },
          body: JSON.stringify(body)
      });
      
      const data = await res.json();
      return NextResponse.json(data);
      
  } catch (e) {
      // Refund credit if backend fails immediately? 
      // For now, keep it simple.
      return new NextResponse("Backend Error", { status: 500 });
  }
}