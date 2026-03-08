import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function GET(req: Request) {
  let { userId } = auth();
  
  // Fallback for header auth
  if (!userId) {
      const userIdHeader = req.headers.get("X-User-ID");
      if (userIdHeader) userId = userIdHeader;
  }

  if (!userId) return new NextResponse("Unauthorized", { status: 401 });

  const { data, error } = await supabaseAdmin
    .from("profiles")
    .select("role")
    .eq("user_id", userId)
    .single();

  if (error || !data) {
      return NextResponse.json({ role: "user" });
  }

  return NextResponse.json({ role: data.role || "user" });
}