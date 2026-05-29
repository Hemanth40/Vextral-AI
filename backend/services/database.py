"""
Database helper supporting:
1. Upstash Redis (Permanently free serverless cloud KV store)
2. PostgreSQL (psycopg2 for Supabase/Neon cloud database)
3. SQLite (sqlite3 for serverless offline local storage)
"""

import os
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Upstash Redis Configuration
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
IS_UPSTASH = bool(UPSTASH_URL and UPSTASH_TOKEN)

# PostgreSQL Connection Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL) and not IS_UPSTASH

# SQLite Fallback Configuration (if neither is set)
IS_SQLITE = not IS_UPSTASH and not IS_POSTGRES
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vextral.db")

# Initialize Upstash Client if active
if IS_UPSTASH:
    from upstash_redis import Redis
    redis_client = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)
    print("[OK] Configured permanent cloud database: Serverless Upstash Redis")
else:
    redis_client = None

def init_sqlite_db():
    """Initialize SQLite database tables if they do not exist"""
    if not IS_SQLITE:
        return
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        with conn:
            # 1. Create documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, filename)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id)")
            
            # 2. Create chat_history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    source_file TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_tenant_time ON chat_history(tenant_id, created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_source_file ON chat_history(tenant_id, source_file)")
            print("[OK] Auto-initialized local SQLite tables")
    finally:
        conn.close()

# Auto-initialize SQLite if we are in local development mode
if IS_SQLITE:
    init_sqlite_db()

def get_db_connection():
    """Get a database connection (PostgreSQL or SQLite)"""
    if IS_SQLITE:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    elif IS_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return None

def execute_query(query, params=None, fetch=False):
    """Execute SQL query with abstractions for SQLite, Postgres, and Upstash Redis"""
    
    # === 1. UPSTASH REDIS CLOUD DATABASE INTERCEPTOR ===
    if IS_UPSTASH:
        try:
            # Intercept "SELECT COUNT(*) FROM documents WHERE tenant_id = %s"
            if "SELECT COUNT(*)" in query:
                tenant_id = params[0]
                pattern = f"vextral:documents:{tenant_id}:*"
                keys = redis_client.keys(pattern) or []
                # Return standard list of list mimicking PG/SQLite cursor outputs
                return [[len(keys)]]
            
            # Intercept "SELECT id, filename, chunk_count, uploaded_at FROM documents WHERE tenant_id"
            elif "SELECT id, filename, chunk_count, uploaded_at" in query:
                tenant_id = params[0]
                pattern = f"vextral:documents:{tenant_id}:*"
                keys = redis_client.keys(pattern) or []
                results = []
                for k in keys:
                    raw = redis_client.get(k)
                    if raw:
                        # Upstash client handles string decoding natively
                        doc = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode("utf-8"))
                        results.append(doc)
                # Sort newest first
                results.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
                return results
            
            return None
        except Exception as e:
            print(f"Upstash Redis Query Execution Error: {e}")
            raise e
            
    # === 2. STANDARD RELATIONAL SQL DATABASES ===
    conn = get_db_connection()
    try:
        if IS_SQLITE:
            query = query.replace("%s", "?")
            if "gen_random_uuid()" in query:
                query = query.replace("gen_random_uuid()", "?")
                params = (str(uuid4()),) + tuple(params or [])
            query = query.replace("NOW()", "CURRENT_TIMESTAMP")
            query = query.replace("EXCLUDED.", "excluded.")
            
            cur = conn.cursor()
            cur.execute(query, params or ())
            if fetch:
                rows = cur.fetchall()
                result = [dict(row) for row in rows]
                conn.commit()
                return result
            conn.commit()
            return None
        else:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if fetch:
                    result = cur.fetchall()
                    conn.commit()
                    return result
                conn.commit()
                return None
    finally:
        if conn:
            conn.close()

def insert_document(tenant_id, filename, chunk_count):
    """Insert or update document metadata"""
    if IS_UPSTASH:
        key = f"vextral:documents:{tenant_id}:{filename}"
        doc_data = {
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "filename": filename,
            "chunk_count": int(chunk_count),
            "uploaded_at": datetime.utcnow().isoformat()
        }
        redis_client.set(key, json.dumps(doc_data))
        print(f"[OK] Saved document metadata to Upstash Redis: {filename}")
    elif IS_SQLITE:
        query = """
            INSERT INTO documents (id, tenant_id, filename, chunk_count, uploaded_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (tenant_id, filename) DO UPDATE
            SET chunk_count = excluded.chunk_count, uploaded_at = CURRENT_TIMESTAMP
        """
        execute_query(query, (str(uuid4()), tenant_id, filename, chunk_count))
    else:
        query = """
            INSERT INTO documents (id, tenant_id, filename, chunk_count, uploaded_at)
            VALUES (gen_random_uuid(), %s, %s, %s, NOW())
            ON CONFLICT (tenant_id, filename) DO UPDATE
            SET chunk_count = EXCLUDED.chunk_count, uploaded_at = NOW()
        """
        execute_query(query, (tenant_id, filename, chunk_count))

def delete_document(tenant_id, filename):
    """Delete document metadata"""
    if IS_UPSTASH:
        key = f"vextral:documents:{tenant_id}:{filename}"
        redis_client.delete(key)
        print(f"[OK] Deleted document metadata from Upstash Redis: {filename}")
    else:
        query = "DELETE FROM documents WHERE tenant_id = %s AND filename = %s"
        execute_query(query, (tenant_id, filename))

def insert_chat_message(tenant_id, question, answer, source_file=None):
    """Insert chat history with optional source_file for per-document history"""
    if IS_UPSTASH:
        # Separate list per document or general chat
        label = source_file if source_file else "general"
        key = f"vextral:chat_history:{tenant_id}:{label}"
        msg_data = {
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "question": question,
            "answer": answer,
            "source_file": source_file,
            "created_at": datetime.utcnow().isoformat()
        }
        redis_client.lpush(key, json.dumps(msg_data))
        # Keep only the last 40 messages to protect free memory space
        redis_client.ltrim(key, 0, 39)
        print(f"[OK] Saved chat message in Upstash Redis ({label})")
    elif IS_SQLITE:
        query = """
            INSERT INTO chat_history (id, tenant_id, question, answer, source_file, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        execute_query(query, (str(uuid4()), tenant_id, question, answer, source_file))
    else:
        query = """
            INSERT INTO chat_history (id, tenant_id, question, answer, source_file, created_at)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, NOW())
        """
        execute_query(query, (tenant_id, question, answer, source_file))

def get_chat_history(tenant_id, limit=20, source_file=None):
    """Get chat history for a tenant, optionally filtered by document"""
    if IS_UPSTASH:
        label = source_file if source_file else "general"
        key = f"vextral:chat_history:{tenant_id}:{label}"
        raw_msgs = redis_client.lrange(key, 0, limit - 1) or []
        msgs = []
        for raw in raw_msgs:
            if isinstance(raw, str):
                msgs.append(json.loads(raw))
            else:
                msgs.append(json.loads(raw.decode("utf-8")))
        return msgs
        
    if source_file:
        query = """
            SELECT id, tenant_id, question, answer, source_file, created_at
            FROM chat_history
            WHERE tenant_id = %s AND source_file = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (tenant_id, source_file, limit), fetch=True)
    else:
        query = """
            SELECT id, tenant_id, question, answer, source_file, created_at
            FROM chat_history
            WHERE tenant_id = %s AND source_file IS NULL
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (tenant_id, limit), fetch=True)

def delete_chat_history(tenant_id, source_file=None):
    """Delete chat history - per document or general"""
    if IS_UPSTASH:
        label = source_file if source_file else "general"
        key = f"vextral:chat_history:{tenant_id}:{label}"
        redis_client.delete(key)
        print(f"[OK] Cleared chat history from Upstash Redis ({label})")
    else:
        if source_file:
            query = "DELETE FROM chat_history WHERE tenant_id = %s AND source_file = %s"
            execute_query(query, (tenant_id, source_file))
        else:
            query = "DELETE FROM chat_history WHERE tenant_id = %s AND source_file IS NULL"
            execute_query(query, (tenant_id,))


