"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { ArrowLeft, Calendar, Link as LinkIcon, Download } from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  const { user } = useUser();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;

    async function fetchReport() {
      try {
        const res = await fetch(`/api/history/${params.id}`, {
            headers: {
                'X-User-ID': user!.id
            }
        });
        
        if (!res.ok) throw new Error("Failed to load report");
        
        const data = await res.json();
        setReport(data);
      } catch (e) {
        setError("Report not found or access denied.");
      } finally {
        setLoading(false);
      }
    }

    fetchReport();
  }, [user, params.id]);

  if (loading) return <div className="p-12 text-center text-gray-500">Loading report...</div>;
  if (error) return <div className="p-12 text-center text-red-500">{error}</div>;
  if (!report) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/dashboard/history" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{report.target_url}</h1>
          <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
            <span className="flex items-center gap-1"><Calendar className="w-4 h-4" /> {new Date(report.created_at).toLocaleDateString()}</span>
            <a href={report.target_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-indigo-600">
                <LinkIcon className="w-4 h-4" /> Visit Site
            </a>
          </div>
        </div>
      </div>

      {/* Report Content */}
      <div className="bg-white p-10 rounded-xl shadow-sm border border-gray-200">
        <article className="prose prose-indigo max-w-none">
            <ReactMarkdown>{report.report_content || "*No content available.*"}</ReactMarkdown>
        </article>
      </div>
    </div>
  );
}