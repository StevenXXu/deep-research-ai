import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function GET(req: Request) {
  let { userId } = auth();
  
  if (!userId) {
      const userIdHeader = req.headers.get("X-User-ID");
      if (userIdHeader) userId = userIdHeader;
  }

  if (!userId) return new NextResponse("Unauthorized", { status: 401 });

  // Verify Admin Role (Double Check)
  const { data: profile } = await supabaseAdmin
    .from("profiles")
    .select("role")
    .eq("user_id", userId)
    .single();

  if (profile?.role !== 'admin') {
      return new NextResponse("Forbidden", { status: 403 });
  }

  // Fetch Data
  const { data: reports } = await supabaseAdmin
    .from("reports")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(50);
    
  const { count: userCount } = await supabaseAdmin.from("profiles").select("*", { count: 'exact', head: true });

  const totalReports = reports?.length || 0;
  const totalCost = reports?.reduce((sum, r) => sum + (r.cost_usd || 0), 0) || 0;
  
  const stats = {
      totalReports,
      totalCost,
      totalUsers: userCount || 0,
      avgCost: totalReports > 0 ? totalCost / totalReports : 0
  };

  return NextResponse.json({ stats, logs: reports });
}