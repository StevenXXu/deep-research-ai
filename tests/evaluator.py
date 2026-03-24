import json
import re
import os

def load_golden_dataset(filepath="tests/golden_dataset.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)["test_cases"]

def evaluate_report(markdown_content, test_case):
    """
    The Fitness Function for the Solo-Evolver Autoresearch loop.
    Evaluates a generated markdown report against the golden dataset ground truth.
    """
    score = 0
    max_possible = 0
    log = []
    
    domain = test_case["domain"]
    content_lower = markdown_content.lower()
    
    log.append(f"=== Evaluating {domain} ===")
    
    # 1. Entity Anchoring Match
    expected_entity = test_case.get("expected_entity", "")
    if expected_entity:
        max_possible += 10
        # Check if the exact expected entity name appears (case insensitive)
        if expected_entity.lower() in content_lower:
            score += 10
            log.append(f"[PASS] Entity anchored correctly: {expected_entity} (+10)")
        else:
            log.append(f"[FAIL] Entity missing or misidentified. Expected: {expected_entity} (+0)")

    ground_truth = test_case.get("ground_truth", {})
    
    # 2. Founder Extraction
    for founder in ground_truth.get("must_find_founders", []):
        max_possible += 15
        if founder.lower() in content_lower:
            score += 15
            log.append(f"[PASS] Founder extracted: {founder} (+15)")
        else:
            log.append(f"[FAIL] Founder dropped/missed: {founder} (+0)")

    # 3. Deep Tech Physics/Mechanisms
    for kw in ground_truth.get("must_find_tech_keywords", []):
        max_possible += 10
        if kw.lower() in content_lower:
            score += 10
            log.append(f"[PASS] Tech mechanism identified: {kw} (+10)")
        else:
            log.append(f"[FAIL] Tech mechanism missed (fluff used?): {kw} (+0)")

    # 4. Funding Data
    funding = ground_truth.get("must_find_funding", "")
    if funding:
        max_possible += 5
        if funding.lower() in content_lower:
            score += 5
            log.append(f"[PASS] Funding data intact: {funding} (+5)")
        else:
            log.append(f"[FAIL] Funding data missing: {funding} (+0)")

    # 5. ANTI-HALLUCINATION (The Guillotine)
    anti_hallucination = test_case.get("anti_hallucination", {})
    for fw in anti_hallucination.get("forbidden_words", []):
        if fw.lower() in content_lower:
            score -= 50
            log.append(f"[FATAL] Hallucination detected! Forbidden word found: '{fw}' (-50)")
        else:
            log.append(f"[PASS] Hallucination avoided: '{fw}' not found.")

    # 6. Honest Scarcity (Red Flags)
    for rf in anti_hallucination.get("expected_red_flags", []):
        max_possible += 15
        if rf.lower() in content_lower:
            score += 15
            log.append(f"[PASS] Honest scarcity/Red flag triggered: {rf} (+15)")
        else:
            log.append(f"[FAIL] Failed to trigger expected red flag: {rf} (+0)")

    # Calculate final grade
    percentage = (score / max_possible) * 100 if max_possible > 0 else 0
    
    return {
        "domain": domain,
        "score": score,
        "max_possible": max_possible,
        "percentage": round(percentage, 2),
        "log": log
    }

def print_evaluation(result):
    for line in result["log"]:
        print(line)
    print(f"Final Score: {result['score']}/{result['max_possible']} ({result['percentage']}%)")
    if result['score'] < 0:
        print(">>> DISCARD MUTATION: Hallucination penalty triggered. <<<")
    print("-" * 50)

if __name__ == "__main__":
    print("Solo-Evolver: Fitness Evaluator initialized.")
    # Example usage (commented out):
    # dataset = load_golden_dataset()
    # mock_report = "AlumaPower is building a galvanic generator with an aluminum-air anode. Rob Alexander is the founder. Not Available."
    # res = evaluate_report(mock_report, dataset[0])
    # print_evaluation(res)
