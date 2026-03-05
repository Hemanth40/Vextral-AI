"""
Vextral Answer Generation Service - Dual Model Architecture
- Kimi K2.5 (NVIDIA NIM) → General AI Chat
- Llama 3.3 70B (Groq) → Document RAG (ultra-fast)
"""

import os
import time
import logging
from typing import Any
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)


class GeneratorService:
    """Dual-model service: Kimi K2.5 (general) + Groq Llama 3.3 70B (documents)"""
    
    def __init__(self):
        """Initialize both AI model clients"""
        
        # === Kimi K2.5 for General AI Chat (NVIDIA NIM) ===
        kimi_key = os.getenv("NVIDIA_API_KEY_KIMI", "")
        self.kimi_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=kimi_key,
            timeout=120.0
        )
        self.kimi_model = "moonshotai/kimi-k2-instruct"
        
        # === Llama 3.3 70B for Document RAG (Groq - ultra fast) ===
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            self.groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                timeout=60.0
            )
        else:
            self.groq_client = None
        self.groq_model = "llama-3.3-70b-versatile"
        
        # === Gemini 3.0 Flash as the LEADER/REVIEWER Agent ===
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            self.gemini_client = genai.Client(api_key=gemini_key)
        else:
            self.gemini_client = None
        self.gemini_model = "gemini-3.0-flash"
        
        # Default model reference for logging
        self.model = self.kimi_model

    def _build_context(self, context_chunks: list[Any]) -> str:
        """
        Build a grounded context block from either plain strings or chunk dicts.
        """
        context_blocks: list[str] = []

        for i, chunk in enumerate(context_chunks[:6]):
            if isinstance(chunk, dict):
                text = str(chunk.get("text", "")).strip()
                if not text:
                    continue

                source_file = chunk.get("source_file", "document")
                page_number = chunk.get("page_number", 0)
                score = chunk.get("score")
                score_label = f"{float(score):.3f}" if isinstance(score, (float, int)) else "n/a"
                source_label = f"{source_file} page {page_number}" if page_number else str(source_file)

                # Instead of explicit source tags that leak into the UI, simply provide the document info
                context_blocks.append(
                    f"--- DOCUMENT PORTION: {source_label} ---\n{text}"
                )
            else:
                text = str(chunk).strip()
                if text:
                    context_blocks.append(f"--- DOCUMENT PORTION ---\n{text}")

        return "\n\n".join(context_blocks)
        
    def _review_with_gemini(self, question: str, context: str, draft_answer: str, chat_history: list = None) -> str:
        """
        Leader Agent (Gemini 3.0 Flash) reviews and corrects the Worker Agent's draft.
        """
        if not self.gemini_client:
            logger.info("⚠️  Gemini client not configured. Skipping LEADER review step.")
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

        logger.info(f"👑 Passing draft to LEADER agent (Gemini 3.0 Flash) for review...")
        api_start = time.time()
        
        try:
            # Format history for Gemini
            contents = []
            if chat_history:
                for msg in chat_history[:-1]:
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append(
                        types.Content(role=role, parts=[types.Part.from_text(text=msg.get("content", ""))])
                    )
            
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))
            
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                    max_output_tokens=1024,
                )
            )
            
            api_duration = time.time() - api_start
            logger.info(f"⏱️  Leader Review Latency: {api_duration:.2f}s")
            
            # Very basic sanity check to make sure it didn't just return empty
            if response.text and len(response.text.strip()) > 10:
                logger.info(f"✓ Leader review complete")
                return response.text
            else:
                logger.warning("⚠️  Leader returned empty response. Falling back to Worker's draft.")
                return draft_answer
                
        except Exception as e:
            logger.error(f"Error during Gemini review: {e}")
            return draft_answer # Fallback to original draft if Gemini fails

    def generate_answer(
        self, 
        question: str, 
        context_chunks: list[Any], 
        tenant_id: str,
        chat_history: list = None,
        stream: bool = False
    ) -> str:
        """
        Generate answer using the appropriate model:
        - Document mode (context_chunks provided) → Groq Llama 3.3 70B
        - General AI mode (no context) → Kimi K2.5
        """
        try:
            if context_chunks:
                # === DOCUMENT RAG MODE → WORKER (Groq/Llama or Kimi if Groq missing) ===
                if self.groq_client:
                    client = self.groq_client
                    model = self.groq_model
                    worker_name = "Groq Llama 3.3 70B"
                else:
                    client = self.kimi_client
                    model = self.kimi_model
                    worker_name = "Kimi K2.5"
                    
                temperature = 0.1
                context = self._build_context(context_chunks)
                
                system_prompt = """You are Vextral AI's diligent Worker Agent inside an expert document assistant system.

INSTRUCTIONS:
1. Use DOCUMENT CONTEXT as your sole source of truth.
2. Do not invent facts, numbers, names, or quotes.
3. If the context is insufficient, explicitly say what is missing.
4. Keep the answer extremely clear, neat, and highly readable for all users.
5. Provide a perfectly formatted Markdown response (headings, bullets, bold text).
6. DO NOT use explicit citation chunks like [Source N] in the text. Just answer naturally and accurately based on the context."""

                user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Respond with a complete, beautifully formatted, easy-to-understand answer."""

                logger.info(f"⚡ Using WORKER Agent ({worker_name}) to generate draft...")
                
                # Build messages with conversation history for OpenAI-compatible Worker
                api_start = time.time()
                messages = [{"role": "system", "content": system_prompt}]
                
                if chat_history:
                    for msg in chat_history[:-1]:
                        role = msg.get("role", "user")
                        if role in ("user", "assistant"):
                            messages.append({"role": role, "content": msg.get("content", "")})
                
                messages.append({"role": "user", "content": user_prompt})
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=1024,
                    stream=stream
                )
                
                api_duration = time.time() - api_start
                logger.info(f"⏱️  Worker Draft Latency: {api_duration:.2f}s")
                
                if stream:
                    # Multi-agent review handles complete strings, so streaming isn't fully compatible with leader review.
                    # For a true multi-agent approach, we must collect the whole response first to review it.
                    # If stream=True is forcefully requested, we bypass review.
                    return response
                else:
                    draft_answer = response.choices[0].message.content
                    
                    # 👑 Pass to LEADER Agent for review
                    final_answer = self._review_with_gemini(
                        question=question, 
                        context=context, 
                        draft_answer=draft_answer,
                        chat_history=chat_history
                    )
                    return final_answer

            else:
                # === GENERAL AI MODE → WORKER (Kimi K2.5) ===
                client = self.kimi_client
                model = self.kimi_model
                temperature = 0.3
                
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
                
                logger.info(f"🌙 Using Kimi K2.5 (General AI)")

            # Build messages with conversation history for OpenAI-compatible Kimi
            api_start = time.time()
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent chat history for conversational memory
            if chat_history:
                for msg in chat_history[:-1]:  # exclude the current question
                    role = msg.get("role", "user")
                    if role in ("user", "assistant"):
                        messages.append({"role": role, "content": msg.get("content", "")})
            
            # Add current question
            messages.append({"role": "user", "content": user_prompt})
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
                stream=stream
            )
            
            api_duration = time.time() - api_start
            logger.info(f"⏱️  AI Model Latency (Kimi): {api_duration:.2f}s")
            
            if stream:
                return response
            else:
                draft_answer = response.choices[0].message.content
                
                # 👑 Pass to LEADER Agent for review (General Mode)
                # For general mode, context is empty
                final_answer = self._review_with_gemini(
                    question=question,
                    context="No document context provided. Answer using general knowledge.",
                    draft_answer=draft_answer,
                    chat_history=chat_history
                )
                return final_answer
                
        except Exception as e:
            logger.error(f"Error generating answer for tenant {tenant_id}: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")


# Singleton instance
generator = GeneratorService()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing Vextral Dual-Model Generator...")
    
    # Test General AI (Kimi)
    try:
        answer = generator.generate_answer("Say hello in one sentence.", [], "test_user")
        logger.info(f"✓ Kimi K2.5: {answer[:100]}...")
    except Exception as e:
        logger.error(f"✗ Kimi test failed: {e}")
    
    # Test Document RAG (Gemini)
    try:
        answer = generator.generate_answer(
            "What is Vextral?",
            ["Vextral is a multi-tenant RAG platform."],
            "test_user"
        )
        logger.info(f"✓ Gemini 3.0 Flash: {answer[:100]}...")
    except Exception as e:
        logger.error(f"✗ Gemini test failed: {e}")
