import os
import sqlite3
import logging
from dotenv import load_dotenv
from openai import OpenAI
from google import genai

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
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        has_docs = cur.fetchone()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        has_chat = cur.fetchone()
        
        if has_docs and has_chat:
            print("[OK] SQLite Local Database connected. All tables verified successfully.")
        else:
            print(f"[ERROR] SQLite Local connected but tables missing. docs={has_docs}, chat={has_chat}")
        conn.close()
    except Exception as e:
        print(f"[ERROR] SQLite Local Database Failed: {e}")


def test_google_gemini():
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
                contents="Respond with 'GEMINI_3_5_SUCCESS'."
            )
            print(f"[OK] Gemini 3.5 Success. Response: {response.text.strip()}")
        except Exception as e35:
            print(f"[WARNING] Gemini 3.5 fallback to gemini-2.5-flash: {e35}")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Respond with 'GEMINI_2_5_SUCCESS'."
            )
            print(f"[OK] Gemini 2.5 Fallback Success. Response: {response.text.strip()}")
    except Exception as e:
        print(f"[ERROR] Google Gemini client failed: {e}")


def test_groq():
    print("\n--- Testing Groq API (GPT-OSS 120B) ---")
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("[ERROR] GROQ_API_KEY missing")
        return
    try:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)
        res = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Respond with 'GROQ_120B_SUCCESS'"}],
            max_tokens=30
        )
        print(f"[OK] Groq GPT-OSS 120B Success. Response: {res.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"[ERROR] Groq API Failed: {e}")


def test_nvidia_models():
    print("\n--- Testing NVIDIA NIM Models (MiniMax-M3 & Nemotron 3 550B) ---")
    
    # 1. MiniMax M3
    minimax_key = os.getenv("NVIDIA_API_KEY_MINIMAX")
    if minimax_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=minimax_key)
            res = client.chat.completions.create(
                model="minimaxai/minimax-m3",
                messages=[{"role": "user", "content": "Respond with 'MINIMAX_M3_SUCCESS'"}],
                max_tokens=30
            )
            print(f"[OK] MiniMax-M3 Success. Response: {res.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"[ERROR] MiniMax-M3 Failed: {e}")
    else:
        print("[WARNING] NVIDIA_API_KEY_MINIMAX missing")

    # 2. Nemotron 3 Ultra 550B
    nemotron_key = os.getenv("NVIDIA_API_KEY_NEMOTRON")
    if nemotron_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nemotron_key)
            res = client.chat.completions.create(
                model="nvidia/nemotron-3-ultra-550b-a55b",
                messages=[{"role": "user", "content": "Respond with 'NEMOTRON_550B_SUCCESS'"}],
                max_tokens=50,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 500}
            )
            ans_msg = res.choices[0].message
            reasoning = getattr(ans_msg, "reasoning_content", None) or getattr(ans_msg, "reasoning", None)
            print(f"[OK] Nemotron 3 550B Success. Content: {ans_msg.content.strip()} | Reasoning tokens present: {bool(reasoning)}")
        except Exception as e:
            print(f"[ERROR] Nemotron 3 550B Failed: {e}")
    else:
        print("[WARNING] NVIDIA_API_KEY_NEMOTRON missing")


if __name__ == "__main__":
    for test in [test_sqlite_db, test_google_gemini, test_groq, test_nvidia_models]:
        try:
            test()
        except Exception as ex:
            print(f"[FATAL] Test {test.__name__} failed: {ex}")
