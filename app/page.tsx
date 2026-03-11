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
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Don't bring a Google search<br/><span className="text-indigo-600">to an investment meeting.</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 max-w-2xl mx-auto">
              Get the hard data Pitchbook charges $20k for. Our autonomous agents bypass Cloudflare, extract real traffic data, verify funding rounds, and hunt down founder histories to generate a VC-grade due diligence report in 3 minutes.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {!isLoaded ? (
                  <div className="h-12 w-32 bg-gray-100 rounded-md animate-pulse"></div>
              ) : isSignedIn ? (
                  <Link href="/dashboard" className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 flex items-center gap-2">
                    Open Dashboard <ArrowRight className="w-4 h-4" />
                  </Link>
              ) : (
                  <Link href="/sign-up" className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 flex items-center gap-2">
                    Get Started <ArrowRight className="w-4 h-4" />
                  </Link>
              )}
              <a href="/sample" className="text-sm font-semibold leading-6 text-gray-900">View Sample Report <span aria-hidden="true">→</span></a>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Section */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 pb-24">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h2 className="text-base font-semibold leading-7 text-indigo-600">Deploy Agents</h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need to diligence a startup
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-4xl">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-10 lg:max-w-none lg:grid-cols-3 lg:gap-y-16">
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <BarChart3 className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                The "Ugly Truth" Engine
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">We bypass PR fluff. Our agents extract Crunchbase funding history, cross-reference SimilarWeb traffic, and track down pivot histories via Wayback Machine.</dd>
            </div>
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <ShieldCheck className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                Founder Detective
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">We reverse-engineer job boards and track past exits. Know if they are heavily hiring engineers or just SDRs before you write the check.</dd>
            </div>
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <Clock className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                Bilingual Delivery
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">Looking at overseas deals? We analyze English raw data and output perfectly structured, native-level Chinese PDF reports for your IC meetings.</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Founder's Letter / About Us Section */}
      <div className="bg-slate-50 py-24 sm:py-32 border-t border-gray-100">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-left">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl mb-8">The Table is Flipped.</h2>
            <div className="space-y-6 text-lg leading-8 text-gray-600">
              <p>
                For a long time, the privilege of discovering the next "unicorn" was blocked by a massive data wall.
              </p>
              <p>
                Top-tier VC funds spend tens of thousands of dollars a year on Pitchbook accounts and employ armies of analysts. They use complex systems to monitor real startup traffic, dig up founders' hidden pasts, and uncover the true funding rounds beneath the surface.
              </p>
              <p>
                Meanwhile, solo investors, angels, and everyday founders are left looking at polished PR articles, beautifully faked websites, and inflated Pitch Decks.
              </p>
              <p className="font-semibold text-gray-900">
                This isn't fair. Information asymmetry shouldn't be the only moat for elite capital to harvest the market.
              </p>
              <p>
                That's why we built <strong>SoloAnalyst</strong>. We took the heavy artillery used by Wall Street for due diligence and packed it into a simple search bar. No $20,000 annual fees. No 50-person analyst teams. Just drop a domain, and our autonomous agent swarm will force its way through anti-bot shields, cross-reference dozens of raw data sources, and reverse-engineer hiring signals.
              </p>
              <p>
                In 3 minutes, it hands you the bleeding, unfiltered truth about a company.
              </p>
              <p className="font-bold text-indigo-600 text-xl mt-8">
                Our mission is simple: Break the monopoly on capital information, and give everyone institutional-grade intelligence.
              </p>
              <p>
                When you have the same line of sight as a top VC, why shouldn't you be the one to back the next unicorn?
              </p>
              <p className="mt-8 italic text-sm text-gray-500">
                — The SoloAnalyst Team
              </p>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}