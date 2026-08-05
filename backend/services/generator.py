"""
Vextral Answer Generation Service - Advanced Model Architecture
- Google AI Studio Gemma 4 → gemma-4-31b-it (primary) with gemma-4-26b-it fallback
- Google Gemini → gemini-3.5-flash (primary) with gemini-2.5-flash fallback
- NVIDIA NIM Kimi K2.6 → moonshotai/kimi-k2.6 (General AI + fallback)
"""

import os
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
    """Multi-model generation service with robust fallback structures"""
    
    def __init__(self):
        """Initialize all model clients"""
        
        # === Google AI Studio Client (For Gemma 4 and Gemini 3.5/2.5) ===
        # Load newly provided Google key, fallback to GEMINI_API_KEY if needed
        google_key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        if google_key:
            self.google_client = genai.Client(api_key=google_key)
            logger.info("✓ Initialized Google GenAI / Studio Client")
        else:
            self.google_client = None
            logger.warning("⚠️ Google GenAI Client NOT initialized: key missing")
            
        # Store model strings
        self.gemma_primary = "gemma-4-31b-it"
        self.gemma_fallback = "gemma-4-26b-it"
        self.gemini_primary = "gemini-3.5-flash"
        self.gemini_fallback = "gemini-2.5-flash"
        
        # === Kimi K2.6 Client (NVIDIA NIM) ===
        kimi_key = os.getenv("NVIDIA_API_KEY_KIMI", "")
        self.kimi_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=kimi_key,
            timeout=20.0,
            max_retries=1
        )
        self.kimi_model = "moonshotai/kimi-k2.6"

        # === GLM 5.1 Client (NVIDIA NIM) ===
        glm_key = os.getenv("NVIDIA_API_KEY_GLM", "")
        self.glm_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=glm_key,
            timeout=20.0,
            max_retries=1
        )
        self.glm_model = "z-ai/glm-5.1"
        
        # === MiniMax M3 Client (NVIDIA NIM) ===
        minimax_key = os.getenv("NVIDIA_API_KEY_MINIMAX", "")
        self.minimax_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=minimax_key,
            timeout=20.0,
            max_retries=1
        )
        self.minimax_model = "minimaxai/minimax-m3"

        # === Nemotron 3 Ultra Client (NVIDIA NIM) ===
        nemotron_key = os.getenv("NVIDIA_API_KEY_NEMOTRON", "")
        self.nemotron_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nemotron_key,
            timeout=20.0,
            max_retries=1
        )
        self.nemotron_model = "nvidia/nemotron-3-ultra-550b-a55b"
        
        # === Groq GPT-OSS 120B Client ===
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            self.groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                timeout=60.0
            )
        else:
            self.groq_client = None
        self.groq_model = "openai/gpt-oss-120b"

    def _build_context(self, context_chunks: list[Any]) -> str:
        """
        Build a grounded context block dynamically from retrieved chunks.
        FIXED: Removed context_chunks[:6] hardcoded cutting to use all retrieved chunks!
        """
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
            # Attempt normal call with system_instruction
            response = self.google_client.models.generate_content(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=1024,
                )
            )
            return response.text
        except Exception as e:
            # Fallback: Combine system prompt inside the main user prompt if system_instruction is not supported
            logger.warning(f"Google GenAI system_instruction failed, retrying with combined prompt: {e}")
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Reconstruct contents with combined prompt in the last user message
            contents[-1] = types.Content(role="user", parts=[types.Part.from_text(text=combined_prompt)])
            response = self.google_client.models.generate_content(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=1024,
                )
            )
            return response.text

    def _review_with_gemini(self, question: str, context: str, draft_answer: str, chat_history: list = None, model_name: str = "gemini") -> str:
        """
        Review and polish draft answer using Gemini Leader Agent with robust fallbacks
        """
        if not self.google_client:
            logger.info("⚠️ Google GenAI client not configured. Skipping reviewer review step.")
            return draft_answer
            
        system_prompt = """You are the Vextral AI Leader Agent, a meticulous fact-checker and reviewer.
Your job is to review a DRAFT ANSWER provided by a Worker Agent.

INSTRUCTIONS:
1. Verify the Draft Answer against the provided DOCUMENT CONTEXT.
2. Correct any hallucinations, incorrect numbers, or misinterpretations.
3. Ensure the answer is beautifully formatted, neat, and extremely easy for anyone to understand.
4. DO NOT use academic citations like [Source 1] inside your response. Make it read like a natural, expert explanation.
5. If the draft invents information not in the context, rewrite it to be strictly grounded.
6. YOU MUST output ONLY the final, polished response. Do not include commentary about your review process."""

        user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

WORKER'S DRAFT ANSWER:
{draft_answer}

Please review, correct if necessary, and output the FINAL answer."""

        logger.info(f"👑 Passing draft to LEADER agent for review...")
        api_start = time.time()
        
        # Decide reviewer model
        reviewer_model = self.gemini_primary
        if model_name == "gemini":
            reviewer_model = self.gemini_primary
        
        try:
            # Try primary reviewer model
            answer = self._generate_google_content(
                model_id=reviewer_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                chat_history=chat_history,
                temperature=0.1
            )
            api_duration = time.time() - api_start
            logger.info(f"⏱️ Leader Review Latency: {api_duration:.2f}s")
            
            if answer and len(answer.strip()) > 10:
                logger.info(f"✓ Leader review complete ({reviewer_model})")
                return answer
            raise Exception("Empty reviewer response")
            
        except Exception as e:
            logger.warning(f"Leader review on primary model ({reviewer_model}) failed: {e}. Falling back to secondary model.")
            
            # Switch to fallback reviewer model
            fallback_reviewer = self.gemini_fallback
            try:
                answer = self._generate_google_content(
                    model_id=fallback_reviewer,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    chat_history=chat_history,
                    temperature=0.1
                )
                logger.info(f"✓ Leader review complete on fallback model ({fallback_reviewer})")
                return answer
            except Exception as ex:
                logger.error(f"Leader review fallback failed: {ex}. Returning original worker draft.")
                return draft_answer

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
        Generate answer using the selected model with fully robust fallback procedures.
        Returns a dictionary: {"answer": str, "reasoning": Optional[str]}
        """
        try:
            model_name = (model_name or "gemini").lower()
            context = self._build_context(context_chunks) if context_chunks else ""
            
            # 1. DOCUMENT RAG MODE vs GENERAL MODE prompts
            if context:
                system_prompt = """You are Vextral AI's diligent RAG Assistant.

INSTRUCTIONS:
1. Use the provided DOCUMENT CONTEXT as your sole source of truth.
2. Do not invent facts, numbers, names, or quotes.
3. If the context is insufficient, explicitly say what is missing.
4. Keep the answer extremely clear, neat, and highly readable for all users.
5. Provide a perfectly formatted Markdown response (headings, bullets, bold text, tables where applicable).
6. DO NOT use explicitcitation chunks like [Source N] in the text. Just answer naturally and accurately based on the context."""

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

            # 2. ROUTE TO SELECT MODEL

            # === GLM 5.1 ===
            if model_name in ("glm-5.1", "glm") and self.glm_client:
                logger.info("⚡ Generating response using GLM-5.1...")
                messages = [{"role": "system", "content": system_prompt}]
                if chat_history:
                    for msg in chat_history[:-1]:
                        role = msg.get("role", "user")
                        if role in ("user", "assistant"):
                            messages.append({"role": role, "content": msg.get("content", "")})
                messages.append({"role": "user", "content": user_prompt})
                try:
                    response = self.glm_client.chat.completions.create(
                        model=self.glm_model,
                        messages=messages,
                        temperature=1.0,
                        top_p=1.0,
                        max_tokens=16384
                    )
                    return {"answer": response.choices[0].message.content, "reasoning": None}
                except Exception as e:
                    logger.error(f"GLM-5.1 failed: {e}. Re-routing to Gemini fallback.")
                    model_name = "gemini"

            # === MINIMAX M3 ===
            if model_name in ("minimax", "minimax-m3") and self.minimax_client:
                logger.info("⚡ Generating response using MiniMax-M3...")
                messages = [{"role": "system", "content": system_prompt}]
                if chat_history:
                    for msg in chat_history[:-1]:
                        role = msg.get("role", "user")
                        if role in ("user", "assistant"):
                            messages.append({"role": role, "content": msg.get("content", "")})
                messages.append({"role": "user", "content": user_prompt})
                try:
                    response = self.minimax_client.chat.completions.create(
                        model=self.minimax_model,
                        messages=messages,
                        temperature=1.0,
                        top_p=0.95,
                        max_tokens=8192
                    )
                    return {"answer": response.choices[0].message.content, "reasoning": None}
                except Exception as e:
                    logger.error(f"MiniMax-M3 failed: {e}. Re-routing to Gemini fallback.")
                    model_name = "gemini"

            # === NEMOTRON-3-ULTRA-550B (Reasoning enabled) ===
            if model_name in ("nemotron", "nemotron-550b") and self.nemotron_client:
                logger.info("⚡ Generating response using Nemotron-3-Ultra-550b...")
                messages = [{"role": "system", "content": system_prompt}]
                if chat_history:
                    for msg in chat_history[:-1]:
                        role = msg.get("role", "user")
                        if role in ("user", "assistant"):
                            messages.append({"role": role, "content": msg.get("content", "")})
                messages.append({"role": "user", "content": user_prompt})
                try:
                    response = self.nemotron_client.chat.completions.create(
                        model=self.nemotron_model,
                        messages=messages,
                        temperature=1.0,
                        top_p=0.95,
                        max_tokens=16384,
                        extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 16384}
                    )
                    ans_msg = response.choices[0].message
                    reasoning = getattr(ans_msg, "reasoning_content", None) or getattr(ans_msg, "reasoning", None)
                    content = ans_msg.content or ""
                    
                    if not reasoning and "<think>" in content:
                        import re
                        match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                        if match:
                            reasoning = match.group(1).strip()
                            content = content.replace(match.group(0), "").strip()
                            
                    return {"answer": content, "reasoning": reasoning}
                except Exception as e:
                    logger.error(f"Nemotron-3-Ultra-550b failed: {e}. Re-routing to Gemini fallback.")
                    model_name = "gemini"

            # === GOOGLE STUDIO GEMMA 4 PATHWAY ===
            if model_name == "gemma" and self.google_client:
                logger.info(f"⚡ Generating response using Gemma 4 ({self.gemma_primary})...")
                api_start = time.time()
                try:
                    answer = self._generate_google_content(
                        model_id=self.gemma_primary,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        chat_history=chat_history,
                        temperature=0.2
                    )
                    logger.info(f"✓ Gemma 4 response complete ({self.gemma_primary}) in {time.time() - api_start:.2f}s")
                    return {"answer": answer, "reasoning": None}
                except Exception as e:
                    logger.warning(f"Gemma 4 primary model ({self.gemma_primary}) failed: {e}. Trying fallback ({self.gemma_fallback})")
                    try:
                        answer = self._generate_google_content(
                            model_id=self.gemma_fallback,
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            chat_history=chat_history,
                            temperature=0.2
                        )
                        logger.info(f"✓ Gemma 4 fallback response complete ({self.gemma_fallback})")
                        return {"answer": answer, "reasoning": None}
                    except Exception as ex:
                        logger.error(f"Gemma 4 fallback failed: {ex}. Re-routing to Gemini.")
                        model_name = "gemini"

            # === GOOGLE STUDIO GEMINI PATHWAY ===
            if model_name == "gemini" and self.google_client:
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
                    logger.info(f"✓ Gemini response complete ({self.gemini_primary}) in {time.time() - api_start:.2f}s")
                    return {"answer": answer, "reasoning": None}
                except Exception as e:
                    logger.warning(f"Gemini primary model ({self.gemini_primary}) failed: {e}. Trying fallback ({self.gemini_fallback})")
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
                        logger.error(f"Gemini fallback failed: {ex}. Re-routing to Groq fallback.")

            # === EXPLICIT GROQ GPT-OSS 120B PATHWAY ===
            if model_name == "groq" and self.groq_client:
                logger.info("⚡ Generating response using Groq (GPT-OSS 120B)...")
                messages = [{"role": "system", "content": system_prompt}]
                if chat_history:
                    for msg in chat_history[:-1]:
                        role = msg.get("role", "user")
                        if role in ("user", "assistant"):
                            messages.append({"role": role, "content": msg.get("content", "")})
                messages.append({"role": "user", "content": user_prompt})
                try:
                    response = self.groq_client.chat.completions.create(
                        model=self.groq_model,
                        messages=messages,
                        temperature=0.1 if context else 0.4,
                        max_tokens=1024
                    )
                    draft_answer = response.choices[0].message.content
                    if context:
                        polished = self._review_with_gemini(question, context, draft_answer, chat_history, "gemini")
                        return {"answer": polished, "reasoning": None}
                    return {"answer": draft_answer, "reasoning": None}
                except Exception as e:
                    logger.error(f"Explicit Groq model call failed: {e}. Falling back to standard flows.")

            # === EXPLICIT KIMI K2.6 PATHWAY ===
            if model_name == "kimi" and self.kimi_client:
                logger.info("⚡ Generating response using NVIDIA Kimi K2.6...")
                messages = [{"role": "system", "content": system_prompt}]
                if chat_history:
                    for msg in chat_history[:-1]:
                        role = msg.get("role", "user")
                        if role in ("user", "assistant"):
                            messages.append({"role": role, "content": msg.get("content", "")})
                messages.append({"role": "user", "content": user_prompt})
                try:
                    response = self.kimi_client.chat.completions.create(
                        model=self.kimi_model,
                        messages=messages,
                        temperature=1.0,
                        top_p=1.0,
                        max_tokens=16384
                    )
                    return {"answer": response.choices[0].message.content, "reasoning": None}
                except Exception as e:
                    logger.error(f"Explicit Kimi model call failed: {e}. Re-routing to Gemini fallback.")
                    model_name = "gemini"

            # === LEGACY PROVIDERS FALLBACK ===
            if context:
                if self.groq_client:
                    logger.info("⚡ RAG generation falling back to Groq Worker...")
                    messages = [{"role": "system", "content": system_prompt}]
                    if chat_history:
                        for msg in chat_history[:-1]:
                            role = msg.get("role", "user")
                            if role in ("user", "assistant"):
                                messages.append({"role": role, "content": msg.get("content", "")})
                    messages.append({"role": "user", "content": user_prompt})
                    response = self.groq_client.chat.completions.create(
                        model=self.groq_model,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=1024
                    )
                    draft_answer = response.choices[0].message.content
                    polished = self._review_with_gemini(question, context, draft_answer, chat_history, model_name)
                    return {"answer": polished, "reasoning": None}

            # General Chat fallback uses Kimi with a fail-safe Google Gemini recovery flow
            logger.info("⚡ Chat generation falling back to NVIDIA Kimi Worker...")
            messages = [{"role": "system", "content": system_prompt}]
            if chat_history:
                for msg in chat_history[:-1]:
                    role = msg.get("role", "user")
                    if role in ("user", "assistant"):
                        messages.append({"role": role, "content": msg.get("content", "")})
            messages.append({"role": "user", "content": user_prompt})
            
            try:
                response = self.kimi_client.chat.completions.create(
                    model=self.kimi_model,
                    messages=messages,
                    temperature=1.0,
                    top_p=1.0,
                    max_tokens=16384
                )
                return {"answer": response.choices[0].message.content, "reasoning": None}
            except Exception as e:
                logger.warning(f"Kimi fallback failed: {e}. Executing final Google Gemini recovery flow.")
                if self.google_client:
                    answer = self._generate_google_content(
                        model_id=self.gemini_primary,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        chat_history=chat_history,
                        temperature=0.2
                    )
                    return {"answer": answer, "reasoning": None}
                raise e
                
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


