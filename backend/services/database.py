"""
Database helper for direct PostgreSQL connection to Supabase
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection string from Supabase
DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    """Get a database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def execute_query(query, params=None, fetch=False):
    """Execute a SQL query"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                conn.commit()
                return result
            conn.commit()
            return None
    finally:
        conn.close()


def insert_document(tenant_id, filename, chunk_count):
    """Insert document metadata"""
    query = """
        INSERT INTO documents (id, tenant_id, filename, chunk_count, uploaded_at)
        VALUES (gen_random_uuid(), %s, %s, %s, NOW())
        ON CONFLICT (tenant_id, filename) DO UPDATE
        SET chunk_count = EXCLUDED.chunk_count, uploaded_at = NOW()
    """
    execute_query(query, (tenant_id, filename, chunk_count))


def delete_document(tenant_id, filename):
    """Delete document metadata"""
    query = "DELETE FROM documents WHERE tenant_id = %s AND filename = %s"
    execute_query(query, (tenant_id, filename))


def insert_chat_message(tenant_id, question, answer, source_file=None):
    """Insert chat history with optional source_file for per-document history"""
    query = """
        INSERT INTO chat_history (id, tenant_id, question, answer, source_file, created_at)
        VALUES (gen_random_uuid(), %s, %s, %s, %s, NOW())
    """
    execute_query(query, (tenant_id, question, answer, source_file))


def get_chat_history(tenant_id, limit=20, source_file=None):
    """Get chat history for a tenant, optionally filtered by document"""
    if source_file:
        # Get history for specific document
        query = """
            SELECT id, tenant_id, question, answer, source_file, created_at
            FROM chat_history
            WHERE tenant_id = %s AND source_file = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (tenant_id, source_file, limit), fetch=True)
    else:
        # Get general AI chat history (where source_file IS NULL)
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
    if source_file:
        query = "DELETE FROM chat_history WHERE tenant_id = %s AND source_file = %s"
        execute_query(query, (tenant_id, source_file))
    else:
        # Delete general AI chat history only
        query = "DELETE FROM chat_history WHERE tenant_id = %s AND source_file IS NULL"
        execute_query(query, (tenant_id,))
