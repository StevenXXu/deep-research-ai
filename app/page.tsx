"use client";

import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Safety Check: File Size
    if (file && file.size > 10 * 1024 * 1024) {
        setStatus("Error: File exceeds 10MB limit.");
        return;
    }

    setLoading(true);
    setStatus("Initiating Deep Research... (This takes 2-3 mins)");

    try {
      const formData = new FormData();
      formData.append("url", url);
      formData.append("email", email);
      if (file) formData.append("file", file);

      // BYPASS VERCEL: Upload directly to Local Tunnel
      // Vercel Serverless has 4.5MB limit. Tunnel allows more.
      const DIRECT_ENDPOINT = "https://tasty-crabs-sing.loca.lt/research-upload";
      
      const res = await fetch(DIRECT_ENDPOINT, {
        method: "POST",
        // 'Bypass-Tunnel-Reminder' is critical for loca.lt
        headers: {
            'Bypass-Tunnel-Reminder': 'true'
        },
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }

      const data = await res.json();
      setStatus(data.message || "Agent Dispatched. Check your email shortly.");
    } catch (err) {
      console.error(err);
      setStatus("Error: " + err);
    }
    setLoading(false);
  };

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
              <label htmlFor="deck" className="block text-xs text-neutral-400 mb-2">Optional: Upload Deck / Project File (PDF, TXT, MD)</label>
              <input
                id="deck"
                name="deck"
                type="file"
                accept=".pdf,.txt,.md"
                className="block w-full text-sm text-neutral-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-neutral-700 file:text-neutral-200 hover:file:bg-neutral-600"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? "Agent Working..." : "Generate Analysis Report"}
            </button>
          </div>

          {status && (
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
