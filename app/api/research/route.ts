import { auth } from "@clerk/nextjs/server";
import { supabase } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { userId } = auth();
  
  if (!userId) {
    return new NextResponse("Unauthorized", { status: 401 });
  }

  // 1. Check Credits
  const { data: profile, error } = await supabase
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