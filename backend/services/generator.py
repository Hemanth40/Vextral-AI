"""
Vextral Answer Generation Service - Multi-Model Architecture
Verified & Active Models:
- Google AI Studio / Gemini: gemini-3.5-flash (primary) with gemini-2.5-flash fallback
- Groq: openai/gpt-oss-120b (ultra-low latency 120B model)
- NVIDIA NIM: minimaxai/minimax-m3 (fast multimodal model)
- NVIDIA NIM: nvidia/nemotron-3-ultra-550b-a55b (550B reasoning model with chain-of-thought)
"""

import os
import re
import time
import logging
from typing import Any, Optional
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)


class GeneratorService:
    """Multi-model generation service with robust failover structures"""

    def __init__(self):
        """Initialize verified model clients"""

        # === Google AI Studio / GenAI Client ===
        google_key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        if google_key:
            self.google_client = genai.Client(api_key=google_key)
            logger.info("✓ Initialized Google GenAI Client")
        else:
            self.google_client = None
            logger.warning("⚠️ Google GenAI Client NOT initialized: key missing")

        self.gemini_primary = "gemini-3.5-flash"
        self.gemini_fallback = "gemini-2.5-flash"

        # === Groq Client (GPT-OSS 120B) ===
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            self.groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                timeout=30.0,
                max_retries=1
            )
            logger.info("✓ Initialized Groq Client")
        else:
            self.groq_client = None
            logger.warning("⚠️ Groq Client NOT initialized: key missing")
        self.groq_model = "openai/gpt-oss-120b"

        # === MiniMax M3 Client (NVIDIA NIM) ===
        minimax_key = os.getenv("NVIDIA_API_KEY_MINIMAX", "")
        if minimax_key:
            self.minimax_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=minimax_key,
                timeout=20.0,
                max_retries=1
            )
            logger.info("✓ Initialized MiniMax-M3 Client")
        else:
            self.minimax_client = None
            logger.warning("⚠️ MiniMax Client NOT initialized: key missing")
        self.minimax_model = "minimaxai/minimax-m3"

        # === Nemotron 3 Ultra Client (NVIDIA NIM) ===
        nemotron_key = os.getenv("NVIDIA_API_KEY_NEMOTRON", "")
        if nemotron_key:
            self.nemotron_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=nemotron_key,
                timeout=35.0,
                max_retries=1
            )
            logger.info("✓ Initialized Nemotron Client")
        else:
            self.nemotron_client = None
            logger.warning("⚠️ Nemotron Client NOT initialized: key missing")
        self.nemotron_model = "nvidia/nemotron-3-ultra-550b-a55b"

    def _build_context(self, context_chunks: list[Any]) -> str:
        """Build a grounded context block dynamically from retrieved chunks."""
        context_blocks: list[str] = []

        for chunk in context_chunks:
            if isinstance(chunk, dict):
                text = str(chunk.get("text", "")).strip()
                if not text:
                    continue

                source_file = chunk.get("source_file", "document")
                page_number = chunk.get("page_number", 0)
                source_label = f"{source_file} page {page_number}" if page_number else str(source_file)

                context_blocks.append(
                    f"--- DOCUMENT PORTION: {source_label} ---\n{text}"
                )
            else:
                text = str(chunk).strip()
                if text:
                    context_blocks.append(f"--- DOCUMENT PORTION ---\n{text}")

        return "\n\n".join(context_blocks)

    def _generate_google_content(self, model_id: str, system_prompt: str, user_prompt: str, chat_history: list = None, temperature: float = 0.1) -> str:
        """Robust helper to query Google GenAI/Studio with automatic system_prompt compatibility fallback"""
        if not self.google_client:
            raise Exception("Google client is not configured. Please supply an API key.")

        contents = []
        if chat_history:
            for msg in chat_history[:-1]:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg.get("content", ""))])
                )

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

        try:
            response = self.google_client.models.generate_content(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=2048,
                )
            )
            return response.text.strip() if response and response.text else ""
        except Exception as e:
            logger.warning(f"Google GenAI system_instruction call failed on {model_id}, retrying with combined prompt: {e}")
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            contents[-1] = types.Content(role="user", parts=[types.Part.from_text(text=combined_prompt)])
            response = self.google_client.models.generate_content(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                )
            )
            return response.text.strip() if response and response.text else ""

    def generate_answer(
        self,
        question: str,
        context_chunks: list[Any],
        tenant_id: str,
        chat_history: list = None,
        stream: bool = False,
        model_name: Optional[str] = "gemini"
    ) -> dict:
        """
        Generate answer using the selected verified model with clean fallback.
        Returns a dictionary: {"answer": str, "reasoning": Optional[str]}
        """
        try:
            model_name = (model_name or "gemini").lower()
            context = self._build_context(context_chunks) if context_chunks else ""

            # 1. Prompts for Document RAG mode vs General AI mode
            if context:
                system_prompt = """You are Vextral AI's diligent RAG Assistant.

INSTRUCTIONS:
1. Use the provided DOCUMENT CONTEXT as your sole source of truth.
2. Do not invent facts, numbers, names, or quotes.
3. If the context is insufficient, explicitly say what is missing.
4. Keep the answer extremely clear, neat, and highly readable for all users.
5. Provide a perfectly formatted Markdown response (headings, bullets, bold text, tables where applicable).
6. DO NOT use explicit citation chunks like [Source N] in the text. Just answer naturally and accurately based on the context."""

                user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Respond with a complete, beautifully formatted, easy-to-understand answer."""
            else:
                system_prompt = """You are Vextral AI, a friendly and highly intelligent general assistant.

INSTRUCTIONS:
1. Answer questions using your knowledge. Be helpful, conversational, and direct.
2. Format your responses beautifully using Markdown:
   - Use **bold** for key terms
   - Use bullet points and numbered lists
   - Use headings (##) for longer answers
   - Use code blocks when showing code
3. Be thorough yet concise. No fluff.
4. Be professional yet engaging and personable."""
                user_prompt = question

            # Build standard OpenAI messages format for Groq / NIM models
            standard_messages = [{"role": "system", "content": system_prompt}]
            if chat_history:
                for msg in chat_history[:-1]:
                    role = msg.get("role", "user")
                    if role in ("user", "assistant"):
                        standard_messages.append({"role": role, "content": msg.get("content", "")})
            standard_messages.append({"role": "user", "content": user_prompt})

            # 2. ROUTE TO VERIFIED MODEL

            # === GROQ GPT-OSS 120B (Ultra-fast) ===
            if model_name in ("groq", "gpt-oss", "gpt-120b") and self.groq_client:
                logger.info("⚡ Generating response using Groq (GPT-OSS 120B)...")
                try:
                    response = self.groq_client.chat.completions.create(
                        model=self.groq_model,
                        messages=standard_messages,
                        temperature=0.1 if context else 0.4,
                        max_tokens=2048
                    )
                    return {"answer": response.choices[0].message.content, "reasoning": None}
                except Exception as e:
                    logger.error(f"Groq generation failed: {e}. Falling back to Gemini.")

            # === MINIMAX M3 (Fast Multimodal) ===
            elif model_name in ("minimax", "minimax-m3") and self.minimax_client:
                logger.info("⚡ Generating response using MiniMax-M3...")
                try:
                    response = self.minimax_client.chat.completions.create(
                        model=self.minimax_model,
                        messages=standard_messages,
                        temperature=0.7,
                        top_p=0.95,
                        max_tokens=4096
                    )
                    return {"answer": response.choices[0].message.content, "reasoning": None}
                except Exception as e:
                    logger.error(f"MiniMax-M3 failed: {e}. Falling back to Gemini.")

            # === NEMOTRON 3 ULTRA 550B (Deep Reasoning with Chain-of-Thought) ===
            elif model_name in ("nemotron", "nemotron-550b", "nemotron-3") and self.nemotron_client:
                logger.info("⚡ Generating response using Nemotron-3-Ultra-550b...")
                try:
                    response = self.nemotron_client.chat.completions.create(
                        model=self.nemotron_model,
                        messages=standard_messages,
                        temperature=0.7,
                        top_p=0.95,
                        max_tokens=8192,
                        extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 8192}
                    )
                    ans_msg = response.choices[0].message
                    reasoning = getattr(ans_msg, "reasoning_content", None) or getattr(ans_msg, "reasoning", None)
                    content = ans_msg.content or ""

                    if not reasoning and "<think>" in content:
                        match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                        if match:
                            reasoning = match.group(1).strip()
                            content = content.replace(match.group(0), "").strip()

                    return {"answer": content, "reasoning": reasoning}
                except Exception as e:
                    logger.error(f"Nemotron failed: {e}. Falling back to Gemini.")

            # === GOOGLE GEMINI PATHWAY (Primary & Resilient Fallback) ===
            if self.google_client:
                logger.info(f"⚡ Generating response using Gemini ({self.gemini_primary})...")
                api_start = time.time()
                try:
                    answer = self._generate_google_content(
                        model_id=self.gemini_primary,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        chat_history=chat_history,
                        temperature=0.2
                    )
                    if answer:
                        logger.info(f"✓ Gemini response complete in {time.time() - api_start:.2f}s")
                        return {"answer": answer, "reasoning": None}
                except Exception as e:
                    logger.warning(f"Gemini primary ({self.gemini_primary}) failed: {e}. Trying fallback ({self.gemini_fallback})")

                try:
                    answer = self._generate_google_content(
                        model_id=self.gemini_fallback,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        chat_history=chat_history,
                        temperature=0.2
                    )
                    logger.info(f"✓ Gemini fallback response complete ({self.gemini_fallback})")
                    return {"answer": answer, "reasoning": None}
                except Exception as ex:
                    logger.error(f"Gemini fallback failed: {ex}")

            # === FINAL GROQ FAILOVER (if Gemini also failed) ===
            if self.groq_client:
                logger.info("⚡ Executing emergency failover to Groq...")
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=standard_messages,
                    temperature=0.2,
                    max_tokens=2048
                )
                return {"answer": response.choices[0].message.content, "reasoning": None}

            raise Exception("All configured AI models are currently unavailable.")

        except Exception as e:
            logger.error(f"Error generating answer for tenant {tenant_id}: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")


# Singleton instance
generator = GeneratorService()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing Vextral Generator Services...")
    try:
        ans = generator.generate_answer("Hello", [], "test_user", model_name="gemini")
        print(f"Gemini: {ans}")
    except Exception as err:
        print(f"Error testing Gemini: {err}")
