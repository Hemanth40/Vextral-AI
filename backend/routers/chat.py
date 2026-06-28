"""
Vextral Chat Router
Handles user questions using Gemini File API (document-specific) or General AI mode.
"""

import os
import time
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

from services.gemini_reader import gemini_reader
from services.file_storage import file_storage
from services.generator import generator
from services.database import (
    insert_chat_message,
    get_chat_history,
    get_document,
    update_gemini_uri,
    delete_chat_history
)

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    tenant_id: str
    source_file: Optional[str] = None  # None = general AI, filename = document chat
    chat_history: list = Field(default_factory=list)
    model: Optional[str] = "gemini"


@router.post("/ask")
async def ask_question(request: ChatRequest):
    """
    Answer a user question using:
    - Gemini File API (if source_file is provided)
    - General AI models (if source_file is None)
    """
    start_time = time.time()
    
    mode = f"📄 Document: {request.source_file}" if request.source_file else "🤖 General AI"
    
    logger.info(f"{'='*60}")
    logger.info(f"💬 [{mode}] Question from {request.tenant_id}: {request.question}")
    
    if not request.question or len(request.question.strip()) < 1:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        sources = []
        chunks_used = 0
        
        if request.source_file:
            # === DOCUMENT CHAT MODE ===
            # Fetch document metadata
            doc = get_document(request.tenant_id, request.source_file)
            if not doc:
                raise HTTPException(status_code=404, detail=f"Document '{request.source_file}' not found.")
            
            gemini_file_uri = doc.get("gemini_file_uri")
            expires_at_str = doc.get("gemini_expires_at")
            
            # Check if Gemini file URI has expired or is missing
            is_expired = True
            if gemini_file_uri and expires_at_str:
                try:
                    # Parse expires_at (ISO string with timezone offset / Z)
                    # Replace Z with +00:00 to support fromisoformat on Python <= 3.10
                    clean_dt = expires_at_str.replace("Z", "+00:00")
                    expires_at = datetime.fromisoformat(clean_dt)
                    if expires_at > datetime.now(timezone.utc):
                        is_expired = False
                except Exception as ex:
                    logger.warning(f"Failed to parse gemini_expires_at '{expires_at_str}': {ex}. Assuming expired.")
            
            # If expired, download from Supabase Storage and re-upload to Gemini File API
            if is_expired:
                logger.info(f"🔄 Gemini File URI has expired or is missing. Re-uploading from Supabase Storage...")
                
                # 1. Download file bytes from Supabase Storage
                file_bytes = file_storage.download_file(doc["supabase_path"])
                
                # 2. Upload to Gemini File API
                gemini_data = gemini_reader.upload_to_gemini(file_bytes, request.source_file)
                gemini_file_uri = gemini_data["gemini_file_uri"]
                
                # 3. Update database record
                update_gemini_uri(
                    request.tenant_id,
                    request.source_file,
                    gemini_file_uri,
                    gemini_data["gemini_expires_at"]
                )
                logger.info(f"✓ Gemini File URI successfully refreshed: {gemini_file_uri}")
            
            # Query Gemini File API directly
            answer = gemini_reader.query_document(
                question=request.question,
                gemini_file_uri=gemini_file_uri,
                chat_history=request.chat_history
            )
            sources = [request.source_file]
            chunks_used = 1  # 1 whole file context
            reasoning = None
            
        else:
            # === GENERAL AI MODE ===
            # Defaults to Gemini / Kimi K2.6
            gen_res = generator.generate_answer(
                question=request.question,
                context_chunks=[],
                tenant_id=request.tenant_id,
                chat_history=request.chat_history,
                model_name=request.model
            )
            answer = gen_res.get("answer", "")
            reasoning = gen_res.get("reasoning")
        
        # Save question and answer to chat history table (embed thinking block if present)
        db_answer = f"<think>{reasoning}</think>\n\n{answer}" if reasoning else answer
        insert_chat_message(request.tenant_id, request.question, db_answer, request.source_file)
        
        response_time = int((time.time() - start_time) * 1000)
        logger.info(f"✅ Response generated in {response_time}ms")
        logger.info(f"{'='*60}")
        
        return {
            "answer": answer,
            "reasoning": reasoning,
            "sources": sources,
            "chunks_used": chunks_used,
            "response_time_ms": response_time,
            "mode": "document" if request.source_file else "general"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ ERROR: {str(e)}")
        logger.info(f"{'='*60}")
        raise HTTPException(status_code=500, detail="Failed to process the question")


@router.get("/history/{tenant_id}")
async def get_history(tenant_id: str, limit: int = 20, source_file: Optional[str] = None):
    """
    Get chat history for a tenant, optionally filtered by document.
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
    Clear chat history - per document or general.
    """
    try:
        delete_chat_history(tenant_id, source_file)
        label = f"for {source_file}" if source_file else "general AI"
        logger.info(f"Chat history cleared ({label}) for {tenant_id}")
        return {"success": True, "message": f"Chat history cleared ({label})"}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")

