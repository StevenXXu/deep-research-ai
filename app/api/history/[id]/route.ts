import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function GET(req: Request, { params }: { params: { id: string } }) {
  let { userId } = auth();
  
  // FALLBACK: Check header if cookie auth fails
  if (!userId) {
      const userIdHeader = req.headers.get("X-User-ID");
      if (userIdHeader) {
          console.log(`[API] Report Detail: Using fallback user_id from header: ${userIdHeader}`);
          userId = userIdHeader;
      } else {
          return new NextResponse("Unauthorized", { status: 401 });
      }
  }

  const { data, error } = await supabaseAdmin
    .from("reports")
    .select("*")
    .eq("id", params.id)
    .eq("user_id", userId) // Ensure user owns the report
    .single();

  if (error) {
      return new NextResponse("Report not found", { status: 404 });
  }

  return NextResponse.json(data);
}