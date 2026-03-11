import { ArrowLeft, Printer, FileText } from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function SampleReportPage() {
  const sampleMarkdown = `
# Investment Memo: Samsara Eco

**Target:** Samsara Eco (samsaraeco.com)

## Executive Summary
Samsara Eco is a deep-tech environmental company specializing in infinite plastic recycling. Their proprietary "enzymatic recycling" technology breaks down complex plastics (like unrecyclable PET and polyester) into their core monomers, allowing them to be endlessly recycled into new, virgin-grade plastic. 

With significant recent funding and strong partnerships with brands like Lululemon, the company is moving aggressively from R&D into commercial-scale deployment.

### SWOT Analysis

| Strengths | Weaknesses | Opportunities | Threats |
| :--- | :--- | :--- | :--- |
| **Proprietary Tech:** Patented enzyme technology capable of breaking down complex polymers. | **Capital Intensive:** Building physical biorecycling facilities requires massive CapEx. | **Regulatory Tailwinds:** Global mandates for recycled content in packaging (e.g., EU regulations). | **Unproven Scale:** Enzymatic recycling has historically struggled to achieve cost parity with virgin plastic at massive scale. |
| **Strong Partnerships:** Backed by and partnered with major brands (Lululemon, Main Sequence). | **Long Sales Cycles:** Selling to large chemical and consumer goods companies takes years. | **Expansion to New Plastics:** Tech could potentially be adapted for other hard-to-recycle materials. | **Incumbent Chemical Giants:** Companies like BASF or Dow could develop or acquire competing tech. |
| **High ESG Profile:** Extremely attractive to climate-tech funds and ESG-driven capital. | **Talent Dependency:** Relies heavily on a scarce pool of top-tier bioengineers. | | |

---

## The Ugly Truth: Data Consistency & Hidden Signals

### 1. Crunchbase Funding Data 
*   **Total Funding:** $100M+
*   **Latest Round:** Series A+ (Extended)
*   **Key Investors:** Main Sequence Ventures, Lululemon, Temasek.
*   **Analysis:** The involvement of sovereign wealth (Temasek) and strategic corporate capital (Lululemon) suggests the technology has passed strict technical due diligence, not just standard VC vibe-checks.

### 2. Hiring Detective (Lever/Greenhouse Analysis)
*   **Active Roles:** 18 open positions.
*   **Role Breakdown:** 12 in Bioengineering / Process Engineering, 4 in Facility Operations, 2 in Commercial.
*   **Analysis:** The hiring profile is heavily skewed towards *Scale-up Engineering* rather than fundamental R&D or pure Sales. This validates their claim that they are currently focused on transitioning from lab-scale to building their first major commercial facility.

### 3. Traffic Reality Check (SimilarWeb Proxy)
*   **Monthly Visits:** < 50,000
*   **Bounce Rate:** ~ 65%
*   **Analysis:** Traffic is highly irrelevant for a deep-tech B2B hardware/chemical company. Low traffic is expected and not a red flag. Their buyers are a few dozen global conglomerates, not web consumers.

---

## Founding Team & Track Record

*   **Paul Riley (CEO & Founder):** Serial entrepreneur. Previously founded and exited multiple ventures. Has a strong track record of commercializing complex technologies and raising institutional capital.
*   **Technical Bench:** The core scientific team heavily features PhDs and researchers spun out of the Australian National University (ANU), which is a global hub for this specific enzyme research.
*   **Vetting Conclusion:** The team represents a textbook "Commercial CEO + Academic Spin-out" combo, which is highly preferred by deep-tech VCs. No historical red flags or failed crypto pivots detected.

---

## Exit Strategy & M&A Landscape

**Who buys this?**
1. **Global Chemical Conglomerates (Dow, BASF, LyondellBasell):** They are under immense pressure to decarbonize their supply chains and offer "circular" plastics to their FMCG clients. Acquiring a proven enzymatic process is faster than building it.
2. **Waste Management Giants (Waste Management, Veolia):** Looking to move up the value chain from basic sorting/landfill to high-margin chemical recycling.
3. **IPO:** Possible in a strong climate-tech window, but M&A is the far more likely path given the CapEx requirements.
  `;

  return (
    <div className="bg-gray-50 min-h-screen py-12">
      <div className="max-w-5xl mx-auto pb-20">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 px-4 sm:px-0">
          <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-gray-200 bg-white shadow-sm rounded-full transition-colors">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Sample Report</h1>
                <div className="text-sm text-gray-500 mt-1">
                    Generated by SoloAnalyst AI
                </div>
              </div>
          </div>

          <div className="flex gap-3">
              <Link href="/sign-up" className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm">
                  Run Your Own Audit
              </Link>
          </div>
        </div>

        {/* Report Content (The "Paper" Look) */}
        <div className="bg-white p-8 sm:p-12 rounded-xl shadow-lg border border-gray-200">
          
          <div className="mb-8 border-b-2 border-black pb-4">
              <h1 className="text-3xl font-bold text-black mb-2">CONFIDENTIAL • PRE-SCREEN MEMO</h1>
              <p className="text-sm text-gray-500">Target: samsaraeco.com • Date: {new Date().toLocaleDateString()}</p>
          </div>

          <article className="prose prose-slate prose-lg max-w-none 
              prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-slate-900
              prose-h1:text-3xl prose-h1:mb-6 prose-h1:border-b prose-h1:pb-4
              prose-h2:text-xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:flex prose-h2:items-center prose-h2:gap-2 prose-h2:text-indigo-700
              prose-p:text-slate-600 prose-p:leading-relaxed
              prose-li:text-slate-600
              prose-strong:text-slate-900 prose-strong:font-semibold
              prose-table:border prose-table:shadow-sm prose-table:rounded-lg prose-table:overflow-hidden
              prose-th:bg-slate-50 prose-th:p-4 prose-th:text-slate-700 prose-th:font-bold prose-th:uppercase prose-th:text-xs prose-th:tracking-wider
              prose-td:p-4 prose-td:text-sm prose-td:border-t prose-td:border-slate-100">
              
              <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                      a: ({node, ...props}) => <a {...props} className="text-indigo-600 hover:text-indigo-800 font-medium underline" target="_blank" />,
                      table: ({node, ...props}) => (
                          <div className="my-8 overflow-hidden rounded-lg border border-gray-200 shadow-sm">
                              <table {...props} className="min-w-full divide-y divide-gray-200 bg-white" />
                          </div>
                      ),
                      thead: ({node, ...props}) => <thead {...props} className="bg-gray-50" />,
                      tbody: ({node, ...props}) => <tbody {...props} className="divide-y divide-gray-200 bg-white" />,
                      tr: ({node, ...props}) => <tr {...props} className="hover:bg-gray-50/50 transition-colors" />,
                      th: ({node, ...props}) => <th {...props} className="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider" />,
                      td: ({node, ...props}) => <td {...props} className="px-6 py-4 text-sm text-gray-600 align-top leading-relaxed" />,
                  }}
              >
                  {sampleMarkdown}
              </ReactMarkdown>
          </article>

          <div className="mt-12 pt-8 border-t border-gray-200 text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Want to see the ugly truth about your competitors?</h3>
              <Link href="/sign-up" className="inline-block px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm transition-colors">
                  Start Your Free Trial
              </Link>
          </div>

        </div>
      </div>
    </div>
  );
}