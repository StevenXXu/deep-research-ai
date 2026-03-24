import os
import json
import shutil
import sys
import time
from dotenv import load_dotenv
import os
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
    load_dotenv(env_path)

# Add backend to path so we can import the engine and gateway
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from research_engine import ResearchEngine
from evaluator import load_golden_dataset, evaluate_report, print_evaluation
from llm_gateway import gateway

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'prompts_config.py'))
BACKUP_PATH = CONFIG_PATH + ".bak"

def run_full_eval(dataset):
    total_score = 0
    total_max = 0
    
    for case in dataset:
        domain = case['domain']
        print(f"\n--- Testing Domain: {domain} ---")
        url = f"https://www.{domain}"
        
        # Initialize engine (mocking user_id/report_id for standalone run)
        engine = ResearchEngine(url, language="english", user_id="evolver_agent", report_id=f"eval_{int(time.time())}")
        
        try:
            # Run the pipeline (This costs real API credits!)
            markdown_report = engine.run()
            if not markdown_report:
                print(f"[!] Engine returned empty report for {domain}.")
                continue
                
            # Evaluate against Golden Dataset
            result = evaluate_report(markdown_report, case)
            print_evaluation(result)
            
            total_score += result["score"]
            total_max += result["max_possible"]
            
        except Exception as e:
            print(f"[!] Pipeline crash on {domain}: {e}")
            total_score -= 100 # Severe penalty for crashing the pipeline
            
    return total_score, total_max

def mutate_prompts(current_prompts, feedback=""):
    print("\n[Evolver] Generating prompt mutations via LLM...")
    mutation_prompt = f"""
    You are an AI Research Scientist optimizing prompt templates for a deep tech VC analysis agent.
    Your goal is to improve the accuracy of data extraction, enforce anti-hallucination, and ensure deep tech physics are extracted.

    CURRENT PROMPTS:
    ```python
    {current_prompts}
    ```

    FEEDBACK FROM LAST RUN:
    {feedback}

    Modify the Python code to improve the prompt instructions. You can tweak rules, add explicit bans on certain behaviors, or change formatting constraints.
    DO NOT REMOVE THE VARIABLE NAMES (e.g., AGENT_1_PROMPT_TEMPLATE).
    RETURN ONLY THE FULL, VALID PYTHON CODE. DO NOT WRAP IN MARKDOWN BLOCKS EXCEPT TRIPLE QUOTES FOR STRINGS.
    """
    
    try:
        new_prompts = gateway.generate(mutation_prompt, "Return valid Python code only.")
        new_prompts = new_prompts.replace("```python", "").replace("```", "").strip()
        return new_prompts
    except Exception as e:
        print(f"[!] LLM Mutation failed: {e}")
        return current_prompts

def main(iterations=3):
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    dataset = load_golden_dataset(dataset_path)
    
    print("===================================================")
    print("=== SOLO-EVOLVER: AUTORESEARCH LOOP INITIATED ===")
    print("===================================================")
    print("WARNING: This loop will consume real API credits (Tavily, Firecrawl, Exa) for each test case.")
    
    print("\n1. Running baseline evaluation...")
    baseline_score, baseline_max = run_full_eval(dataset)
    print(f"\n[BASELINE ESTABLISHED] Total Score: {baseline_score}/{baseline_max}")

    for i in range(iterations):
        print(f"\n===================================================")
        print(f"=== EVOLUTION EPOCH {i+1}/{iterations} ===")
        print(f"===================================================")
        
        # Backup current prompts
        shutil.copy(CONFIG_PATH, BACKUP_PATH)
        
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            current_prompts = f.read()

        # Mutate
        feedback = f"Previous total score was {baseline_score}/{baseline_max}. Try to enforce stricter anti-hallucination and extract more specific technical mechanisms. Ensure we don't drop verified founders."
        new_prompts = mutate_prompts(current_prompts, feedback)
        
        # Inject mutation
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(new_prompts)
            
        print("\n2. Running candidate evaluation...")
        candidate_score, candidate_max = run_full_eval(dataset)
        print(f"\n[CANDIDATE SCORED] Total Score: {candidate_score}/{candidate_max}")
        
        # Selection (Darwinian Survival)
        if candidate_score > baseline_score:
            print(f"\n>>> MUTATION ACCEPTED: Score improved from {baseline_score} to {candidate_score}! <<<")
            baseline_score = candidate_score
            if os.path.exists(BACKUP_PATH):
                os.remove(BACKUP_PATH)
        else:
            print(f"\n>>> MUTATION REJECTED: {candidate_score} <= {baseline_score}. Rolling back to previous generation. <<<")
            shutil.copy(BACKUP_PATH, CONFIG_PATH)
            os.remove(BACKUP_PATH)
            
    print("\n=== EVOLUTION COMPLETE ===")
    print(f"Final Optimized Score: {baseline_score}/{baseline_max}")

if __name__ == "__main__":
    # To run: python tests/run_evolution.py
    main(iterations=3)
