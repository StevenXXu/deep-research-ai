"use client";

import Link from "next/link";
import { ArrowRight, BarChart3, Clock, ShieldCheck, LayoutDashboard } from "lucide-react";
import { useUser } from "@clerk/nextjs";

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useUser();

  return (
    <div className="bg-white">
      {/* Navigation */}
      <header className="absolute inset-x-0 top-0 z-50">
        <nav className="flex items-center justify-between p-6 lg:px-8" aria-label="Global">
          <div className="flex lg:flex-1">
            <span className="text-xl font-bold text-indigo-600 tracking-tight">SoloAnalyst</span>
          </div>
          <div className="flex flex-1 justify-end gap-x-6">
            {!isLoaded ? (
                // Loading Skeleton
                <div className="h-8 w-20 bg-gray-100 rounded animate-pulse"></div>
            ) : isSignedIn ? (
                <Link href="/dashboard" className="flex items-center gap-2 rounded-md bg-indigo-50 px-3.5 py-2.5 text-sm font-semibold text-indigo-600 shadow-sm hover:bg-indigo-100">
                    <LayoutDashboard className="w-4 h-4" /> <span className="hidden sm:inline">Go to Dashboard</span><span className="sm:hidden">Dashboard</span>
                </Link>
            ) : (
                <>
                    <Link href="/sign-in" className="text-sm font-semibold leading-6 text-gray-900 flex items-center">Log in</Link>
                    <Link href="/sign-up" className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
                    Sign up
                    </Link>
                </>
            )}
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <div className="relative isolate px-6 pt-24 pb-20 lg:px-8 bg-slate-900 text-white">
        {/* Subtle background glow effect */}
        <div className="absolute inset-x-0 top-0 -z-10 transform-gpu overflow-hidden blur-3xl" aria-hidden="true">
          <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#3b82f6] to-[#8b5cf6] opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"></div>
        </div>

        <div className="mx-auto max-w-3xl py-24 sm:py-32">
          <div className="text-center">
            <div className="inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold text-indigo-400 bg-indigo-500/10 ring-1 ring-indigo-500/20 mb-8">
              The Pre-Meeting Recon Engine
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-white sm:text-7xl mb-8 leading-tight">
              Know Their Hand <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Before The First Call.</span>
            </h1>
            <p className="mt-6 text-xl leading-8 text-gray-300 max-w-2xl mx-auto">
              Just drop a URL. In 3 minutes, our autonomous agents penetrate paywalls, verify funding, and arm you with the hard questions you need to ask. No more blind intro calls.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {!isLoaded ? (
                  <div className="h-14 w-36 bg-slate-800 rounded-full animate-pulse"></div>
              ) : isSignedIn ? (
                  <Link href="/dashboard" className="rounded-full bg-indigo-600 px-8 py-4 text-sm font-bold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 flex items-center gap-2 transition-all">
                    Open Dashboard <ArrowRight className="w-5 h-5" />
                  </Link>
              ) : (
                  <Link href="/sign-up" className="rounded-full bg-indigo-600 px-8 py-4 text-sm font-bold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 flex items-center gap-2 transition-all">
                    Start Your Audit <ArrowRight className="w-5 h-5" />
                  </Link>
              )}
              <a href="/sample" className="text-sm font-semibold leading-6 text-gray-300 hover:text-white transition-colors flex items-center gap-1">
                View Sample Report <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </div>

        {/* Who is this for Section */}
        <div className="bg-slate-50 py-16 border-b border-gray-100">
          <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-gray-500 mb-8">Built as a strategic weapon for</p>
            <div className="flex flex-col sm:flex-row justify-center gap-8 sm:gap-16 items-center">
              <div className="text-gray-900 text-xl font-bold">👼 Angel Investors</div>
              <div className="text-gray-900 text-xl font-bold">📊 M&A Analysts</div>
              <div className="text-gray-900 text-xl font-bold">🚀 Startup Founders</div>
            </div>
          </div>
        </div>

      {/* Feature Section */}
      <div className="bg-white py-24 sm:py-32 border-b border-gray-100">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-bold tracking-widest uppercase text-indigo-600">URL-to-Memo</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Screen deals faster with data-backed reconnaissance.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-4xl">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-10 lg:max-w-none lg:grid-cols-3 lg:gap-y-16">
              <div className="relative pl-16">
                <dt className="text-base font-bold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100">
                    <BarChart3 className="h-6 w-6 text-indigo-600" aria-hidden="true" />
                  </div>
                  The "Ugly Truth" Scanner
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">We cross-reference SimilarWeb traffic and Crunchbase histories to check if their pitch deck matches reality.</dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-bold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100">
                    <ShieldCheck className="h-6 w-6 text-indigo-600" aria-hidden="true" />
                  </div>
                  Founder Detective
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">We scrape job boards and track down past pivots. Know their actual stage before you jump on a call.</dd>
              </div>
              <div className="relative pl-16">
                <dt className="text-base font-bold leading-7 text-gray-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100">
                    <Clock className="h-6 w-6 text-indigo-600" aria-hidden="true" />
                  </div>
                  The Interrogation List
                </dt>
                <dd className="mt-2 text-base leading-7 text-gray-600">Don't ask generic questions. Every report ends with 3-5 aggressive, data-backed questions designed to test their moat.</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="bg-white py-24 sm:py-32 border-b border-gray-100">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-base font-bold tracking-widest uppercase text-indigo-600">Transparent Pricing</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Pay for insights, not for a database seat.
            </p>
          </div>
          <div className="mx-auto max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            
            {/* Trial Card */}
            <div className="bg-slate-50 rounded-3xl p-8 ring-1 ring-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Trial</h3>
              <p className="mt-4 flex items-baseline gap-x-2">
                <span className="text-5xl font-bold tracking-tight text-gray-900">$0</span>
              </p>
              <p className="mt-4 text-sm leading-6 text-gray-600">Test our data depth on your hardest deal.</p>
              <ul className="mt-8 space-y-3 text-sm leading-6 text-gray-600">
                <li className="flex gap-x-3"><ShieldCheck className="h-6 w-5 flex-none text-indigo-600" /> 1 Free Due Diligence Report</li>
                <li className="flex gap-x-3"><ShieldCheck className="h-6 w-5 flex-none text-indigo-600" /> No Credit Card Required</li>
              </ul>
              <Link href="/sign-up" className="mt-8 block rounded-full px-3.5 py-2.5 text-center text-sm font-semibold text-indigo-600 ring-1 ring-inset ring-indigo-200 hover:ring-indigo-300">Get Started</Link>
            </div>

            {/* Pro Card */}
            <div className="bg-slate-900 rounded-3xl p-8 ring-1 ring-slate-900 shadow-xl relative">
              <div className="absolute top-0 right-6 transform -translate-y-1/2">
                <span className="bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Most Popular</span>
              </div>
              <h3 className="text-lg font-semibold text-white">Pro Plan</h3>
              <p className="mt-4 flex items-baseline gap-x-2">
                <span className="text-5xl font-bold tracking-tight text-white">$29</span>
                <span className="text-sm font-semibold leading-6 text-gray-400">/month</span>
              </p>
              <p className="mt-4 text-sm leading-6 text-gray-300">For active investors scanning weekly deal flow.</p>
              <ul className="mt-8 space-y-3 text-sm leading-6 text-gray-300">
                <li className="flex gap-x-3"><ShieldCheck className="h-6 w-5 flex-none text-indigo-400" /> 20 Reports per month ($1.45/each)</li>
                <li className="flex gap-x-3"><ShieldCheck className="h-6 w-5 flex-none text-indigo-400" /> Rollover unused credits</li>
                <li className="flex gap-x-3"><ShieldCheck className="h-6 w-5 flex-none text-indigo-400" /> PDF & Email Delivery</li>
              </ul>
              <Link href="/sign-up" className="mt-8 block rounded-full bg-indigo-500 px-3.5 py-2.5 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-400">Upgrade to Pro</Link>
            </div>

          </div>
        </div>
      </div>

      {/* Founder's Letter / About Us Section */}
      <div className="bg-slate-50 py-24 sm:py-32 border-t border-gray-100 relative overflow-hidden">
        {/* Subtle background decoration */}
        <div className="absolute inset-y-0 right-1/2 -z-10 mr-16 w-[200%] origin-bottom-left skew-x-[-30deg] bg-white shadow-xl shadow-indigo-600/10 ring-1 ring-indigo-50 sm:mr-28 lg:mr-0 xl:mr-16 xl:origin-center" />
        
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-left">
            <h2 className="text-base font-bold tracking-widest uppercase text-indigo-600 mb-2">Our Mission</h2>
            <h2 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl mb-8">The Table is Flipped.</h2>
            <div className="space-y-6 text-lg leading-8 text-gray-600 bg-white p-8 sm:p-10 rounded-2xl shadow-sm border border-gray-200">
              <p>
                For solo investors and startup founders, time is your most expensive asset.
              </p>
              <p>
                You look at dozens of companies a week. You don't have the time to spend 4 hours running deep diligence on every single one before the first meeting. But walking into a call blind, armed with nothing but a polished Pitch Deck and a Google search, is how bad deals are made.
              </p>
              <p>
                That's why we built <strong>SoloAnalyst</strong>.
              </p>
              <p>
                For the price of a cup of coffee, our agent swarm rips through the PR packaging. It checks the traffic they claim against reality. It pulls the actual funding history. It reverse-engineers their hiring board. And it generates the exact 3-5 hard-hitting questions you need to ask them.
              </p>
              <p className="font-bold text-indigo-600 text-xl mt-8">
                Stop being pitched to. Start interrogating.
              </p>
              <p>
                Get the institutional-grade recon you need, right when you need it.
              </p>
              <p className="mt-8 text-base font-bold text-gray-900 border-t border-gray-100 pt-6">
                — The SoloAnalyst Team
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Upsell / Waitlist Section */}
      <div className="bg-slate-900 py-16">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white mb-4">Need a full Data Room audit?</h2>
          <p className="text-gray-400 max-w-2xl mx-auto mb-8">
            SoloAnalyst provides rapid pre-meeting recon. But if you have access to a company's data room (financials, cap tables, legal docs) and need a comprehensive technical and financial due diligence audit, we are building something for you.
          </p>
          <a href="mailto:support@soloanalyst.com?subject=Enterprise%20Audit%20Waitlist" className="inline-block rounded-full bg-white/10 px-6 py-3 text-sm font-semibold text-white hover:bg-white/20 ring-1 ring-inset ring-white/20 transition-all">
            Join Enterprise Waitlist →
          </a>
        </div>
      </div>

    </div>
  );
}