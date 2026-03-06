import os
import time
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

# Communication Protocol (Inlined to avoid Import Errors in Docker)
COMMUNICATION_PROTOCOL = """
[COMMUNICATION PROTOCOL ACTIVE]
You are equipped with the "Communication Skill". Before responding, apply these principles:

1. **Deep Listening:**
   - Look beyond the surface text. What is the user's underlying need?
   - Detect emotional subtext (anxiety, excitement, frustration).
   - Identify context patterns (history, parallel threads).

2. **Principles:**
   - **Clarity is Kindness:** Be direct but warm.
   - **Presence over Performance:** Focus on helping, not impressing.
   - **Curiosity:** If requirements are vague, ask clarifying questions.

3. **Response Crafting:**
   - **Objective:** What must this message achieve?
   - **Tone:** Calibrate to the situation (e.g., Warm+Direct for difficult news, Curious+Neutral for conflict).
   - **Structure:** Use "Acknowledge -> Bridge -> Guide" for complex topics.

4. **Verify:**
   - Does this respect the user's values?
   - Is it actionable?
   - Would I want to receive this message?

Apply this protocol to all drafted content (emails, posts, replies).
"""

load_dotenv()

class LLMGateway:
    def __init__(self):
        # 1. Google GenAI (New SDK)
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        if self.gemini_key:
            self.gemini_client = genai.Client(api_key=self.gemini_key)

        # 2. DeepSeek (OpenAI Compatible)
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if self.deepseek_key:
            self.deepseek_client = OpenAI(
                api_key=self.deepseek_key,
                base_url="https://api.deepseek.com"
            )

        # 3. MiniMax (OpenAI Compatible)
        self.minimax_key = os.getenv("MINIMAX_API_KEY")
        self.minimax_group = os.getenv("MINIMAX_GROUP_ID")
        if self.minimax_key:
            self.minimax_client = OpenAI(
                api_key=self.minimax_key,
                base_url="https://api.minimax.chat/v1"
            )

        # 4. OpenAI
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)

    def generate(self, prompt, system_prompt="You are a helpful assistant."):
        """
        Waterfall Fallback Strategy:
        Gemini -> DeepSeek -> MiniMax -> OpenAI
        """
        # INJECT COMMUNICATION SKILL
        # We prepend it to ensure it sets the baseline behavior
        full_system_prompt = COMMUNICATION_PROTOCOL + "\n\n" + system_prompt
        
        errors = []

        # Attempt 1: Gemini
        if self.gemini_key:
            try:
                # print("[LLM] Trying Gemini...")
                full_input = f"System: {full_system_prompt}\n\nUser: {prompt}"
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=full_input
                )
                if response.text:
                    return response.text
            except Exception as e:
                # print(f"[LLM] Gemini Failed: {e}")
                errors.append(f"Gemini: {e}")
        
        # Attempt 2: DeepSeek
        if self.deepseek_key:
            try:
                # print("[LLM] Trying DeepSeek...")
                response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                # print(f"[LLM] DeepSeek Failed: {e}")
                errors.append(f"DeepSeek: {e}")

        # Attempt 3: MiniMax
        if self.minimax_key:
            try:
                # print("[LLM] Trying MiniMax...")
                # MiniMax sometimes requires specific model names
                response = self.minimax_client.chat.completions.create(
                    model="abab6.5s-chat", 
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                # print(f"[LLM] MiniMax Failed: {e}")
                errors.append(f"MiniMax: {e}")

        # Attempt 4: OpenAI
        if self.openai_key:
            try:
                # print("[LLM] Trying OpenAI...")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini", # Use mini for cost, or gpt-4o for quality
                    messages=[
                        {"role": "system", "content": full_system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                # print(f"[LLM] OpenAI Failed: {e}")
                errors.append(f"OpenAI: {e}")

        # Critical Failure
        return f"CRITICAL: All LLM providers failed.\nErrors: {'; '.join(errors)}"

# Global instance
gateway = LLMGateway()
