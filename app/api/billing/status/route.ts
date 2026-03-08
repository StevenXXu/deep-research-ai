import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function GET(req: Request) {
  let { userId } = auth();
  
  // FALLBACK: Check header if cookie auth fails (consistent with other APIs)
  if (!userId) {
      const userIdHeader = req.headers.get("X-User-ID");
      if (userIdHeader) {
          userId = userIdHeader;
      } else {
          return new NextResponse("Unauthorized", { status: 401 });
      }
  }

  // Admin query to fetch profile
  const { data, error } = await supabaseAdmin
    .from("profiles")
    .select("credits_remaining, subscription_status")
    .eq("user_id", userId)
    .single();

  if (error) {
      console.error("Billing Status Error:", error);
      return new NextResponse("Profile not found", { status: 404 });
  }

  return NextResponse.json(data);
}