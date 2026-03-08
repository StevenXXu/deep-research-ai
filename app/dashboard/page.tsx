"use client";

import { useState, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { UploadCloud, Search, CheckCircle, Loader2 } from "lucide-react";

export default function Dashboard() {
  const { user } = useUser();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [file, setFile] = useState<File | null>(null);
  
  // Load Credits
  const [credits, setCredits] = useState<number | null>(null);
  
  // Progress State
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState("");
  const [showUpgradeModal, setShowUpgradeModal] = useState(false); // UI State for Upsell

  useEffect(() => {
      if (!user) return;
      const { supabase } = require("@/lib/supabase"); // Lazy load
      supabase.from('profiles').select('credits_remaining').eq('user_id', user.id).single()
        .then(({ data }: any) => { if (data) setCredits(data.credits_remaining); });
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    
    // Client-Side Credit Check (Soft Check)
    if (credits !== null && credits <= 0) {
        setShowUpgradeModal(true);
        return;
    }
    
    // Safety Check: File Size
    if (file && file.size > 10 * 1024 * 1024) {
        setStatus("Error: File exceeds 10MB limit.");
        return;
    }

    setLoading(true);
    setStatus("");
    setProgress(0);
    setProgressMsg("Initializing Agent...");
    setJobId(null);

    const userEmail = user.primaryEmailAddress?.emailAddress || "";

    try {
      const formData = new FormData();
      formData.append("url", url);
      formData.append("email", userEmail);
      formData.append("user_id", user.id); // Pass User ID
      if (file) formData.append("file", file);

      // Use Local Proxy for Billing (URL Mode)
      // For File mode, we might need a different strategy, but for now let's try to proxy or handle logic.
      // MVP Strategy: 
      // If URL only: Hit /api/research (Credit Deducted on Server)
      // If File: Hit Direct Backend (Credit Check bypassed for MVP, or we add a deduct step)
      
      let endpoint = "/api/research"; // Local Next.js API
      let headers: HeadersInit = { 'Content-Type': 'application/json' };
      let body: any = JSON.stringify({ url, email: userEmail, user_id: user.id }); // Pass User ID

      if (file) {
          // Fallback for File Upload (Direct to Railway for now to avoid multipart complexity)
          // TODO: Add credit deduction here later
          const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://deep-research-ai-production.up.railway.app";
          endpoint = `${API_BASE}/research-upload`;
          headers = { 'Bypass-Tunnel-Reminder': 'true' }; // Browser sets content-type for FormData
          body = formData;
      }
      
      const res = await fetch(endpoint, {
        method: "POST",
        headers: file ? undefined : headers, // Let browser set boundary for files
        body: body,
      });
      
      // Handle Specific Errors
      if (res.status === 403) {
          // Insufficient Credits (Hard Check from Server)
          setLoading(false);
          setShowUpgradeModal(true);
          return;
      }
      
      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }

      const data = await res.json();
      if (data.job_id) {
          setJobId(data.job_id);
          setStatus("Agent dispatched. Analysis in progress...");
          // Optimistic update: decrement local credit
          if (credits) setCredits(credits - 1);
      } else {
          setStatus(data.message || "Agent Dispatched. Check your email shortly.");
          setLoading(false);
      }
    } catch (err) {
      console.error(err);
      setStatus("Error: " + err);
      setLoading(false);
    }
  };

  // Check/Create Profile on Load
  useEffect(() => {
      if (!user) return;
      
      async function ensureProfile() {
          const { supabase } = await import("@/lib/supabase"); // Dynamic import
          const { data } = await supabase.from('profiles').select('user_id').eq('user_id', user!.id).single();
          
          if (!data) {
              // Create Profile if missing
              const email = user!.primaryEmailAddress?.emailAddress || "";
              const name = user!.fullName || "User";
              await supabase.from('profiles').insert({
                  user_id: user!.id,
                  email: email,
                  full_name: name,
                  credits_remaining: 1 // Free Trial
              });
              console.log("Profile created via Dashboard fallback.");
          }
      }
      ensureProfile();
  }, [user]);

  // Polling Effect
  useEffect(() => {
      if (!jobId) return;

      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://deep-research-ai-production.up.railway.app";
      
      const interval = setInterval(async () => {
          try {
              const res = await fetch(`${API_BASE}/status/${jobId}`);
              if (res.ok) {
                  const data = await res.json();
                  setProgress(data.progress || 0);
                  setProgressMsg(data.status || "Working...");
                  
                  if (data.progress >= 100) {
                      clearInterval(interval);
                      setLoading(false);
                      setStatus("Research Complete! Report sent to " + (user?.primaryEmailAddress?.emailAddress));
                  }
              }
          } catch (e) {
              console.error("Polling error", e);
          }
      }, 2000);

      return () => clearInterval(interval);
  }, [jobId, user]);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 relative animate-in fade-in zoom-in duration-200">
                <button 
                    onClick={() => setShowUpgradeModal(false)}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
                
                <div className="text-center">
                    <div className="mx-auto w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
                        <Loader2 className="w-6 h-6 text-indigo-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Out of Credits</h3>
                    <p className="text-gray-500 mb-6">
                        You've used all your free research credits. Upgrade to Pro to unlock unlimited deep research reports.
                    </p>
                    
                    <a 
                        href="/dashboard/billing" 
                        className="block w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                    >
                        Upgrade Now
                    </a>
                    <button 
                        onClick={() => setShowUpgradeModal(false)}
                        className="mt-3 text-sm text-gray-500 hover:text-gray-700"
                    >
                        Maybe later
                    </button>
                </div>
            </div>
        </div>
      )}

      <div>
        <h1 className="text-3xl font-bold text-gray-900">New Research Task</h1>
        <p className="mt-2 text-gray-600">Enter a company URL to generate a comprehensive pre-screen investment memo.</p>
      </div>

      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">Target URL</label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="url"
                name="url"
                id="url"
                className="block w-full pl-10 pr-12 py-3 border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border"
                placeholder="https://example.com"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Additional Context (Optional)</label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:bg-gray-50 transition-colors cursor-pointer relative">
              <div className="space-y-1 text-center">
                <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600 justify-center">
                  <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none">
                    <span>Upload a file</span>
                    <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] || null)} accept=".pdf,.doc,.docx,.txt" />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">PDF, DOCX, TXT up to 10MB</p>
                {file && (
                    <p className="text-sm text-green-600 font-semibold mt-2 flex items-center justify-center gap-2">
                        <CheckCircle className="w-4 h-4" /> {file.name}
                    </p>
                )}
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading && !jobId}
              className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all ${loading ? 'opacity-75 cursor-not-allowed' : ''}`}
            >
              {loading && !jobId ? (
                  <span className="flex items-center gap-2"><Loader2 className="animate-spin w-4 h-4" /> Starting Agent...</span>
              ) : (loading ? (
                  <span className="flex items-center gap-2"><Loader2 className="animate-spin w-4 h-4" /> Researching...</span>
              ) : (
                  "Generate Report"
              ))}
            </button>
          </div>
        </form>

        {/* Progress UI */}
        {(loading || status) && (
            <div className="mt-8 border-t border-gray-100 pt-6">
                {loading && jobId && (
                    <div className="space-y-3">
                        <div className="flex justify-between text-sm font-medium text-gray-700">
                            <span>{progressMsg}</span>
                            <span className="text-indigo-600">{Math.round(progress)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                            <div 
                                className="bg-indigo-600 h-3 rounded-full transition-all duration-500 ease-out" 
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                        <p className="text-xs text-gray-500 text-center pt-2">This may take 2-3 minutes. You can leave this page.</p>
                    </div>
                )}

                {status && !loading && (
                    <div className={`mt-4 p-4 rounded-lg text-sm font-medium flex items-center gap-3 ${status.includes("Error") ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"}`}>
                        {status.includes("Error") ? (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        ) : (
                            <CheckCircle className="w-5 h-5" />
                        )}
                        {status}
                    </div>
                )}
            </div>
        )}
      </div>
    </div>
  );
}