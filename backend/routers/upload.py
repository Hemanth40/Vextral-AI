"""
Vextral Upload Router
Handles document upload, processing, and deletion
"""

import os
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from dotenv import load_dotenv
from uuid import uuid4
from datetime import datetime

from services.parser import parser
from services.embedder import embedder
from services.vector_store import vector_store
from services.database import insert_document, delete_document

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form(...)
):
    """
    Upload and process a document
    """
    logger.info(f"{'='*60}")
    logger.info(f"📄 Processing upload: {file.filename} for tenant: {tenant_id}")
    
    # Step 1: Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt', '.csv', '.md', '.json', '.png', '.jpg', '.jpeg', '.webp']
    file_ext = '.' + file.filename.lower().split('.')[-1]
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Step 2: Read file bytes
        file_bytes = await file.read()
        logger.info(f"✓ Read {len(file_bytes)} bytes from {file.filename}")
        
        # Step 3: Parse document
        logger.info(f"⚙️  Parsing document...")
        chunks = parser.parse_document(file_bytes, file.filename)
        logger.info(f"✓ Extracted {len(chunks)} chunks")

        if not chunks:
            raise HTTPException(status_code=400, detail="No readable content found in this document")
        
        # Step 4: Generate embeddings
        logger.info(f"⚙️  Generating embeddings...")
        chunks_with_vectors = []

        text_items = [
            (i, chunk) for i, chunk in enumerate(chunks)
            if chunk.get("chunk_type") == "text" and str(chunk.get("text", "")).strip()
        ]
        image_items = [
            (i, chunk) for i, chunk in enumerate(chunks)
            if chunk.get("chunk_type") == "image"
        ]

        # Batch embed text chunks for faster uploads on large documents.
        if text_items:
            texts = [chunk["text"] for _, chunk in text_items]
            vectors = embedder.embed_text_batch(texts, input_type="passage", batch_size=32)

            for (orig_index, chunk), vector in zip(text_items, vectors):
                if vector is None:
                    logger.warning(f"⚠️  Warning: Failed to embed text chunk {orig_index}")
                    continue

                chunks_with_vectors.append({
                    "id": str(uuid4()),
                    "vector": vector,
                    "text": chunk["text"],
                    "source_file": file.filename,
                    "page_number": chunk.get("page_number", 0),
                    "chunk_type": chunk["chunk_type"],
                    "chunk_index": chunk.get("chunk_index", orig_index)
                })

        # Image chunks are typically fewer; keep them per-item.
        for orig_index, chunk in image_items:
            try:
                vector = embedder.embed_image(chunk["image_base64"])
                chunks_with_vectors.append({
                    "id": str(uuid4()),
                    "vector": vector,
                    "text": chunk["text"],
                    "source_file": file.filename,
                    "page_number": chunk.get("page_number", 0),
                    "chunk_type": chunk["chunk_type"],
                    "chunk_index": chunk.get("chunk_index", orig_index)
                })
            except Exception as e:
                logger.warning(f"⚠️  Warning: Failed to embed image chunk {orig_index}: {e}")
                continue
        
        logger.info(f"✓ Generated {len(chunks_with_vectors)} embeddings")

        if not chunks_with_vectors:
            raise HTTPException(
                status_code=400,
                detail="Unable to generate embeddings from this document. Try a clearer or text-based file."
            )
        
        # Step 5: Ensure collection exists
        logger.info(f"⚙️  Preparing vector database...")
        vector_store.ensure_collection(tenant_id)
        
        # Step 6: Upsert to Qdrant
        logger.info(f"⚙️  Storing vectors...")
        vector_store.upsert_chunks(tenant_id, chunks_with_vectors)
        
        # Step 7: Save metadata to PostgreSQL
        logger.info(f"⚙️  Saving metadata...")
        insert_document(tenant_id, file.filename, len(chunks_with_vectors))
        logger.info(f"✓ Saved metadata to database")
        
        logger.info(f"✅ SUCCESS: {file.filename} processed successfully!")
        logger.info(f"{'='*60}")
        
        return {
            "success": True,
            "filename": file.filename,
            "chunks_processed": len(chunks_with_vectors)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        logger.info(f"{'='*60}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/list/{tenant_id}")
async def list_documents(tenant_id: str):
    """
    List all documents for a tenant
    """
    from services.database import execute_query
    
    try:
        query = """
            SELECT id, filename, chunk_count, uploaded_at 
            FROM documents 
            WHERE tenant_id = %s 
            ORDER BY uploaded_at DESC
        """
        documents = execute_query(query, (tenant_id,), fetch=True)
        
        # Convert datetime objects to ISO strings for JSON serialization
        results = []
        if documents:
            for doc in documents:
                doc_dict = dict(doc)
                if isinstance(doc_dict.get('uploaded_at'), datetime):
                    doc_dict['uploaded_at'] = doc_dict['uploaded_at'].isoformat()
                results.append(doc_dict)
        
        return {
            "success": True,
            "documents": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/document/{filename}")
async def delete_document_endpoint(filename: str, tenant_id: str):
    """
    Delete a document and all its vectors
    """
    logger.info(f"🗑️  Deleting document: {filename} for tenant: {tenant_id}")
    
    try:
        # Delete from Qdrant
        vector_store.delete_document(tenant_id, filename)
        
        # Delete from PostgreSQL
        delete_document(tenant_id, filename)
        
        logger.info(f"✓ Deleted {filename}")
        
        return {
            "success": True,
            "message": f"Document {filename} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
