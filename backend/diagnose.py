import os
import sqlite3
import logging
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_sqlite_db():
    print("\n--- Testing SQLite (Local) ---")
    from services.database import init_sqlite_db
    init_sqlite_db()
    db_path = os.path.join(os.path.dirname(__file__), "vextral.db")
    try:
        conn = sqlite3.connect(db_path)

        cur = conn.cursor()
        
        # Check if documents table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        has_docs = cur.fetchone()
        
        # Check if chat_history table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        has_chat = cur.fetchone()
        
        if has_docs and has_chat:
            print("[OK] SQLite Local Database connected. All tables verified successfully.")
        else:
            print(f"[ERROR] SQLite Local connected but tables missing. docs={has_docs}, chat={has_chat}")
        conn.close()
    except Exception as e:
        print(f"[ERROR] SQLite Local Database Failed: {e}")


def test_google_studio_gemini():
    print("\n--- Testing Google AI Studio (Gemini 3.5 & 2.5) ---")
    key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY"))
    if not key:
        print("[ERROR] GOOGLE_API_KEY / GEMINI_API_KEY missing")
        return
    try:
        client = genai.Client(api_key=key)
        
        # Test Gemini 3.5 (Primary)
        print("Testing gemini-3.5-flash...")
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents="Hello from Vextral Diagnostics! Respond with 'GEMINI_3_5_SUCCESS'."
            )
            print(f"[OK] Gemini 3.5 Success. Response: {response.text.strip()}")
        except Exception as e35:
            print(f"[WARNING] Gemini 3.5 failed or unavailable: {e35}. Testing fallback gemini-2.5-flash...")
            # Try Gemini 2.5 (Fallback)
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents="Hello from Vextral Diagnostics! Respond with 'GEMINI_2_5_SUCCESS'."
                )
                print(f"[OK] Gemini 2.5 Fallback Success. Response: {response.text.strip()}")
            except Exception as e25:
                print(f"[ERROR] Gemini 2.5 Fallback also failed: {e25}")
    except Exception as e:
        print(f"[ERROR] Google Studio Gemini client failed: {e}")

def test_google_studio_gemma():
    print("\n--- Testing Google AI Studio (Gemma 4: 31B & 26B) ---")
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("[ERROR] GOOGLE_API_KEY missing")
        return
    try:
        client = genai.Client(api_key=key)
        
        # Test Gemma 4 31B (Primary)
        print("Testing gemma-4-31b-it...")
        try:
            response = client.models.generate_content(
                model="gemma-4-31b-it",
                contents="Hello from Vextral Diagnostics! Respond with 'GEMMA_4_31B_SUCCESS'."
            )
            print(f"[OK] Gemma 4 31B Success. Response: {response.text.strip()}")
        except Exception as eg4:
            print(f"[WARNING] Gemma 4 31B failed or unavailable: {eg4}. Testing fallback gemma-4-26b-it...")
            # Try Gemma 4 26B (Fallback)
            try:
                response = client.models.generate_content(
                    model="gemma-4-26b-it",
                    contents="Hello from Vextral Diagnostics! Respond with 'GEMMA_4_26B_SUCCESS'."
                )
                print(f"[OK] Gemma 4 26B Fallback Success. Response: {response.text.strip()}")
            except Exception as eg26:
                # Let's check if gemma-2-27b-it exists as absolute fallback for Google AI Studio
                print(f"[WARNING] Gemma 4 26B failed or unavailable: {eg26}. Trying absolute fallback gemma-2-27b-it...")
                try:
                    response = client.models.generate_content(
                        model="gemma-2-27b-it",
                        contents="Hello from Vextral Diagnostics! Respond with 'GEMMA_2_27B_SUCCESS'."
                    )
                    print(f"[OK] Gemma 2 27B Fallback Success. Response: {response.text.strip()}")
                except Exception as eg2:
                    print(f"[ERROR] All Gemma models failed: {eg2}")
    except Exception as e:
        print(f"[ERROR] Google Studio Gemma client failed: {e}")

def test_new_nvidia_models():
    print("\n--- Testing New NVIDIA NIM Models ---")
    
    # 1. GLM-5.1
    glm_key = os.getenv("NVIDIA_API_KEY_GLM")
    if glm_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=glm_key)
            # Query z-ai/glm-5.1
            res = client.chat.completions.create(
                model="z-ai/glm-5.1",
                messages=[{"role": "user", "content": "Respond with 'GLM_5.1_SUCCESS'"}],
                max_tokens=50
            )
            print(f"[OK] GLM-5.1 Success. Response: {res.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"[ERROR] GLM-5.1 Failed: {e}")
    else:
        print("[WARNING] NVIDIA_API_KEY_GLM missing")

    # 2. DeepSeek V4 Pro
    pro_key = os.getenv("NVIDIA_API_KEY_DEEPSEEK_PRO")
    if pro_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=pro_key)
            res = client.chat.completions.create(
                model="deepseek-ai/deepseek-v4-pro",
                messages=[{"role": "user", "content": "Respond with 'DEEPSEEK_PRO_SUCCESS'"}],
                max_tokens=50,
                extra_body={"chat_template_kwargs": {"thinking": False}}
            )
            print(f"[OK] DeepSeek V4 Pro Success. Response: {res.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"[ERROR] DeepSeek V4 Pro Failed: {e}")
    else:
        print("[WARNING] NVIDIA_API_KEY_DEEPSEEK_PRO missing")

    # 3. DeepSeek V4 Flash
    flash_key = os.getenv("NVIDIA_API_KEY_DEEPSEEK_FLASH")
    if flash_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=flash_key)
            res = client.chat.completions.create(
                model="deepseek-ai/deepseek-v4-flash",
                messages=[{"role": "user", "content": "Respond with 'DEEPSEEK_FLASH_SUCCESS'"}],
                max_tokens=50,
                extra_body={"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}}
            )
            print(f"[OK] DeepSeek V4 Flash Success. Response: {res.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"[ERROR] DeepSeek V4 Flash Failed: {e}")
    else:
        print("[WARNING] NVIDIA_API_KEY_DEEPSEEK_FLASH missing")

def test_groq():
    print("\n--- Testing Groq API ---")
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("[ERROR] GROQ_API_KEY missing")
        return
    try:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)
        models = client.models.list()
        print(f"[OK] Groq API Connected. Models found.")
    except Exception as e:
        print(f"[ERROR] Groq API Failed: {e}")


if __name__ == "__main__":
    for test in [test_sqlite_db, test_google_studio_gemini, test_google_studio_gemma, test_groq, test_new_nvidia_models]:
        try:
            test()
        except Exception as ex:
            print(f"[FATAL] Test {test.__name__} failed: {ex}")
