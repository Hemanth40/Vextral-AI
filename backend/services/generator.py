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
        self.groq_client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            timeout=60.0
        )
        self.groq_model = "llama-3.3-70b-versatile"
        
        # Default model reference for logging
        self.model = self.groq_model

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

                context_blocks.append(
                    f"[Source {i+1} | {source_label} | relevance={score_label}]\n{text}"
                )
            else:
                text = str(chunk).strip()
                if text:
                    context_blocks.append(f"[Source {i+1}]\n{text}")

        return "\n\n".join(context_blocks)
    
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
                # === DOCUMENT RAG MODE → Groq Llama 3.3 70B ===
                client = self.groq_client
                model = self.groq_model
                temperature = 0.1
                
                context = self._build_context(context_chunks)
                
                system_prompt = """You are Vextral AI, an expert document assistant.

INSTRUCTIONS:
1. Use DOCUMENT CONTEXT as the primary source of truth.
2. Do not invent facts, numbers, names, or quotes.
3. If context is insufficient, explicitly say what is missing.
4. Cite supporting evidence with [Source N] markers.
5. Keep the answer concise, clear, and in Markdown.
6. Prefer accuracy over completeness."""

                user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Respond with:
1) A direct answer
2) Key evidence bullets with [Source N] citations"""

                logger.info(f"⚡ Using Groq Llama 3.3 70B (Document RAG)")

            else:
                # === GENERAL AI MODE → Kimi K2.5 ===
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

            # Build messages with conversation history
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
            logger.info(f"⏱️  AI Model Latency: {api_duration:.2f}s")
            
            if stream:
                return response
            else:
                answer = response.choices[0].message.content
                return answer
                
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
    
    # Test Document RAG (Groq)
    try:
        answer = generator.generate_answer(
            "What is Vextral?",
            ["Vextral is a multi-tenant RAG platform."],
            "test_user"
        )
        logger.info(f"✓ Groq Llama 3.3: {answer[:100]}...")
    except Exception as e:
        logger.error(f"✗ Groq test failed: {e}")
