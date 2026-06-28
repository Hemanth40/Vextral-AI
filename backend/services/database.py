"""
Vextral AI v2 - Database Service
Uses Supabase Python SDK (REST API) as primary database.
Falls back to local SQLite when SUPABASE_URL/KEY are not set.
"""

import os
import sqlite3
import logging
from uuid import uuid4
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Mode Detection
# ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
IS_SUPABASE  = bool(SUPABASE_URL and SUPABASE_KEY)
IS_SQLITE    = not IS_SUPABASE

SQLITE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "vextral.db"
)

# ─────────────────────────────────────────────
# Supabase Client Init
# ─────────────────────────────────────────────
_supabase_client = None

def get_supabase():
    """Return a cached Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


if IS_SUPABASE:
    logger.info("[OK] Database: Supabase (cloud PostgreSQL via SDK)")
else:
    logger.info("[OK] Database: Local SQLite (fallback)")


# ─────────────────────────────────────────────
# SQLite Auto-Init (local dev only)
# ─────────────────────────────────────────────
def init_sqlite_db():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    supabase_path TEXT DEFAULT NULL,
                    gemini_file_uri TEXT DEFAULT NULL,
                    gemini_expires_at TEXT DEFAULT NULL,
                    chunk_count INTEGER DEFAULT 0,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, filename)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_tenant "
                "ON documents(tenant_id)"
            )
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
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_tenant "
                "ON chat_history(tenant_id, created_at)"
            )
        logger.info("[OK] SQLite tables ready")
    finally:
        conn.close()


if IS_SQLITE:
    init_sqlite_db()


# ─────────────────────────────────────────────
# SQLite Helper
# ─────────────────────────────────────────────
def _sqlite_execute(query: str, params=None, fetch=False):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        if fetch:
            rows = cur.fetchall()
            conn.commit()
            return [dict(r) for r in rows]
        conn.commit()
        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────
# Document Operations
# ─────────────────────────────────────────────
def insert_document(tenant_id: str, filename: str, chunk_count: int = 0,
                    supabase_path: str = None, gemini_file_uri: str = None,
                    gemini_expires_at: str = None):
    """Insert or upsert a document record."""
    doc_id = str(uuid4())

    if IS_SUPABASE:
        sb = get_supabase()
        sb.table("documents").upsert({
            "id": doc_id,
            "tenant_id": tenant_id,
            "filename": filename,
            "supabase_path": supabase_path,
            "gemini_file_uri": gemini_file_uri,
            "gemini_expires_at": gemini_expires_at,
            "chunk_count": chunk_count,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="tenant_id,filename").execute()
    else:
        _sqlite_execute("""
            INSERT INTO documents
                (id, tenant_id, filename, supabase_path, gemini_file_uri,
                 gemini_expires_at, chunk_count, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (tenant_id, filename) DO UPDATE SET
                supabase_path     = excluded.supabase_path,
                gemini_file_uri   = excluded.gemini_file_uri,
                gemini_expires_at = excluded.gemini_expires_at,
                chunk_count       = excluded.chunk_count,
                uploaded_at       = CURRENT_TIMESTAMP
        """, (doc_id, tenant_id, filename, supabase_path,
              gemini_file_uri, gemini_expires_at, chunk_count))

    logger.info(f"Document saved: {filename} for {tenant_id}")


def update_gemini_uri(tenant_id: str, filename: str,
                      gemini_file_uri: str, gemini_expires_at: str):
    """Refresh Gemini file URI after re-upload."""
    if IS_SUPABASE:
        get_supabase().table("documents").update({
            "gemini_file_uri": gemini_file_uri,
            "gemini_expires_at": gemini_expires_at,
        }).eq("tenant_id", tenant_id).eq("filename", filename).execute()
    else:
        _sqlite_execute(
            "UPDATE documents SET gemini_file_uri=?, gemini_expires_at=? "
            "WHERE tenant_id=? AND filename=?",
            (gemini_file_uri, gemini_expires_at, tenant_id, filename)
        )
    logger.info(f"Gemini URI refreshed for {filename}")


def get_document(tenant_id: str, filename: str) -> dict | None:
    """Fetch a single document record."""
    if IS_SUPABASE:
        res = (get_supabase().table("documents")
               .select("*")
               .eq("tenant_id", tenant_id)
               .eq("filename", filename)
               .limit(1)
               .execute())
        return res.data[0] if res.data else None
    rows = _sqlite_execute(
        "SELECT * FROM documents WHERE tenant_id=? AND filename=? LIMIT 1",
        (tenant_id, filename), fetch=True
    )
    return rows[0] if rows else None


def list_documents(tenant_id: str) -> list[dict]:
    """List all documents for a tenant, newest first."""
    if IS_SUPABASE:
        res = (get_supabase().table("documents")
               .select("id,tenant_id,filename,supabase_path,gemini_file_uri,gemini_expires_at,chunk_count,uploaded_at")
               .eq("tenant_id", tenant_id)
               .order("uploaded_at", desc=True)
               .execute())
        return res.data or []

    rows = _sqlite_execute(
        "SELECT * FROM documents WHERE tenant_id=? ORDER BY uploaded_at DESC",
        (tenant_id,), fetch=True
    ) or []
    for doc in rows:
        if isinstance(doc.get("uploaded_at"), datetime):
            doc["uploaded_at"] = doc["uploaded_at"].isoformat()
    return rows


def count_documents(tenant_id: str) -> int:
    """Count documents for a tenant."""
    if IS_SUPABASE:
        res = (get_supabase().table("documents")
               .select("id", count="exact")
               .eq("tenant_id", tenant_id)
               .execute())
        return res.count or 0
    rows = _sqlite_execute(
        "SELECT COUNT(*) as cnt FROM documents WHERE tenant_id=?",
        (tenant_id,), fetch=True
    )
    return rows[0]["cnt"] if rows else 0


def delete_document(tenant_id: str, filename: str):
    """Delete a document record."""
    if IS_SUPABASE:
        (get_supabase().table("documents")
         .delete()
         .eq("tenant_id", tenant_id)
         .eq("filename", filename)
         .execute())
    else:
        _sqlite_execute(
            "DELETE FROM documents WHERE tenant_id=? AND filename=?",
            (tenant_id, filename)
        )
    logger.info(f"Document deleted: {filename}")


# ─────────────────────────────────────────────
# Chat History Operations
# ─────────────────────────────────────────────
def insert_chat_message(tenant_id: str, question: str, answer: str,
                        source_file: str = None):
    """Save a Q&A pair to chat history."""
    msg_id = str(uuid4())
    if IS_SUPABASE:
        get_supabase().table("chat_history").insert({
            "id": msg_id,
            "tenant_id": tenant_id,
            "question": question,
            "answer": answer,
            "source_file": source_file,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    else:
        _sqlite_execute("""
            INSERT INTO chat_history
                (id, tenant_id, question, answer, source_file, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (msg_id, tenant_id, question, answer, source_file))


def get_chat_history(tenant_id: str, limit: int = 20,
                     source_file: str = None) -> list[dict]:
    """Get chat history, optionally filtered by document."""
    if IS_SUPABASE:
        q = (get_supabase().table("chat_history")
             .select("id,tenant_id,question,answer,source_file,created_at")
             .eq("tenant_id", tenant_id)
             .order("created_at", desc=True)
             .limit(limit))
        if source_file:
            q = q.eq("source_file", source_file)
        else:
            q = q.is_("source_file", "null")
        return q.execute().data or []

    if source_file:
        rows = _sqlite_execute(
            "SELECT * FROM chat_history WHERE tenant_id=? AND source_file=? "
            "ORDER BY created_at DESC LIMIT ?",
            (tenant_id, source_file, limit), fetch=True
        )
    else:
        rows = _sqlite_execute(
            "SELECT * FROM chat_history WHERE tenant_id=? AND source_file IS NULL "
            "ORDER BY created_at DESC LIMIT ?",
            (tenant_id, limit), fetch=True
        )
    for row in (rows or []):
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
    return rows or []


def delete_chat_history(tenant_id: str, source_file: str = None):
    """Delete chat history per document or all general chat."""
    if IS_SUPABASE:
        q = get_supabase().table("chat_history").delete().eq("tenant_id", tenant_id)
        if source_file:
            q.eq("source_file", source_file).execute()
        else:
            q.is_("source_file", "null").execute()
    else:
        if source_file:
            _sqlite_execute(
                "DELETE FROM chat_history WHERE tenant_id=? AND source_file=?",
                (tenant_id, source_file)
            )
        else:
            _sqlite_execute(
                "DELETE FROM chat_history WHERE tenant_id=? AND source_file IS NULL",
                (tenant_id,)
            )
    logger.info(f"Chat history cleared for {tenant_id}")


# ─────────────────────────────────────────────
# Legacy compatibility shim (used by upload.py)
# ─────────────────────────────────────────────
def execute_query(query: str, params=None, fetch=False):
    """
    Legacy SQL executor — kept for backward compat with upload.py COUNT query.
    Routes only the document count check; everything else should use named functions.
    """
    if IS_SUPABASE and "COUNT(*)" in query and "documents" in query:
        tenant_id = params[0] if params else None
        cnt = count_documents(tenant_id) if tenant_id else 0
        return [[cnt]]
    if IS_SUPABASE and "SELECT id, filename, chunk_count" in query:
        tenant_id = params[0] if params else None
        return list_documents(tenant_id) if tenant_id else []
    # SQLite fallback
    return _sqlite_execute(query, params, fetch)
