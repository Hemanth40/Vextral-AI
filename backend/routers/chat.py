"""
Vextral Chat Router
Handles user questions using RAG (document-specific) or General AI mode
"""

import os
import time
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from services.embedder import embedder
from services.vector_store import vector_store
from services.generator import generator
from services.database import insert_chat_message, get_chat_history

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    tenant_id: str
    source_file: Optional[str] = None  # None = general AI, filename = document chat
    chat_history: list = []


@router.post("/ask")
async def ask_question(request: ChatRequest):
    """
    Answer a user question using:
    - RAG pipeline (if source_file is provided)
    - General AI knowledge (if source_file is None)
    """
    start_time = time.time()
    
    mode = f"📄 Document: {request.source_file}" if request.source_file else "🤖 General AI"
    
    logger.info(f"{'='*60}")
    logger.info(f"💬 [{mode}] Question from {request.tenant_id}: {request.question}")
    
    # Validate question
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question is too short")
    
    try:
        relevant_chunks = []
        chunks_used = 0
        sources = []
        
        if request.source_file:
            # === RAG MODE: Search specific document ===
            logger.info(f"⚙️  Generating question embedding...")
            question_vector = embedder.embed_text(request.question, input_type="query")
            
            logger.info(f"⚙️  Searching in document: {request.source_file}...")
            relevant_chunks = vector_store.search_chunks(
                request.tenant_id,
                question_vector,
                top_k=5,
                source_file=request.source_file
            )
            
            if relevant_chunks:
                logger.info(f"✓ Found {len(relevant_chunks)} relevant chunks")
                sources = [f"Chunk {i+1}" for i in range(len(relevant_chunks))]
                chunks_used = len(relevant_chunks)
            else:
                logger.warning("⚠️  No relevant chunks found in document")
        else:
            # === GENERAL AI MODE: No document search ===
            logger.info(f"🤖 General AI mode - skipping document search")
        
        # Generate answer
        logger.info(f"⚙️  Generating answer with {generator.model}...")
        answer = generator.generate_answer(
            request.question,
            relevant_chunks,
            request.tenant_id,
            chat_history=request.chat_history
        )
        logger.info(f"✓ Answer generated")
        
        # Save to chat history with source_file
        insert_chat_message(request.tenant_id, request.question, answer, request.source_file)
        logger.info(f"✓ Saved to history")
        
        response_time = int((time.time() - start_time) * 1000)
        logger.info(f"✅ Response generated in {response_time}ms")
        logger.info(f"{'='*60}")
        
        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": chunks_used,
            "response_time_ms": response_time,
            "mode": "document" if request.source_file else "general"
        }
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        logger.info(f"{'='*60}")
        
        return {
            "answer": "I encountered an error processing your question. Please try again.",
            "sources": [],
            "chunks_used": 0,
            "error": str(e)
        }


@router.get("/history/{tenant_id}")
async def get_history(tenant_id: str, limit: int = 20, source_file: Optional[str] = None):
    """
    Get chat history for a tenant, optionally filtered by document
    """
    try:
        history = get_chat_history(tenant_id, limit, source_file)
        
        # Reverse to show oldest first
        history_list = list(reversed(history)) if history else []
        
        return {
            "success": True,
            "history": history_list,
            "count": len(history_list)
        }
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.delete("/history/{tenant_id}")
async def clear_history(tenant_id: str, source_file: Optional[str] = None):
    """
    Clear chat history - per document or general
    """
    from services.database import delete_chat_history
    
    try:
        delete_chat_history(tenant_id, source_file)
        label = f"for {source_file}" if source_file else "general AI"
        logger.info(f"Chat history cleared ({label}) for {tenant_id}")
        return {"success": True, "message": f"Chat history cleared ({label})"}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")
