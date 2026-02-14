"""
Vextral Answer Generation Service - Dual Model Architecture
- Kimi K2.5 (NVIDIA NIM) → General AI Chat
- Llama 3.3 70B (Groq) → Document RAG (ultra-fast)
"""

import os
import time
import logging
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
    
    def generate_answer(
        self, 
        question: str, 
        context_chunks: list[str], 
        tenant_id: str,
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
                
                context = "\n\n".join([
                    f"[Document Chunk {i+1}]\n{chunk}" 
                    for i, chunk in enumerate(context_chunks[:5])
                ])
                
                system_prompt = """You are Vextral AI, an expert document assistant powered by advanced AI.

INSTRUCTIONS:
1. Use the provided DOCUMENT CONTEXT as your PRIMARY source.
2. If the document context provides a partial answer, SUPPLEMENT it with your own knowledge to give a complete response.
3. If the question is related to the document but goes beyond it, combine document information with your broader knowledge.
4. Format your responses beautifully using Markdown:
   - Use **bold** for key terms and important points
   - Use bullet points and numbered lists for clarity
   - Use headings (##) to organize longer answers
   - Use tables when comparing data
   - Use > blockquotes for direct citations from the document
5. Be thorough, precise, and insightful.
6. Never say you cannot answer - always provide the best possible response."""

                user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Provide a comprehensive, well-formatted answer. Use the document context as your primary source, and supplement with your own knowledge where helpful."""

                logger.info(f"⚡ Using Groq Llama 3.3 70B (Document RAG)")

            else:
                # === GENERAL AI MODE → Kimi K2.5 ===
                client = self.kimi_client
                model = self.kimi_model
                
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

            # Call the selected model
            api_start = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
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
