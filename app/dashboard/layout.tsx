"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { LayoutDashboard, FileText, Settings, CreditCard, Menu, X, ShieldCheck, MessageSquareWarning, Loader2 } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState('Feedback');
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const { user } = useUser();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
      if (!user) return;
      // Fetch role via API (Bypasses RLS issues)
      fetch("/api/auth/role", {
          headers: { 'X-User-ID': user.id }
      })
      .then(res => res.json())
      .then(data => {
          if (data.role === 'admin') setIsAdmin(true);
      })
      .catch(e => console.error("Role check failed", e));
  }, [user]);

  const submitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackMessage.trim()) return;
    
    setIsSubmittingFeedback(true);
    setFeedbackStatus('idle');
    
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: feedbackType,
          message: feedbackMessage,
          email: user?.primaryEmailAddress?.emailAddress || ''
        })
      });
      
      if (!res.ok) throw new Error('Failed to submit');
      
      setFeedbackStatus('success');
      setTimeout(() => {
        setIsFeedbackModalOpen(false);
      }, 2000);
    } catch (err) {
      console.error(err);
      setFeedbackStatus('error');
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const NavLinks = () => (
    <>
      <Link href="/dashboard" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-zinc-500 rounded-lg hover:bg-zinc-50 hover:text-zinc-900 transition-colors group">
        <LayoutDashboard className="w-5 h-5 mr-3 text-zinc-400 group-hover:text-zinc-900" />
        New Research
      </Link>
      <Link href="/dashboard/history" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-zinc-500 rounded-lg hover:bg-zinc-50 hover:text-zinc-900 transition-colors group">
        <FileText className="w-5 h-5 mr-3 text-zinc-400 group-hover:text-zinc-900" />
        History
      </Link>
      <Link href="/dashboard/billing" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-zinc-500 rounded-lg hover:bg-zinc-50 hover:text-zinc-900 transition-colors group">
        <CreditCard className="w-5 h-5 mr-3 text-zinc-400 group-hover:text-zinc-900" />
        Billing
      </Link>

      <div className="pt-4 mt-4 border-t border-zinc-100">
        <button onClick={() => { setIsMobileMenuOpen(false); setIsFeedbackModalOpen(true); setFeedbackStatus('idle'); setFeedbackMessage(''); }} className="w-full flex items-center px-4 py-3 text-sm font-medium text-zinc-500 rounded-lg hover:bg-zinc-50 hover:text-zinc-900 transition-colors group">
          <MessageSquareWarning className="w-5 h-5 mr-3 text-zinc-400 group-hover:text-zinc-900" />
          Feedback & Bugs
        </button>
      </div>

      {isAdmin && (
          <div className="pt-4 mt-4 border-t border-zinc-100">
            <div className="px-4 text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Admin</div>
            <Link href="/admin" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-zinc-700 rounded-lg hover:bg-zinc-100 hover:text-zinc-900 transition-colors group bg-zinc-50/50">
                <ShieldCheck className="w-5 h-5 mr-3 text-zinc-500" />
                Mission Control
            </Link>
          </div>
      )}
    </>
  );

  return (
    <div className="flex h-screen bg-zinc-50">
      {/* Desktop Sidebar */}
      <aside className="w-64 bg-white border-r border-zinc-200 hidden md:flex flex-col">
        <div className="p-6 h-16 flex items-center border-b border-zinc-100">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-zinc-900 rounded-sm" />
            <span className="text-base font-bold text-zinc-900 tracking-tight">SoloAnalyst</span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <NavLinks />
        </nav>
        <div className="p-4 border-t border-zinc-200">
          <div className="flex items-center gap-3 px-2">
            <UserButton showName />
          </div>
        </div>
      </aside>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 bg-black/20 md:hidden" onClick={() => setIsMobileMenuOpen(false)}>
          <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="p-4 flex items-center justify-between border-b border-zinc-100 h-16">
               <div className="flex items-center gap-2">
                <div className="w-5 h-5 bg-zinc-900 rounded-sm" />
                <span className="text-base font-bold text-zinc-900 tracking-tight">SoloAnalyst</span>
               </div>
               <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 text-zinc-500 hover:bg-zinc-50 rounded-md">
                 <X className="w-5 h-5" />
               </button>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              <NavLinks />
            </nav>
            <div className="p-4 border-t border-zinc-200">
               <UserButton showName />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden h-16 bg-white border-b border-zinc-200 flex items-center justify-between px-4">
           <div className="flex items-center gap-3">
             <button onClick={() => setIsMobileMenuOpen(true)} className="p-2 -ml-2 text-zinc-600 hover:bg-zinc-100 rounded-md">
               <Menu className="w-6 h-6" />
             </button>
             <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-zinc-900 rounded-sm" />
              <span className="text-sm font-bold text-zinc-900">SoloAnalyst</span>
             </div>
           </div>
           <UserButton />
        </div>

        <div className="flex-1 overflow-auto p-4 md:p-8">
          {children}
        </div>
        {/* Feedback Modal */}
        {isFeedbackModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-zinc-900/40 backdrop-blur-sm sm:p-0">
            <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-xl overflow-hidden border border-zinc-200 transform transition-all">
              <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-100">
                <h3 className="text-lg font-semibold text-zinc-900 tracking-tight">Submit Feedback or Bug</h3>
                <button onClick={() => setIsFeedbackModalOpen(false)} className="text-zinc-400 hover:text-zinc-600 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={submitFeedback} className="p-6">
                <div className="mb-5">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">Type</label>
                  <div className="flex gap-4">
                    <label className="flex items-center cursor-pointer">
                      <input type="radio" value="Feedback" checked={feedbackType === 'Feedback'} onChange={(e) => setFeedbackType(e.target.value)} className="w-4 h-4 text-zinc-900 border-zinc-300 focus:ring-zinc-900" />
                      <span className="ml-2 text-sm font-medium text-zinc-700">Suggestion</span>
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <input type="radio" value="Bug" checked={feedbackType === 'Bug'} onChange={(e) => setFeedbackType(e.target.value)} className="w-4 h-4 text-zinc-900 border-zinc-300 focus:ring-zinc-900" />
                      <span className="ml-2 text-sm font-medium text-zinc-700">Bug Report</span>
                    </label>
                  </div>
                </div>
                
                <div className="mb-6">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">Message</label>
                  <textarea 
                    value={feedbackMessage}
                    onChange={(e) => setFeedbackMessage(e.target.value)}
                    required
                    placeholder={feedbackType === 'Bug' ? "What went wrong?" : "How can we improve SoloAnalyst?"}
                    rows={4}
                    className="w-full px-4 py-3 text-sm border border-zinc-200 rounded-xl bg-zinc-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent transition-all placeholder:text-zinc-400 text-zinc-900 resize-none"
                  ></textarea>
                </div>
                
                {feedbackStatus === 'success' && (
                  <div className="mb-4 p-3 bg-emerald-50 border border-emerald-100 text-emerald-700 text-sm rounded-lg flex items-center">
                    Message sent successfully! Thank you.
                  </div>
                )}
                {feedbackStatus === 'error' && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-100 text-red-700 text-sm rounded-lg flex items-center">
                    Failed to send message. Please try again later.
                  </div>
                )}
                
                <div className="flex justify-end gap-3 pt-2">
                  <button type="button" onClick={() => setIsFeedbackModalOpen(false)} className="px-4 py-2.5 text-sm font-medium text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50 rounded-lg transition-colors">
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    disabled={isSubmittingFeedback || !feedbackMessage.trim()}
                    className="flex items-center justify-center px-6 py-2.5 text-sm font-medium text-white bg-zinc-900 rounded-lg hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSubmittingFeedback ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    {isSubmittingFeedback ? "Sending..." : "Send to Team"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
