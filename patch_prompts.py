def patch_engine():
    with open("backend/research_engine.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Import the prompts at the top
    if "import prompts_config" not in content:
        content = content.replace("import time", "import time\nimport prompts_config")

    # Replace Agent 1
    # Find prompt_agent1 = f""" ... """
    import re
    # Match from prompt_agent1 = f""" to """
    agent1_pattern = r'prompt_agent1 = f"""(.*?)"""'
    content = re.sub(agent1_pattern, 'prompt_agent1 = prompts_config.AGENT_1_PROMPT_TEMPLATE.format(company=self.company, domain=self.domain, identity_anchor=identity_anchor, context_blob=context_blob)', content, flags=re.DOTALL)

    # Replace Agent 2
    agent2_pattern = r'prompt_agent2 = f"""(.*?)"""'
    content = re.sub(agent2_pattern, 'prompt_agent2 = prompts_config.AGENT_2_PROMPT_TEMPLATE.format(company=self.company, facts_json=facts_json)', content, flags=re.DOTALL)

    # Replace Agent 3
    agent3_pattern = r'prompt_agent3 = f"""(.*?)"""'
    content = re.sub(agent3_pattern, 'prompt_agent3 = prompts_config.AGENT_3_PROMPT_TEMPLATE.format(company=self.company, domain=self.domain, identity_anchor=identity_anchor, formatting_payload=formatting_payload)', content, flags=re.DOTALL)

    # Replace Audit Prompt
    audit_pattern = r'audit_prompt = f"""(.*?)"""'
    content = re.sub(audit_pattern, 'audit_prompt = prompts_config.AUDIT_PROMPT_TEMPLATE.format(company=self.company, url=self.url, source_list_json=json.dumps(source_list, indent=2))', content, flags=re.DOTALL)

    with open("backend/research_engine.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_engine()
    print("Prompts successfully extracted and linked!")
