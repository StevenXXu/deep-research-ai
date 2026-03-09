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
  }, [user]);

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
    if (status === "completed") return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (status === "failed") return <AlertCircle className="w-5 h-5 text-red-500" />;
    if (status?.startsWith("processing")) return <div className="w-5 h-5 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>;
    return <Clock className="w-5 h-5 text-yellow-500" />;
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 max-w-xs truncate">
                    {report.target_url}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                        {getStatusIcon(report.status)}
                        <span className="capitalize">{report.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end items-center gap-4">
                        {report.status === 'completed' && (
                            <>
                                <button onClick={() => handleDownloadMD(report)} className="text-gray-400 hover:text-gray-600 transition-colors p-1" title="Download Markdown">
                                    <Download className="w-4 h-4" />
                                </button>
                                <Link href={`/dashboard/history/${report.id}`} className="text-indigo-600 hover:text-indigo-900 font-semibold text-xs border border-indigo-200 rounded px-3 py-1 hover:bg-indigo-50">
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
        )}
      </div>
    </div>
  );
}