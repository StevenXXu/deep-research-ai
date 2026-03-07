"use client";

import { useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { ArrowLeft, Calendar, Link as LinkIcon, Download, Printer, FileText } from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useParams } from "next/navigation";

export default function ReportDetailPage() {
  const { user } = useUser();
  const params = useParams();
  const id = params?.id as string;
  
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user || !id) return;

    async function fetchReport() {
      try {
        const res = await fetch(`/api/history/${id}`, {
            headers: { 'X-User-ID': user!.id }
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
  }, [user, id]);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadMD = () => {
    if (!report) return;
    const blob = new Blob([report.report_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.target_url.replace(/[^a-z0-9]/gi, '_')}_Analysis.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (loading) return <div className="p-12 text-center text-gray-500 animate-pulse">Loading report analysis...</div>;
  if (error) return <div className="p-12 text-center text-red-500 bg-red-50 rounded-lg border border-red-100">{error}</div>;
  if (!report) return null;

  return (
    <div className="max-w-5xl mx-auto pb-20 print:p-0 print:max-w-none">
      {/* Header (Hidden when printing) */}
      <div className="flex items-center justify-between mb-8 print:hidden">
        <div className="flex items-center gap-4">
            <Link href="/dashboard/history" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>
            <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Report Details</h1>
            <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                <span className="flex items-center gap-1"><Calendar className="w-4 h-4" /> {new Date(report.created_at).toLocaleDateString()}</span>
                <a href={report.target_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-indigo-600 transition-colors">
                    <LinkIcon className="w-4 h-4" /> Visit Target
                </a>
            </div>
            </div>
        </div>

        <div className="flex gap-3">
            <button onClick={handleDownloadMD} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors shadow-sm">
                <FileText className="w-4 h-4" /> Download MD
            </button>
            <button onClick={handlePrint} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm">
                <Printer className="w-4 h-4" /> Export PDF
            </button>
        </div>
      </div>

      {/* Report Content (The "Paper" Look) */}
      <div className="bg-white p-12 rounded-xl shadow-lg border border-gray-200 print:shadow-none print:border-none print:p-0">
        
        {/* Print Header */}
        <div className="hidden print:block mb-8 border-b-2 border-black pb-4">
            <h1 className="text-3xl font-bold text-black mb-2">CONFIDENTIAL • PRE-SCREEN MEMO</h1>
            <p className="text-sm text-gray-500">Target: {report.target_url} • Date: {new Date(report.created_at).toLocaleDateString()}</p>
        </div>

        <article className="prose prose-indigo prose-lg max-w-none prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4 prose-p:text-gray-700 prose-li:text-gray-700 prose-table:border prose-table:shadow-sm prose-th:bg-gray-50 prose-th:p-3 prose-td:p-3 print:prose-sm">
            <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                    // Custom Link styling to ensure they are blue
                    a: ({node, ...props}) => <a {...props} className="text-blue-600 hover:underline" target="_blank" />,
                    // Ensure tables scan well
                    table: ({node, ...props}) => <div className="overflow-x-auto my-8"><table {...props} className="min-w-full divide-y divide-gray-300 border border-gray-200" /></div>,
                    th: ({node, ...props}) => <th {...props} className="bg-gray-50 px-3 py-3.5 text-left text-sm font-semibold text-gray-900 border-b border-gray-200" />,
                    td: ({node, ...props}) => <td {...props} className="whitespace-pre-wrap px-3 py-4 text-sm text-gray-500 border-b border-gray-100" />
                }}
            >
                {report.report_content || "*No content available.*"}
            </ReactMarkdown>
        </article>

        {/* Print Footer */}
        <div className="hidden print:block mt-12 pt-4 border-t border-gray-200 text-center text-xs text-gray-400">
            Generated by Deep Research AI • Proprietary & Confidential
        </div>
      </div>
      
      <style jsx global>{`
        @media print {
            body * {
                visibility: hidden;
            }
            .max-w-5xl, .max-w-5xl * {
                visibility: visible;
            }
            .max-w-5xl {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                margin: 0;
                padding: 20px;
            }
            /* Hide Sidebar completely if it exists in layout */
            aside { display: none !important; }
            nav { display: none !important; }
        }
      `}</style>
    </div>
  );
}