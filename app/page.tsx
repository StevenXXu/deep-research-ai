"use client";

import Link from "next/link";
import { ArrowRight, BarChart3, Clock, ShieldCheck, LayoutDashboard } from "lucide-react";
import { useUser } from "@clerk/nextjs";

export default function HomeV2Page() {
  const { isSignedIn, isLoaded } = useUser();

  return (
    <div className="bg-zinc-950 min-h-screen text-white">

      {/* ─── Navigation ─── */}
      <header className="sticky top-0 z-50 bg-zinc-950/70 backdrop-blur-xl border-b border-white/[0.06]">
        <nav className="flex items-center justify-between px-6 py-4 lg:px-8 max-w-6xl mx-auto">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 bg-white rounded-md" />
            <span className="text-base font-bold text-white tracking-tight">SoloAnalyst</span>
          </div>
          <div className="flex items-center gap-5">
            {!isLoaded ? (
              <div className="h-9 w-20 bg-white/10 rounded-lg animate-pulse" />
            ) : isSignedIn ? (
              <Link
                href="/dashboard"
                className="flex items-center gap-2 bg-white text-black text-sm font-semibold px-4 py-2 rounded-lg hover:bg-zinc-200 transition-all"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
            ) : (
              <>
                <Link href="/sign-in" className="text-sm font-medium text-zinc-400 hover:text-white transition-colors">
                  Log in
                </Link>
                <Link
                  href="/sign-up"
                  className="text-sm font-semibold bg-white text-black px-4 py-2 rounded-lg hover:bg-zinc-200 transition-all"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>

      {/* ─── Hero Section ─── */}
      <section className="relative bg-zinc-950 px-6 pt-28 pb-24 lg:px-8 overflow-hidden">
        {/* Radial ambient glow — restrained glass depth */}
        <div
          aria-hidden="true"
          className="absolute pointer-events-none"
          style={{
            top: "0%",
            left: "50%",
            transform: "translateX(-50%)",
            width: "80%",
            height: "80%",
            background:
              "radial-gradient(ellipse at 50% 0%, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 40%, transparent 70%)",
            filter: "blur(60px)",
          }}
        />

        <div className="relative mx-auto max-w-3xl text-center">
          {/* Badge */}
          <div className="inline-flex items-center rounded-full px-4 py-1 text-xs font-semibold font-mono bg-white/5 border border-white/10 text-zinc-400 mb-10 tracking-widest uppercase backdrop-blur-sm">
            The Pre-Meeting Recon Engine
          </div>

          {/* Headline */}
          <h1 className="text-5xl font-extrabold tracking-tighter sm:text-6xl lg:text-7xl mb-8 leading-[1.02]">
            <span className="text-white">Know Their Hand</span>{" "}
            <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-blue-400 to-emerald-400">Before The First Call.</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl leading-8 text-zinc-400 max-w-xl mx-auto">
            Just drop a URL. In 3 minutes, our autonomous agents penetrate paywalls, verify funding, and arm you with the hard questions you need to ask. No more blind intro calls.
          </p>

          {/* CTAs */}
          <div className="mt-12 flex items-center justify-center gap-4 flex-wrap">
            {!isLoaded ? (
              <div className="h-14 w-44 bg-white/10 rounded-lg animate-pulse" />
            ) : isSignedIn ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2.5 bg-white text-black text-sm font-semibold px-8 py-4 rounded-lg hover:bg-zinc-200 transition-all"
              >
                Open Dashboard <ArrowRight className="w-5 h-5" />
              </Link>
            ) : (
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2.5 bg-white text-black text-sm font-semibold px-8 py-4 rounded-lg hover:bg-zinc-200 transition-all"
              >
                Start Your Journey <ArrowRight className="w-5 h-5" />
              </Link>
            )}
            <a
              href="/sample"
              className="inline-flex items-center gap-2 text-sm font-medium text-zinc-400 hover:text-white transition-colors bg-white/[0.04] border border-white/[0.08] backdrop-blur-sm px-6 py-4 rounded-lg hover:bg-white/[0.08] hover:border-white/[0.14]"
            >
              View Sample Report <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* ─── Social Proof ─── */}
      <section className="bg-zinc-950 border-y border-white/[0.05] py-14">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-600 mb-8">
            Built as a strategic weapon for
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-10 sm:gap-18 items-center">
            <div className="text-zinc-300 text-base font-semibold">👼 Angel Investors</div>
            <div className="text-zinc-300 text-base font-semibold">📊 M&A Analysts</div>
            <div className="text-zinc-300 text-base font-semibold">💼 Strategic BDs</div>
          </div>
        </div>
      </section>

      {/* ─── Features Section ─── */}
      <section className="bg-zinc-950 py-28 sm:py-36">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-20">
            <p className="text-xs font-semibold uppercase tracking-widest text-zinc-600 mb-4 font-mono">
              URL-to-Memo
            </p>
            <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Screen deals faster with data-backed reconnaissance.
            </h2>
          </div>

          <div className="mx-auto max-w-5xl">
            <dl className="grid grid-cols-1 gap-4 lg:grid-cols-3">

              {/* Feature 1 */}
              <div className="bg-zinc-900/30 rounded-xl p-8 border border-zinc-800/80 hover:bg-zinc-900/60 transition-colors">
                <dt className="text-base font-bold leading-7 text-white">
                  <div className="flex items-center gap-4 mb-5">
                    <div className="flex-none flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-800/40 border border-zinc-700/50">
                      <BarChart3 className="h-6 w-6 text-zinc-300" aria-hidden="true" />
                    </div>
                    The &quot;Ugly Truth&quot; Scanner
                  </div>
                  <p className="text-sm leading-6 text-zinc-400">
                    We cross-reference SimilarWeb traffic and Crunchbase histories to check if their pitch deck matches reality.
                  </p>
                </dt>
              </div>

              {/* Feature 2 */}
              <div className="bg-zinc-900/30 rounded-xl p-8 border border-zinc-800/80 hover:bg-zinc-900/60 transition-colors">
                <dt className="text-base font-bold leading-7 text-white">
                  <div className="flex items-center gap-4 mb-5">
                    <div className="flex-none flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-800/40 border border-zinc-700/50">
                      <ShieldCheck className="h-6 w-6 text-zinc-300" aria-hidden="true" />
                    </div>
                    Founder Detective
                  </div>
                  <p className="text-sm leading-6 text-zinc-400">
                    We scrape job boards and track down past pivots. Know their actual stage before you jump on a call.
                  </p>
                </dt>
              </div>

              {/* Feature 3 */}
              <div className="bg-zinc-900/30 rounded-xl p-8 border border-zinc-800/80 hover:bg-zinc-900/60 transition-colors">
                <dt className="text-base font-bold leading-7 text-white">
                  <div className="flex items-center gap-4 mb-5">
                    <div className="flex-none flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-800/40 border border-zinc-700/50">
                      <Clock className="h-6 w-6 text-zinc-300" aria-hidden="true" />
                    </div>
                    The Interrogation List
                  </div>
                  <p className="text-sm leading-6 text-zinc-400">
                    Don&apos;t ask generic questions. Every report ends with 3-5 aggressive, data-backed questions designed to test their moat.
                  </p>
                </dt>
              </div>

            </dl>
          </div>
        </div>
      </section>

      {/* ─── Pricing Section ─── */}
      <section className="bg-zinc-950 py-28 sm:py-36 border-t border-white/[0.05]">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-20">
            <p className="text-xs font-semibold uppercase tracking-widest text-zinc-600 mb-4 font-mono">
              Transparent Pricing
            </p>
            <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Pay for insights, not for a database seat.
            </h2>
          </div>

          <div className="mx-auto max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">

            {/* Free Tier Card — Glass */}
            <div className="bg-zinc-900/30 rounded-xl p-8 border border-zinc-800/80 hover:bg-zinc-900/60 transition-colors">
              <h3 className="text-base font-semibold text-white">Trial</h3>
              <div className="mt-5 flex items-baseline gap-x-2">
                <span className="text-5xl font-bold tracking-tight text-white">$0</span>
              </div>
              <p className="mt-4 text-sm leading-6 text-zinc-400">
                Test our data depth on your hardest deal.
              </p>
              <ul className="mt-8 space-y-3.5 text-sm leading-6 text-zinc-400 flex-1">
                <li className="flex gap-3">
                  <ShieldCheck className="h-5 w-5 flex-none text-zinc-600 mt-0.5" />
                  1 Free Due Diligence Report
                </li>
                <li className="flex gap-3">
                  <ShieldCheck className="h-5 w-5 flex-none text-zinc-600 mt-0.5" />
                  No Credit Card Required
                </li>
              </ul>
              <Link
                href="/sign-up"
                className="mt-10 block w-full text-center text-sm font-semibold text-white border border-white/[0.15] bg-white/[0.05] backdrop-blur-sm rounded-lg px-3.5 py-2.5 hover:bg-white/[0.10] hover:border-white/[0.22] transition-all"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Plan Card — Dark Glass Premium */}
            <div className="bg-zinc-900/60 rounded-xl p-8 border border-zinc-700/50 flex flex-col relative">
              {/* Most Popular badge */}
              <div className="absolute top-0 right-8 transform -translate-y-1/2">
                <span className="bg-white text-black text-xs font-bold px-3.5 py-1 rounded-full uppercase tracking-wide">
                  Most Popular
                </span>
              </div>

              <h3 className="text-base font-semibold text-white">Pro Plan</h3>
              <div className="mt-5 flex items-baseline gap-x-2">
                <span className="text-5xl font-bold tracking-tight text-white">$29</span>
                <span className="text-sm font-medium leading-6 text-zinc-400">/month</span>
              </div>
              <p className="mt-4 text-sm leading-6 text-zinc-400">
                For active investors scanning weekly deal flow.
              </p>
              <ul className="mt-8 space-y-3.5 text-sm leading-6 text-zinc-300 flex-1">
                <li className="flex gap-3">
                  <ShieldCheck className="h-5 w-5 flex-none text-zinc-500 mt-0.5" />
                  20 Reports per month ($1.45/each)
                </li>
                <li className="flex gap-3">
                  <ShieldCheck className="h-5 w-5 flex-none text-zinc-500 mt-0.5" />
                  Rollover unused credits
                </li>
                <li className="flex gap-3">
                  <ShieldCheck className="h-5 w-5 flex-none text-zinc-500 mt-0.5" />
                  PDF & Email Delivery
                </li>
              </ul>
              <Link
                href="/sign-up"
                className="mt-10 block w-full text-center text-sm font-semibold bg-white text-black rounded-lg px-3.5 py-2.5 hover:bg-zinc-200 transition-all"
              >
                Upgrade to Pro
              </Link>
            </div>

          </div>
        </div>
      </section>

      {/* ─── Mission Section ─── */}
      <section className="bg-zinc-950 py-28 sm:py-36 border-t border-white/[0.05]">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-zinc-600 mb-4 font-mono">
              Our Mission
            </p>
            {/* Massive headline */}
            <h2 className="text-6xl sm:text-7xl lg:text-8xl font-extrabold tracking-tighter text-white mb-12 leading-[0.95]">
              The Table is<br />Flipped.
            </h2>

            {/* Intelligence memo — dark glass card */}
            <div className="bg-white/[0.03] rounded-2xl p-10 sm:p-12 border border-white/[0.08] backdrop-blur-xl shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <div className="space-y-7 text-base leading-relaxed text-zinc-300">
                <p>
                  For solo investors and dealmakers, time is your most expensive asset.
                </p>
                <p>
                  You look at dozens of companies a week. You don&apos;t have the time to spend 4 hours running deep diligence on every single one before the first meeting. But walking into a call blind, armed with nothing but a polished Pitch Deck and a Google search, is how bad deals are made.
                </p>
                <p>
                  That&apos;s why we built <strong className="text-white font-semibold">SoloAnalyst</strong>.
                </p>
                <p>
                  For the price of a cup of coffee, our agent swarm rips through the PR packaging. It checks the traffic they claim against reality. It pulls the actual funding history. It reverse-engineers their hiring board. And it generates the exact 3-5 hard-hitting questions you need to ask them.
                </p>
                {/* Stark pull quote */}
                <p className="text-xl font-bold text-white leading-snug border-l-2 border-zinc-600 pl-6 my-8">
                  Stop being pitched to. Start interrogating.
                </p>
                <p>
                  Get the institutional-grade recon you need, right when you need it.
                </p>
                <p className="mt-10 text-sm font-semibold text-zinc-400 border-t border-white/[0.08] pt-6">
                  — The SoloAnalyst Team
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Bottom CTA ─── */}
      <section className="bg-zinc-950 py-20 border-t border-white/[0.05]">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white mb-4">
            Need a full Data Room audit?
          </h2>
          <p className="text-zinc-500 max-w-xl mx-auto mb-10 text-sm leading-relaxed">
            SoloAnalyst provides rapid pre-meeting recon. But if you have access to a company&apos;s data room (financials, cap tables, legal docs) and need a comprehensive technical and financial due diligence audit, we are building something for you.
          </p>
          <a
            href="mailto:support@soloanalyst.com?subject=Enterprise%20Audit%20Waitlist"
            className="inline-flex items-center gap-2 text-sm font-semibold text-black bg-white px-6 py-3 rounded-lg hover:bg-zinc-200 transition-all"
          >
            Join Enterprise Waitlist <span aria-hidden="true">→</span>
          </a>
        </div>
      </section>

      {/* ─── Footer Bar ─── */}
      <footer className="bg-zinc-950 border-t border-white/[0.05] px-6 py-5">
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-white/20 rounded-sm" />
            <span className="text-xs font-semibold text-zinc-500">SoloAnalyst</span>
          </div>
          <span className="text-xs text-zinc-600">
            © 2026 SoloAnalyst. All rights reserved.
          </span>
        </div>
      </footer>

    </div>
  );
}
