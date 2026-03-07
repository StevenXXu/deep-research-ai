import { UserButton } from "@clerk/nextjs";
import { LayoutDashboard, FileText, Settings, CreditCard } from "lucide-react";
import Link from "next/link";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col">
        <div className="p-6 h-16 flex items-center border-b border-gray-100">
          <span className="text-xl font-bold text-indigo-600 tracking-tight">Deep Research</span>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <Link href="/dashboard" className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 hover:text-indigo-600 transition-colors group">
            <LayoutDashboard className="w-5 h-5 mr-3 text-gray-400 group-hover:text-indigo-500" />
            New Research
          </Link>
          <Link href="/dashboard/history" className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 hover:text-indigo-600 transition-colors group">
            <FileText className="w-5 h-5 mr-3 text-gray-400 group-hover:text-indigo-500" />
            History
          </Link>
          <Link href="/dashboard/billing" className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 hover:text-indigo-600 transition-colors group">
            <CreditCard className="w-5 h-5 mr-3 text-gray-400 group-hover:text-indigo-500" />
            Billing
          </Link>
        </nav>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 px-2">
            <UserButton showName />
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <div className="md:hidden h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4">
           <span className="text-lg font-bold text-indigo-600">Deep Research</span>
           <UserButton />
        </div>
        
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}