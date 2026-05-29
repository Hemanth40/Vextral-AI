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

def test_lancedb():
    print("\n--- Testing LanceDB (Local Vector Store) ---")
    try:
        import lancedb
        import pyarrow as pa
        
        db_path = os.path.join(os.path.dirname(__file__), "data", "vextral_lancedb")
        db = lancedb.connect(db_path)
        
        test_table = "tenant_test_diagnose"
        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), 2048)),
            pa.field("text", pa.string()),
            pa.field("source_file", pa.string())
        ])
        
        if test_table in db.table_names():
            db.drop_table(test_table)
            
        table = db.create_table(test_table, schema=schema)
        table.add([{
            "id": "1",
            "vector": [0.1] * 2048,
            "text": "Hello LanceDB",
            "source_file": "test.txt"
        }])
        
        res = table.search([0.1]*2048).limit(1).to_list()
        if res and res[0]["text"] == "Hello LanceDB":
            print("[OK] LanceDB connected, vectors indexed and queried successfully.")
        else:
            print(f"[ERROR] LanceDB unexpected query result: {res}")
            
        db.drop_table(test_table)
    except Exception as e:
        print(f"[ERROR] LanceDB Failed: {e}")

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

def test_upstash_redis():
    print("\n--- Testing Upstash Redis ---")
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        print("[WARNING] Upstash Redis URL or Token missing in environment variables.")
        return
    try:
        from upstash_redis import Redis
        client = Redis(url=url, token=token)
        test_key = "vextral:test:diagnose"
        client.set(test_key, "Upstash is operational!")
        val = client.get(test_key)
        if val == "Upstash is operational!":
            print("[OK] Upstash Redis Cloud Database verified. Read and Write operations succeeded.")
        else:
            print(f"[ERROR] Upstash Redis returned unexpected value: {val}")
        client.delete(test_key)
    except Exception as e:
        print(f"[ERROR] Upstash Redis Connection Failed: {e}")

def test_qdrant_cloud():
    print("\n--- Testing Qdrant Cloud ---")
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_KEY")
    if not url or not key:
        print("[WARNING] Qdrant Cloud URL or Key missing in environment variables.")
        return
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=url, api_key=key, timeout=10)
        collections = client.get_collections().collections
        print(f"[OK] Qdrant Cloud verified successfully. Connected. Found {len(collections)} collections.")
    except Exception as e:
        print(f"[ERROR] Qdrant Cloud Connection Failed: {e}")

if __name__ == "__main__":
    for test in [test_sqlite_db, test_lancedb, test_google_studio_gemini, test_google_studio_gemma, test_groq, test_upstash_redis, test_qdrant_cloud]:
        try:
            test()
        except Exception as ex:
            print(f"[FATAL] Test {test.__name__} failed: {ex}")
