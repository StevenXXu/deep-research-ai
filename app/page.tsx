import Link from "next/link";
import { ArrowRight, BarChart3, Clock, ShieldCheck } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Navigation */}
      <header className="absolute inset-x-0 top-0 z-50">
        <nav className="flex items-center justify-between p-6 lg:px-8" aria-label="Global">
          <div className="flex lg:flex-1">
            <span className="text-xl font-bold text-indigo-600 tracking-tight">Deep Research</span>
          </div>
          <div className="hidden lg:flex lg:flex-1 lg:justify-end gap-x-6">
            <Link href="/sign-in" className="text-sm font-semibold leading-6 text-gray-900">Log in</Link>
            <Link href="/sign-up" className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
              Sign up
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="hidden sm:mb-8 sm:flex sm:justify-center">
            <div className="relative rounded-full px-3 py-1 text-sm leading-6 text-gray-600 ring-1 ring-gray-900/10 hover:ring-gray-900/20">
              New: PDF Export & Resend Integration. <a href="#" className="font-semibold text-indigo-600"><span className="absolute inset-0" aria-hidden="true" />Read more <span aria-hidden="true">&rarr;</span></a>
            </div>
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Investment-Grade Memos, <span className="text-indigo-600">Generated in Minutes.</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Stop spending hours scraping data. Our autonomous agents scan the web, analyze competitors, and write comprehensive pre-screen memos for VCs and Founders.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/dashboard" className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 flex items-center gap-2">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#" className="text-sm font-semibold leading-6 text-gray-900">Live Demo <span aria-hidden="true">→</span></a>
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
                Deep Market Scan
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">We check Reddit, LinkedIn, Google Trends, and Competitor sites to find the truth behind the pitch deck.</dd>
            </div>
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <ShieldCheck className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                Objective Analysis
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">No fluff. No "Buy/Sell" advice. Just raw data, SWOT analysis, and clickable references for your own verification.</dd>
            </div>
            <div className="relative pl-16">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                <div className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                  <Clock className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                Save 4+ Hours/Deal
              </dt>
              <dd className="mt-2 text-base leading-7 text-gray-600">What used to take an analyst half a day now takes 3 minutes. Focus on the meeting, not the googling.</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}