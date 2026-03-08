"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import { LayoutDashboard, FileText, Settings, CreditCard, Menu, X, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase"; 

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { user } = useUser();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
      if (!user) return;
      // Fetch role
      supabase.from("profiles").select("role").eq("user_id", user.id).single()
        .then(({ data }) => {
            if (data?.role === 'admin') setIsAdmin(true);
        });
  }, [user]);

  const NavLinks = () => (
    <>
      <Link href="/dashboard" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 hover:text-indigo-600 transition-colors group">
        <LayoutDashboard className="w-5 h-5 mr-3 text-gray-400 group-hover:text-indigo-500" />
        New Research
      </Link>
      <Link href="/dashboard/history" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 hover:text-indigo-600 transition-colors group">
        <FileText className="w-5 h-5 mr-3 text-gray-400 group-hover:text-indigo-500" />
        History
      </Link>
      <Link href="/dashboard/billing" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 hover:text-indigo-600 transition-colors group">
        <CreditCard className="w-5 h-5 mr-3 text-gray-400 group-hover:text-indigo-500" />
        Billing
      </Link>
      
      {isAdmin && (
          <div className="pt-4 mt-4 border-t border-gray-100">
            <div className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Admin</div>
            <Link href="/admin" onClick={() => setIsMobileMenuOpen(false)} className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-indigo-50 hover:text-indigo-700 transition-colors group bg-indigo-50/50">
                <ShieldCheck className="w-5 h-5 mr-3 text-indigo-500" />
                Mission Control
            </Link>
          </div>
      )}
    </>
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col">
        <div className="p-6 h-16 flex items-center border-b border-gray-100">
          <span className="text-xl font-bold text-indigo-600 tracking-tight">Deep Research</span>
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <NavLinks />
        </nav>
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 px-2">
            <UserButton showName />
          </div>
        </div>
      </aside>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 bg-gray-800/50 md:hidden" onClick={() => setIsMobileMenuOpen(false)}>
          <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="p-4 flex items-center justify-between border-b border-gray-100 h-16">
               <span className="text-xl font-bold text-indigo-600">Deep Research</span>
               <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 text-gray-500">
                 <X className="w-6 h-6" />
               </button>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              <NavLinks />
            </nav>
            <div className="p-4 border-t border-gray-200">
               <UserButton showName />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4">
           <div className="flex items-center gap-3">
             <button onClick={() => setIsMobileMenuOpen(true)} className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-md">
               <Menu className="w-6 h-6" />
             </button>
             <span className="text-lg font-bold text-indigo-600">Deep Research</span>
           </div>
           <UserButton />
        </div>
        
        <div className="flex-1 overflow-auto p-4 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}