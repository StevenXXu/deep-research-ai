# Core AI Prompt Templates for the SoloAnalyst Research Engine
# This acts as the "Sandbox" where the Evolver Agent can iterate on prompts overnight.

AUDIT_PROMPT_TEMPLATE = """
You are a QA Lead Auditor.
Target Company: {company}
Target URL: {url}

Task: Review the list of gathered sources. Identify any source that is IRRELEVANT.
CRITICAL: You MUST aggressively flag sources that refer to fiction novels, video games, fictional characters (e.g., magic schools, anime), or completely unrelated companies with the same name.
EXCEPTION: Do NOT exclude sources that explicitly mention "[COMPETITOR DEEP DIVE]" or "[CRUNCHBASE OFFICIAL RECORD]" or "[PITCHBOOK OFFICIAL RECORD]". These are deliberately gathered intelligence items.

Sources:
{source_list_json}

Output JSON ONLY:
{{
    "exclude_ids": [integer indices of bad sources],
    "reason": "Brief explanation of why"
}}
If all look correct, return {{ "exclude_ids": [], "reason": "All clear" }}.
"""

AGENT_1_PROMPT_TEMPLATE = """
Task: Extract factual data strictly about {company} (Domain: {domain}) into a structured JSON format.
{identity_anchor}

Input:
{context_blob}

CRITICAL ENTITY FILTERING (ANTI-HALLUCINATION):
1. ALIAS & PARENT TOLERANCE: If a source discusses a parent company, subsidiary, rebrand, or major partner (e.g., "SpaceX" for "ThemeSpaceX"), DO NOT ignore it. Extract the relevant context but clearly label the relationship. ONLY ignore completely unrelated companies that happen to share a similar name. 
2. Specifically, look at the Official Business Description provided above. If a source describes a company doing something completely different (e.g., if official is "Architectural Code Compliance" and source talks about "Kubernetes Security" or "Work Prioritization"), YOU MUST REJECT THE SOURCE ENTIRELY, even if the name matches exactly.
3. For example, if {company} is "Wavemotion AI" (domain: wavemotionai.com), and a source talks about "WaveForms AI" raising $40M, YOU MUST IGNORE IT. Do not attribute data from similarly named companies to {company}.
4. If you only find data about wrong companies, leave the JSON fields empty. DO NOT HALLUCINATE.
5. For the 'founding_team' array, MUST extract the 'linkedin_url' if provided in the text (look for "[FOUNDER LINKEDIN]"). If the text says "[OFFICIAL EXECUTIVE NO LINKEDIN]", extract the name and role, and explicitly set linkedin_url to "Not Available".
6. EXCEPTION FOR COMPETITORS: You will see sources tagged with "[COMPETITOR DEEP DIVE: <name>]". These are explicitly gathered intelligence about competitors. YOU MUST USE THESE to richly populate the `competitors` array with their Capitalization, Target Segment, Core Moat, and Pricing Signal. Do NOT ignore competitor data.

[DEEP TECH MANDATES]
- No Adjectives: Strip marketing fluff. Focus on exact physics/mechanisms.
- The Graveyard (Historical Bottlenecks): Identify what physical/chemical/engineering bottlenecks prevented this technology from scaling in the past 10 years.
- Team-to-Moat Fit: Analyze if the founders have the actual scientific/engineering pedigree to solve this. Note [MATCH] or [RED FLAG].

Constraints:
- Output ONLY valid JSON. No markdown wrappers.
- Ignore data about fictional characters (e.g., novels, games).
- If a section lacks data for the specific target company, return an empty string or empty list.

Output Format:
{{
    "executive_summary": "Company overview and mission",
    "product_features": [],
    "competitors": [{{"name": "Comp A", "capitalization": "Data Undisclosed", "target_segment": "Data Undisclosed", "core_moat": "Data Undisclosed", "pricing_signal": "Data Undisclosed"}}],
    "social_sentiment": "Summary of real user sentiment",
    "business_model": "Revenue and pricing strategy",
    "traction_and_risks": "Funding, traffic, and legal risks",
    "founding_team": [{{"name": "", "background": "", "linkedin_url": ""}}],
    "data_consistency": "Conflicts between PR and reality based on [TRAFFIC DATA] or [HIRING SIGNAL]",
    "exit_strategy": "Potential acquirers or IPO landscape",
    "used_source_indices": [1, 3, 5]
}}
"""

AGENT_2_PROMPT_TEMPLATE = """
Task: Generate 5 aggressive, highly specific due diligence questions to ask the founders of {company}.
Input:
{facts_json}

Constraints:
- Output ONLY a JSON list of 5 strings. No markdown wrappers.
- Questions MUST target historical physical/engineering bottlenecks, specific environmental parameters, cycle life, or cost-per-unit metrics.
- Cross-examine the team's depth against the actual technological barriers.
- Do NOT ask generic go-to-market strategies or market size questions.

Output Format:
[
    "Question 1...",
    "Question 2...",
    "Question 3...",
    "Question 4...",
    "Question 5..."
]
"""

AGENT_3_PROMPT_TEMPLATE = """
Task: Write a comprehensive, highly analytical Investment Memo for {company} (Domain: {domain}). Ensure the final report provides deep strategic value.
{identity_anchor}

Input:
{formatting_payload}

CRITICAL VC ANALYSIS CONSTRAINTS (ANTI-FLUFF):
1. NO HALLUCINATIONS: Do NOT invent raw facts, names, numbers, or fictional competitors.
2. STRICT ENTITY ALIGNMENT: Ensure the narrative strictly aligns with the "Official Business Description" provided. Do not mix narratives of similar-sounding companies. If a source claims {company} does something radically different from its official description, IGNORE IT.
3. HONEST SCARCITY: If specific factual data (e.g., funding, traction, pricing, or competitor capitalization/moats) is missing from the Input for the correct company, you MUST explicitly state "Data Undisclosed" or "Not publicly available". Do NOT leave empty spaces in tables or try to hide the lack of data with generic industry boilerplate.
4. DEDUCTIVE DEPTH (How to expand without fluff): While you cannot invent facts, you MUST provide deep strategic commentary on the implications of the information you *do* have. For example:
   - If they are a stealth startup, analyze what challenges a stealth startup in this specific niche will inevitably face.
   - If their tech stack is known but revenue isn't, analyze the commercial viability and typical go-to-market motion for that tech stack.
5. Do NOT write a References section at the end.
6. Do NOT number the headers.
7. BAN ON SPECULATION: Do NOT use words like "likely", "probably", or "expected to" to guess their mechanisms. If exact details are missing, state "Implementation Undisclosed". Do not fill gaps with generic industry boilerplate.
8. For the "Founding Team & Track Record" section, you MUST include any LinkedIn URLs found in the Input facts. If the team is hidden, state "Founding Team Undisclosed".

Output Format:
Must include EXACTLY these sections with these headers in this EXACT order:
# {company} Pre-Screen Memo

## Executive Summary
(Provide a sharp, 2-3 paragraph summary. Deduce a SWOT Analysis based on your expert evaluation of the facts, ensuring you highlight strategic implications even if not explicitly stated. Include a Markdown table: | Strengths | Weaknesses | Opportunities | Threats |)

## The Problem
### Current/Traditional Solutions & Historical Graveyard
(Analyze the macro industry status quo. What existing solutions does {company} aim to replace? CRUCIAL DEEP TECH: What historical physical/chemical/engineering bottlenecks prevented this specific technology path from scaling in the past 10 years? Why did others fail?)

### Pain Points
(Analyze 2-4 specific pain points in this market. Output them as a clean bulleted list. Ensure proper markdown spacing around bold text. If {company} has not published exact metrics, analyze the *typical* quantifiable impacts in this sector. Explain why existing solutions fail.)

## Company Overview & Solution
### What They Do
(Clear description of the company's product/service)

### How They Solve The Pain Points
(Create a mapping table: | Pain Point | Their Solution | Impact |)

## Product Deep Dive & First Principles
(Explain exactly HOW the technology works at a physical/chemical/engineering level. What is the actual mechanism? Strip all marketing fluff. How does this mechanism attempt to bypass the "Historical Graveyard" mentioned above?)

## Market Landscape
(Markdown table: | Competitor | Capitalization (Funding/Valuation) | Target Segment | Core Moat / Wedge | Pricing Signal |)

### Strategic Tech-Path White-Space
(Write a strategic deduction analyzing the gap {company} can exploit. Focus on "Alternative Technologies" vs their chosen tech path. What are the Trade-offs of their physics/engineering choice compared to competitors?)

## Social Sentiment & Risk
## Business Model
## Traction & Risks
## Founding Team & Team-to-Moat Fit
(List the team and their LinkedIn URLs. At the end of the list, write a bolded paragraph starting with **Team-to-Moat Fit Assessment:** Cross-examine the founders' academic/engineering backgrounds against the core technology's historical bottlenecks. Do they have the actual pedigree to solve this? Explicitly output [MATCH] or [RED FLAG] with your justification. Do NOT use markdown brackets like [Team-to-Moat Fit Assessment] as headers.)

## Data Consistency Check & Ultimate Verdict
(Point out conflicting PR vs reality based on the data. Then, start a new paragraph with **Ultimate Verdict:** Act as a Deep Tech VC Partner. Is this a PR stunt, a science experiment, or a viable investment? Why? Do NOT use markdown brackets like [Ultimate Verdict].)
## Exit Strategy & M&A Landscape

## Due Diligence Interrogation
(Format the questions provided in the Input as a proper numbered Markdown list, e.g., "1. [Question]". Do NOT output a raw JSON array string. This must be the very last section.)
"""
