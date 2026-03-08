"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { supabase } from "@/lib/supabase"; // Client-side client
import { ShieldAlert, TrendingUp, DollarSign, Users, Activity } from "lucide-react";
import Link from "next/link";

type AdminStats = {
  totalReports: number;
  totalCost: number;
  totalUsers: number;
  avgCost: number;
};

type ReportLog = {
  id: string;
  target_url: string;
  company_name: string;
  sector_tags: string[];
  cost_usd: number;
  created_at: string;
  user_email?: string; // Need join for this, or just show ID for now
};

export default function AdminDashboard() {
  const { user, isLoaded } = useUser();
  const [isAdmin, setIsAdmin] = useState(false);
  const [stats, setStats] = useState<AdminStats>({ totalReports: 0, totalCost: 0, totalUsers: 0, avgCost: 0 });
  const [logs, setLogs] = useState<ReportLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoaded || !user) return;

    async function loadAdminData() {
      try {
        // 1. Check Admin Role
        // We use a custom API route for this to be secure, OR relying on RLS.
        // Let's rely on RLS: if query fails/returns empty on 'all profiles', not admin.
        
        // Fetch All Reports (Only Admins can see ALL due to RLS)
        const { data: reports, error: reportError } = await supabase
            .from("reports")
            .select("*")
            .order("created_at", { ascending: false })
            .limit(50);

        if (reportError) throw reportError;
        
        // If we got data, we are admin (or RLS is broken, but we trust RLS)
        setIsAdmin(true);

        // Fetch All Profiles count
        const { count: userCount } = await supabase.from("profiles").select("*", { count: 'exact', head: true });

        // Calculate Stats
        const totalReports = reports?.length || 0; // Note: this is limit 50, need count for real total
        // For MVP stat calculation, let's just sum the fetched ones or do a separate aggregation query
        // Let's do a quick aggregate loop on the fetched 50 for now
        const totalCost = reports?.reduce((sum, r) => sum + (r.cost_usd || 0), 0) || 0;
        
        setStats({
            totalReports: totalReports,
            totalCost: totalCost,
            totalUsers: userCount || 0,
            avgCost: totalReports > 0 ? totalCost / totalReports : 0
        });

        setLogs(reports || []);

      } catch (e) {
        console.error("Admin Load Error:", e);
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    }

    loadAdminData();
  }, [isLoaded, user]);

  if (loading) return <div className="p-20 text-center text-gray-500">Verifying Clearance...</div>;

  if (!isAdmin) {
      return (
          <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
              <ShieldAlert className="w-16 h-16 text-red-500 mb-4" />
              <h1 className="text-2xl font-bold text-gray-900">Access Denied</h1>
              <p className="text-gray-600 mt-2">You do not have clearance level: ADMIN.</p>
              <Link href="/dashboard" className="mt-6 text-indigo-600 hover:underline">Return to Dashboard</Link>
          </div>
      );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                    <ShieldCheck className="w-8 h-8 text-indigo-600" /> Mission Control
                </h1>
                <p className="text-sm text-gray-500 mt-1">Operational Intelligence & Cost Analysis</p>
            </div>
            <div className="flex gap-3">
                <Link href="/dashboard" className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">User View</Link>
            </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatCard title="Total Users" value={stats.totalUsers} icon={<Users className="w-5 h-5 text-blue-600" />} />
            <StatCard title="Reports Generated" value={stats.totalReports} sub="(Last 50)" icon={<Activity className="w-5 h-5 text-purple-600" />} />
            <StatCard title="Total Cost" value={`$${stats.totalCost.toFixed(2)}`} icon={<DollarSign className="w-5 h-5 text-green-600" />} />
            <StatCard title="Avg Cost / Report" value={`$${stats.avgCost.toFixed(3)}`} icon={<TrendingUp className="w-5 h-5 text-orange-600" />} />
        </div>

        {/* Intelligence Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-semibold text-gray-900">Live Feed</h3>
                <span className="text-xs text-gray-400">Real-time data from Railway Engine</span>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sector</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Est. Cost</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                    {logs.map((log) => (
                        <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-xs text-gray-500">{new Date(log.created_at).toLocaleString()}</td>
                            <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                {log.company_name || "Processing..."}
                                <a href={log.target_url} target="_blank" className="block text-xs text-gray-400 font-normal hover:text-indigo-500 truncate max-w-[150px]">{log.target_url}</a>
                            </td>
                            <td className="px-6 py-4">
                                <div className="flex flex-wrap gap-1">
                                    {log.sector_tags?.map(t => (
                                        <span key={t} className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-medium">{t}</span>
                                    ))}
                                </div>
                            </td>
                            <td className="px-6 py-4 text-right text-sm font-mono text-gray-600">
                                ${Number(log.cost_usd || 0).toFixed(3)}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>

      </div>
    </div>
  );
}

function StatCard({ title, value, sub, icon }: any) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-sm font-medium text-gray-500">{title}</p>
                    <h3 className="text-2xl font-bold text-gray-900 mt-2">{value}</h3>
                    {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
                </div>
                <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
            </div>
        </div>
    )
}

import { ShieldCheck } from "lucide-react";