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

    // Polling logic for Processing Reports
    let interval: NodeJS.Timeout;
    if (report?.status?.startsWith('processing')) {
      interval = setInterval(fetchReport, 3000);
    }

    return () => {
        if (interval) clearInterval(interval);
    };
  }, [user, id, report?.status]);

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

  const isProcessing = report.status?.startsWith('processing');
  
  // Try to extract percentage if it's packed in the status like "processing:45"
  let progressPercent = 0;
  if (report.status?.includes(':')) {
      progressPercent = parseInt(report.status.split(':')[1]) || 0;
  }
  
  const progressText = progressPercent > 0 
    ? `Analysis at ${progressPercent}%...` 
    : "Gathering intelligence...";

  return (
    <div className="max-w-5xl mx-auto pb-20 print:p-0 print:max-w-none">
      {/* Header (Hidden when printing) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 print:hidden">
        <div className="flex items-center gap-4">
            <Link href="/dashboard/history" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>
            <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Report Details</h1>
            <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                <span className="flex items-center gap-1"><Calendar className="w-4 h-4" /> {new Date(report.created_at).toLocaleDateString()}</span>
                <a href={report.target_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-indigo-600 transition-colors">
                    <LinkIcon className="w-4 h-4" /> {report.target_url}
                </a>
            </div>
            </div>
        </div>

        <div className="flex gap-3">
            <button onClick={handleDownloadMD} disabled={isProcessing} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50">
                <FileText className="w-4 h-4" /> Download MD
            </button>
            <button onClick={handlePrint} disabled={isProcessing} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50">
                <Printer className="w-4 h-4" /> Export PDF
            </button>
        </div>
      </div>

      {isProcessing ? (
        <div className="bg-white p-12 rounded-xl shadow-lg border border-gray-200 text-center space-y-6">
            <div className="animate-pulse flex justify-center">
                <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
            </div>
            <div>
                <h2 className="text-xl font-semibold text-gray-900">Research in Progress</h2>
                <p className="text-gray-500 mt-2">{progressText}</p>
            </div>
            <div className="max-w-md mx-auto bg-gray-100 rounded-full h-2.5 mt-4 overflow-hidden">
                <div className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500 ease-out" style={{ width: `${progressPercent}%` }}></div>
            </div>
            <p className="text-sm text-gray-400">This usually takes 2-4 minutes. You can leave this page and come back later.</p>
            
            <div className="mt-8 pt-8 border-t border-gray-100 flex justify-center">
                <button onClick={() => window.location.reload()} className="text-indigo-600 text-sm hover:underline">
                    Refresh Status
                </button>
            </div>
        </div>
      ) : (
        /* Report Content (The "Paper" Look) */
        <div className="bg-white p-12 rounded-xl shadow-lg border border-gray-200 print:shadow-none print:border-none print:p-0">
        
        {/* Print Header */}
        <div className="hidden print:block mb-8 border-b-2 border-black pb-4">
            <h1 className="text-3xl font-bold text-black mb-2">CONFIDENTIAL • PRE-SCREEN MEMO</h1>
            <p className="text-sm text-gray-500">Target: {report.target_url} • Date: {new Date(report.created_at).toLocaleDateString()}</p>
        </div>

        <article className="prose prose-slate prose-lg max-w-none 
            prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-slate-900
            prose-h1:text-3xl prose-h1:mb-6 prose-h1:border-b prose-h1:pb-4
            prose-h2:text-xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:flex prose-h2:items-center prose-h2:gap-2 prose-h2:text-indigo-700
            prose-p:text-slate-600 prose-p:leading-relaxed
            prose-li:text-slate-600
            prose-strong:text-slate-900 prose-strong:font-semibold
            prose-table:border prose-table:shadow-sm prose-table:rounded-lg prose-table:overflow-hidden
            prose-th:bg-slate-50 prose-th:p-4 prose-th:text-slate-700 prose-th:font-bold prose-th:uppercase prose-th:text-xs prose-th:tracking-wider
            prose-td:p-4 prose-td:text-sm prose-td:border-t prose-td:border-slate-100
            print:prose-sm">
            
            <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                    // Custom Link styling
                    a: ({node, ...props}) => <a {...props} className="text-indigo-600 hover:text-indigo-800 font-medium underline decoration-indigo-200 underline-offset-2 transition-colors" target="_blank" />,
                    
                    // Enhanced Table
                    table: ({node, ...props}) => (
                        <div className="my-8 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                            <table {...props} className="min-w-full divide-y divide-gray-200 bg-white" />
                        </div>
                    ),
                    thead: ({node, ...props}) => <thead {...props} className="bg-gray-50" />,
                    tbody: ({node, ...props}) => <tbody {...props} className="divide-y divide-gray-200 bg-white" />,
                    tr: ({node, ...props}) => <tr {...props} className="hover:bg-gray-50/50 transition-colors" />,
                    th: ({node, ...props}) => <th {...props} className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider" />,
                    td: ({node, ...props}) => <td {...props} className="px-6 py-4 text-sm text-gray-600 align-top leading-relaxed" />,
                    
                    // Blockquote for emphasis
                    blockquote: ({node, ...props}) => (
                        <div className="border-l-4 border-indigo-500 bg-indigo-50 p-4 my-6 rounded-r-lg italic text-indigo-900">
                            {props.children}
                        </div>
                    )
                }}
            >
                {report.report_content || "*No content available.*"}
            </ReactMarkdown>
        </article>

        {/* Print Footer */}
        <div className="hidden print:block mt-12 pt-4 border-t border-gray-200 text-center text-xs text-gray-400">
            {`Generated by SoloAnalyst � Proprietary & Confidential � ${new Date().getFullYear()}`}
        </div>
        </div>
      )}
    </div>
  );
}
