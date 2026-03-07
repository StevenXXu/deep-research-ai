import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase"; // Use Admin Client to bypass RLS issues
import { NextResponse } from "next/server";

export async function GET(req: Request) {
  let { userId } = auth();
  
  // FALLBACK: Check for custom header if cookie auth fails
  if (!userId) {
      const userIdHeader = req.headers.get("X-User-ID");
      if (userIdHeader) {
          console.log(`[API] History: Using fallback user_id from header: ${userIdHeader}`);
          userId = userIdHeader;
      } else {
          return new NextResponse("Unauthorized", { status: 401 });
      }
  }

  // Admin query (trusted because userId comes from Clerk auth())
  const { data, error } = await supabaseAdmin
    .from("reports")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });

  if (error) {
      console.error("Supabase History Error:", error);
      return new NextResponse(error.message, { status: 500 });
  }

  return NextResponse.json(data);
}