"use client";

import { useEffect, useState } from "react";
import { useSession, useUser } from "@clerk/nextjs";
import { createClient } from "@supabase/supabase-js";
import { FileText, Clock, AlertCircle, CheckCircle } from "lucide-react";

type Report = {
  id: string;
  target_url: string;
  status: string;
  created_at: string;
  report_content?: string;
};

export default function HistoryPage() {
  const { user } = useUser();
  const { session } = useSession();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || !session) return;

    async function fetchReports() {
      try {
          // 1. Get Clerk Token designated for Supabase
          // Note: You must create a JWT Template in Clerk named 'supabase' first!
          // If not set up yet, this token might be standard, but let's try injecting the Authorization header.
          const token = await session.getToken({ template: "supabase" });
          
          const supabase = createClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL!,
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            {
              global: { headers: { Authorization: `Bearer ${token}` } },
            }
          );

          const { data, error } = await supabase
            .from("reports")
            .select("*")
            // No .eq("user_id") needed because RLS handles it, but keeping it is safe
            .order("created_at", { ascending: false });

          if (error) {
            console.error("Error fetching history:", error);
          } else {
            setReports(data || []);
          }
      } catch (e) {
          console.error("Auth error:", e);
      } finally {
          setLoading(false);
      }
    }

    fetchReports();
  }, [user, session]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "failed": return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Research History</h1>
        <p className="mt-2 text-gray-600">Your past investment memos and analysis reports.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading history...</div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-300" />
            <h3 className="mt-2 text-sm font-semibold text-gray-900">No reports yet</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new research task.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {report.target_url}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 flex items-center gap-2">
                    {getStatusIcon(report.status)}
                    <span className="capitalize">{report.status}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {report.status === 'completed' && (
                        <button className="text-indigo-600 hover:text-indigo-900">View Report</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}