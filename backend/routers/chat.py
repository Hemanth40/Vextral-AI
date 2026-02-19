"""
Vextral Chat Router
Handles user questions using RAG (document-specific) or General AI mode
"""

import os
import time
import logging
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
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

RETRIEVAL_TOP_K = max(4, min(int(os.getenv("RAG_RETRIEVAL_TOP_K", "12")), 20))
FINAL_CONTEXT_CHUNKS = max(2, min(int(os.getenv("RAG_CONTEXT_CHUNKS", "6")), 10))


class ChatRequest(BaseModel):
    question: str
    tenant_id: str
    source_file: Optional[str] = None  # None = general AI, filename = document chat
    chat_history: list = Field(default_factory=list)


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase alphanumeric terms for lightweight lexical reranking."""
    return set(re.findall(r"[a-zA-Z0-9]{3,}", text.lower()))


def _rerank_chunks(question: str, chunks: list[dict], max_chunks: int = 6) -> list[dict]:
    """
    Re-rank vector search results by combining semantic similarity and lexical overlap.
    This improves precision for document-grounded answers.
    """
    if not chunks:
        return []

    question_terms = _tokenize(question)
    top_semantic_score = max(float(chunk.get("score", 0.0)) for chunk in chunks)
    min_semantic_threshold = max(0.2, top_semantic_score * 0.65)

    ranked: list[dict] = []
    for chunk in chunks:
        semantic_score = float(chunk.get("score", 0.0))
        if semantic_score < min_semantic_threshold:
            continue

        chunk_terms = _tokenize(chunk.get("text", ""))
        lexical_overlap = (
            len(question_terms & chunk_terms) / len(question_terms)
            if question_terms
            else 0.0
        )
        combined_score = (semantic_score * 0.85) + (lexical_overlap * 0.15)

        ranked_chunk = dict(chunk)
        ranked_chunk["combined_score"] = combined_score
        ranked_chunk["lexical_overlap"] = lexical_overlap
        ranked.append(ranked_chunk)

    # Keep a fallback chunk if semantic search produced results but thresholding removed all.
    if not ranked and chunks:
        fallback = dict(chunks[0])
        fallback["combined_score"] = float(fallback.get("score", 0.0))
        fallback["lexical_overlap"] = 0.0
        ranked = [fallback]

    ranked.sort(key=lambda c: c.get("combined_score", 0.0), reverse=True)
    return ranked[:max_chunks]


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
        relevant_chunks: list[dict] = []
        chunks_used = 0
        sources = []
        
        if request.source_file:
            # === RAG MODE: Search specific document ===
            logger.info(f"⚙️  Generating question embedding...")
            question_vector = embedder.embed_text(request.question, input_type="query")
            
            logger.info(f"⚙️  Searching in document: {request.source_file}...")
            raw_chunks = vector_store.search_chunks_detailed(
                request.tenant_id,
                question_vector,
                top_k=RETRIEVAL_TOP_K,
                source_file=request.source_file
            )

            relevant_chunks = _rerank_chunks(
                request.question,
                raw_chunks,
                max_chunks=FINAL_CONTEXT_CHUNKS
            )

            if relevant_chunks:
                logger.info(f"✓ Retrieved {len(raw_chunks)} chunks, using top {len(relevant_chunks)} after reranking")
                sources = [
                    f"{chunk.get('source_file', request.source_file)} (page {chunk.get('page_number', 0)})"
                    for chunk in relevant_chunks
                ]
                chunks_used = len(relevant_chunks)
            else:
                logger.warning("⚠️  No relevant chunks found in document")
        else:
            # === GENERAL AI MODE: No document search ===
            logger.info(f"🤖 General AI mode - skipping document search")
        
        if request.source_file and not relevant_chunks:
            # Avoid hallucinations when user asked for document-grounded answer but retrieval found nothing useful.
            answer = (
                "I couldn't find enough relevant evidence in this document for that question.\n\n"
                "Try one of these:\n"
                "- Ask with exact terms from the document\n"
                "- Ask about a specific section/page\n"
                "- Rephrase with more context"
            )

            insert_chat_message(request.tenant_id, request.question, answer, request.source_file)
            response_time = int((time.time() - start_time) * 1000)

            return {
                "answer": answer,
                "sources": [],
                "chunks_used": 0,
                "response_time_ms": response_time,
                "mode": "document"
            }

        # Generate answer
        logger.info("⚙️  Generating grounded answer...")
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ ERROR: {str(e)}")
        logger.info(f"{'='*60}")
        raise HTTPException(status_code=500, detail="Failed to process the question")


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
