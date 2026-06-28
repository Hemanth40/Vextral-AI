"""
Vextral File Storage Service
Handles permanent document upload, download, and deletion using Supabase Storage.
"""

import os
import logging
from services.database import get_supabase, IS_SUPABASE

logger = logging.getLogger(__name__)

BUCKET_NAME = "documents"

class FileStorageService:
    """Service to interact with Supabase Storage bucket."""

    def __init__(self):
        self.enabled = IS_SUPABASE
        if not self.enabled:
            logger.warning("Supabase configuration missing. Local SQLite mode has no permanent storage.")
        else:
            self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create the documents storage bucket if it does not exist in Supabase."""
        try:
            sb = get_supabase()
            # Try to list buckets to verify if it exists
            buckets = sb.storage.list_buckets()
            exists = any(b.name == BUCKET_NAME for b in buckets)
            if not exists:
                logger.info(f"⚙️ Creating Supabase Storage bucket '{BUCKET_NAME}'...")
                sb.storage.create_bucket(BUCKET_NAME, options={"public": False})
                logger.info(f"✓ Created bucket '{BUCKET_NAME}' successfully")
        except Exception as e:
            # We fail silently here because key might lack permission to list but can write
            logger.warning(f"Unable to verify/create Supabase Storage bucket: {e}")

    def upload_file(self, tenant_id: str, filename: str, file_bytes: bytes) -> str:
        """
        Upload file bytes to tenant-scoped path in Supabase Storage.
        Returns the supabase_path.
        """
        if not self.enabled:
            # Local development mock path
            return f"local/{tenant_id}/{filename}"

        # Clean tenant_id and filename for path
        supabase_path = f"{tenant_id}/{filename}"
        sb = get_supabase()

        try:
            # Upload file bytes (forcing overwrite / clean upsert)
            sb.storage.from_(BUCKET_NAME).upload(
                path=supabase_path,
                file=file_bytes,
                file_options={"upsert": "true"}
            )
            logger.info(f"✓ File uploaded to Supabase Storage: {supabase_path}")
            return supabase_path
        except Exception as e:
            logger.error(f"Failed to upload file to Supabase Storage: {e}")
            raise Exception(f"Storage upload failed: {str(e)}")

    def download_file(self, supabase_path: str) -> bytes:
        """Download file bytes from Supabase Storage."""
        if not self.enabled:
            raise Exception("Supabase Storage is disabled in SQLite mode.")

        sb = get_supabase()
        try:
            res = sb.storage.from_(BUCKET_NAME).download(supabase_path)
            return res
        except Exception as e:
            logger.error(f"Failed to download file from Supabase Storage: {e}")
            raise Exception(f"Storage download failed: {str(e)}")

    def delete_file(self, supabase_path: str) -> bool:
        """Delete file from Supabase Storage."""
        if not self.enabled:
            return True

        sb = get_supabase()
        try:
            sb.storage.from_(BUCKET_NAME).remove([supabase_path])
            logger.info(f"✓ File deleted from Supabase Storage: {supabase_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Supabase Storage: {e}")
            return False

# Singleton instance
file_storage = FileStorageService()
