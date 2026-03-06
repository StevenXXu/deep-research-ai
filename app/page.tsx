"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [file, setFile] = useState<File | null>(null);
  
  // Progress State
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Safety Check: File Size
    if (file && file.size > 10 * 1024 * 1024) {
        setStatus("Error: File exceeds 10MB limit.");
        return;
    }

    setLoading(true);
    setStatus("");
    setProgress(0);
    setProgressMsg("Initializing...");
    setJobId(null);

    try {
      const formData = new FormData();
      formData.append("url", url);
      formData.append("email", email);
      if (file) formData.append("file", file);

      // BYPASS VERCEL: Upload directly to Local Tunnel
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://deep-research-ai-production.up.railway.app";
      const DIRECT_ENDPOINT = file ? `${API_BASE}/research-upload` : `${API_BASE}/research`;
      
      const res = await fetch(DIRECT_ENDPOINT, {
        method: "POST",
        headers: file ? { 'Bypass-Tunnel-Reminder': 'true' } : {
            'Content-Type': 'application/json',
            'Bypass-Tunnel-Reminder': 'true'
        },
        body: file ? formData : JSON.stringify({ url, email }),
      });
      
      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }

      const data = await res.json();
      if (data.job_id) {
          setJobId(data.job_id);
          setStatus("Research Agent Dispatched. Tracking progress...");
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
                      setStatus("Research Complete! Report sent to your email.");
                  }
              }
          } catch (e) {
              console.error("Polling error", e);
          }
      }, 2000); // Poll every 2s

      return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="min-h-screen bg-neutral-900 text-neutral-100 font-sans flex items-center justify-center p-4">
      <div className="max-w-xl w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
            Deep Research <span className="text-indigo-500">AI</span>
          </h1>
          <p className="mt-4 text-lg text-neutral-400">
            Turn any URL into an investment-grade analysis memo.
            <br />Powered by Autonomous Agents.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6 bg-neutral-800 p-8 rounded-xl shadow-2xl border border-neutral-700">
          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="url" className="sr-only">Target URL</label>
              <input
                id="url"
                name="url"
                type="url"
                required
                className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-neutral-600 placeholder-neutral-500 text-white bg-neutral-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Target URL (e.g. https://stripe.com)"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="email" className="sr-only">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="appearance-none rounded-lg relative block w-full px-3 py-3 border border-neutral-600 placeholder-neutral-500 text-white bg-neutral-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Where should we send the report?"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="deck" className="block text-xs text-neutral-400 mb-2">Optional: Upload Deck / Project File (PDF, Word, TXT, MD)</label>
              <input
                id="deck"
                name="deck"
                type="file"
                accept=".pdf,.txt,.md,.docx,.doc"
                className="block w-full text-sm text-neutral-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-neutral-700 file:text-neutral-200 hover:file:bg-neutral-600"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading && !jobId} 
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading && !jobId ? "Starting Agent..." : (loading ? "Researching..." : "Generate Analysis Report")}
            </button>
          </div>

          {/* Progress Bar UI */}
          {loading && jobId && (
              <div className="mt-6 space-y-2">
                  <div className="flex justify-between text-xs font-medium text-indigo-300">
                      <span>{progressMsg}</span>
                      <span>{Math.round(progress)}%</span>
                  </div>
                  <div className="w-full bg-neutral-700 rounded-full h-2.5 overflow-hidden">
                      <div 
                          className="bg-indigo-500 h-2.5 rounded-full transition-all duration-500 ease-out" 
                          style={{ width: `${progress}%` }}
                      ></div>
                  </div>
              </div>
          )}

          {status && !loading && (
            <div className="mt-4 text-center text-sm font-medium text-indigo-300 bg-indigo-900/30 p-3 rounded border border-indigo-800">
              {status}
            </div>
          )}
        </form>
        
        <div className="text-center text-neutral-500 text-xs">
          © 2026 INP Capital. Built by Cipher.
        </div>
      </div>
    </div>
  );
}
