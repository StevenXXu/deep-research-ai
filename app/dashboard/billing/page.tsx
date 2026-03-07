"use client";

import { useEffect, useState } from "react";
import { Check, Zap, Loader2 } from "lucide-react";
import { useUser } from "@clerk/nextjs";
import { supabase } from "@/lib/supabase";

export default function BillingPage() {
  const { user } = useUser();
  const [loading, setLoading] = useState(false);
  const [credits, setCredits] = useState(0);
  const [plan, setPlan] = useState("free");

  // Load current status
  useEffect(() => {
      if (!user) return;
      supabase.from('profiles').select('*').eq('user_id', user.id).single()
        .then(({ data }) => {
            if (data) {
                setCredits(data.credits_remaining);
                setPlan(data.subscription_status);
            }
        });
  }, [user]);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/billing/checkout");
      const data = await response.json();
      window.location.href = data.url; // Redirect to Stripe
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Subscription & Credits</h1>
        <p className="mt-2 text-gray-600">Manage your plan and usage.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Current Usage Card */}
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Usage</h3>
            <div className="flex items-end gap-2 mb-2">
                <span className="text-5xl font-bold text-indigo-600">{credits}</span>
                <span className="text-gray-500 mb-2">credits remaining</span>
            </div>
            <p className="text-sm text-gray-500">Each report costs 1 credit.</p>
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="text-sm font-medium text-gray-900">Current Plan: <span className="capitalize">{plan}</span></div>
            </div>
        </div>

        {/* Upgrade Card */}
        <div className="bg-white p-8 rounded-xl shadow-sm border border-indigo-100 ring-1 ring-indigo-500 relative">
            <div className="absolute top-0 right-0 bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">RECOMMENDED</div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Zap className="w-5 h-5 text-indigo-500" /> Pro Plan
            </h3>
            <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-gray-900">$29</span>
                <span className="text-gray-500">/month</span>
            </div>
            <p className="mt-2 text-sm text-gray-500">For active investors & founders.</p>
            
            <ul className="mt-6 space-y-3 text-sm text-gray-600">
                {['30 Credits per month', 'Priority Processing', 'PDF Exports', 'Email Delivery'].map((feat) => (
                    <li key={feat} className="flex gap-2">
                        <Check className="w-5 h-5 text-indigo-500 flex-shrink-0" /> {feat}
                    </li>
                ))}
            </ul>

            <button
                onClick={handleUpgrade}
                disabled={loading}
                className="mt-8 w-full block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-4 rounded-lg text-center transition-colors disabled:opacity-50"
            >
                {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Upgrade to Pro"}
            </button>
        </div>
      </div>
    </div>
  );
}