"""
Vextral Upload Router
Handles document upload, listing, and deletion for Vextral v2.
Integrates Supabase Storage and Gemini File API on FastAPI worker thread pool.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from dotenv import load_dotenv

from services.file_storage import file_storage
from services.gemini_reader import gemini_reader
from services.database import insert_document, get_document, list_documents, delete_document, count_documents

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/document")
def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form(...)
):
    """
    Upload and process a document.
    Permanently stores in Supabase Storage, then registers with Gemini File API.
    Executed in thread pool to prevent blocking.
    """
    logger.info(f"{'='*60}")
    logger.info(f"📄 Processing upload: {file.filename} for tenant: {tenant_id}")

    # 1. Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt', '.csv', '.md', '.json', '.png', '.jpg', '.jpeg', '.webp']
    file_ext = '.' + file.filename.lower().split('.')[-1]

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # 2. Enforce limits: Max 5 documents per tenant
        doc_count = count_documents(tenant_id)
        if doc_count >= 5:
            raise HTTPException(
                status_code=403,
                detail="Storage limit reached. You can only store up to 5 documents. Please delete an old document first."
            )

        # 3. Read file bytes and enforce size limit
        file_bytes = file.file.read()
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File is too large. Maximum allowed size is 50MB."
            )

        logger.info(f"✓ Read {len(file_bytes)} bytes from {file.filename}")

        # 4. Upload permanently to Supabase Storage
        logger.info("⚙️ Uploading to Supabase Storage...")
        supabase_path = file_storage.upload_file(tenant_id, file.filename, file_bytes)

        # 5. Upload to Gemini File API
        logger.info("⚙️ Registering with Gemini File API...")
        gemini_data = gemini_reader.upload_to_gemini(file_bytes, file.filename)

        # 6. Save metadata to database
        logger.info("⚙️ Saving document metadata...")
        insert_document(
            tenant_id=tenant_id,
            filename=file.filename,
            chunk_count=0,  # No chunking in native Gemini reader
            supabase_path=supabase_path,
            gemini_file_uri=gemini_data["gemini_file_uri"],
            gemini_expires_at=gemini_data["gemini_expires_at"]
        )

        logger.info(f"✅ SUCCESS: {file.filename} processed successfully!")
        logger.info(f"{'='*60}")

        return {
            "success": True,
            "filename": file.filename,
            "supabase_path": supabase_path,
            "gemini_file_uri": gemini_data["gemini_file_uri"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        logger.info(f"{'='*60}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/list/{tenant_id}")
def list_tenant_documents(tenant_id: str):
    """
    List all documents for a tenant.
    """
    try:
        docs = list_documents(tenant_id)
        return {
            "success": True,
            "documents": docs,
            "count": len(docs)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/document/{filename}")
def delete_document_endpoint(filename: str, tenant_id: str):
    """
    Delete a document and clean up all storage.
    """
    logger.info(f"🗑️ Deleting document: {filename} for tenant: {tenant_id}")

    try:
        # Fetch metadata
        doc = get_document(tenant_id, filename)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # 1. Delete from Supabase Storage
        if doc.get("supabase_path"):
            file_storage.delete_file(doc["supabase_path"])

        # 2. Delete from Gemini File API
        if doc.get("gemini_file_uri"):
            gemini_reader.delete_from_gemini(doc["gemini_file_uri"])

        # 3. Delete database record
        delete_document(tenant_id, filename)

        logger.info(f"✓ Deleted {filename} successfully")
        return {
            "success": True,
            "message": f"Document {filename} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
