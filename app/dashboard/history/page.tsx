"use client";

import { useEffect, useState } from "react";
import { useSession, useUser } from "@clerk/nextjs";
import { createClient } from "@supabase/supabase-js";
import { FileText, Clock, AlertCircle, CheckCircle, Download } from "lucide-react";
import Link from "next/link";

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
    if (!user) return;

    async function fetchReports() {
      try {
          const res = await fetch("/api/history", {
              headers: {
                  'X-User-ID': user!.id
              }
          });

          if (!res.ok) throw new Error("Failed to fetch history");

          const data = await res.json();
          setReports(data || []);
      } catch (e) {
          console.error("Auth error:", e);
      } finally {
          setLoading(false);
      }
    }

    fetchReports();

    // Auto-refresh the list if any report is processing
    const hasProcessing = reports.some(r => r.status?.startsWith('processing'));
    let interval: NodeJS.Timeout;
    if (hasProcessing) {
        interval = setInterval(fetchReports, 5000);
    }

    return () => {
        if (interval) clearInterval(interval);
    }
  }, [user, reports]);

  const handleDownloadMD = (report: Report) => {
    if (!report.report_content) return;
    const blob = new Blob([report.report_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.target_url.replace(/[^a-z0-9]/gi, '_')}_Analysis.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const getStatusIcon = (status: string) => {
    if (status === "completed") return <CheckCircle className="w-4 h-4 text-emerald-600" />;
    if (status === "failed") return <AlertCircle className="w-4 h-4 text-red-600" />;
    if (status?.startsWith("processing")) return <div className="w-4 h-4 border-2 border-zinc-300 border-t-zinc-700 rounded-full animate-spin"></div>;
    return <Clock className="w-4 h-4 text-amber-600" />;
  };

  const getStatusBadge = (status: string) => {
    if (status === "completed") return "bg-emerald-50 text-emerald-700 border border-emerald-200";
    if (status === "failed") return "bg-red-50 text-red-700 border border-red-200";
    if (status?.startsWith("processing")) return "bg-amber-50 text-amber-700 border border-amber-200";
    return "bg-zinc-100 text-zinc-600 border border-zinc-200";
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Research History</h1>
        <p className="mt-2 text-zinc-500">Your past investment memos and analysis reports.</p>
      </div>

      <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-zinc-400 text-sm">Loading history...</div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="mx-auto h-10 w-10 text-zinc-300" />
            <h3 className="mt-3 text-sm font-semibold text-zinc-700">No reports yet</h3>
            <p className="mt-1 text-sm text-zinc-400">Get started by creating a new research task.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-zinc-100">
              <thead>
                <tr className="bg-zinc-50/50">
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Target</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-zinc-50/60 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-zinc-900 max-w-xs truncate">
                      {report.target_url}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-400">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(report.status)}
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold capitalize ${getStatusBadge(report.status)}`}>
                          {report.status?.replace(':', ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex justify-end items-center gap-3">
                          {report.status === 'completed' && (
                              <>
                                  <button
                                    onClick={() => handleDownloadMD(report)}
                                    className="text-zinc-400 hover:text-zinc-700 p-1.5 hover:bg-zinc-100 rounded transition-colors"
                                    title="Download Markdown"
                                  >
                                      <Download className="w-4 h-4" />
                                  </button>
                                  <Link
                                    href={`/dashboard/history/${report.id}`}
                                    className="text-xs font-semibold text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 border border-zinc-200 rounded px-3 py-1.5 transition-colors"
                                  >
                                      View Report
                                  </Link>
                              </>
                          )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
