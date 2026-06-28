"""
Vextral Gemini Reader Service
Manages uploading files to Gemini File API and executing queries directly on them.
"""

import os
import tempfile
import logging
from datetime import datetime, timedelta, timezone
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize the Gemini GenAI client
google_key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))
if google_key:
    # Use standard Client from google-genai SDK
    gemini_client = genai.Client(api_key=google_key)
    logger.info("✓ Initialized Google GenAI Client in Gemini Reader")
else:
    gemini_client = None
    logger.warning("⚠️ GOOGLE_API_KEY / GEMINI_API_KEY missing in Gemini Reader")


class GeminiReaderService:
    """Service to handle Gemini File API uploads and direct document querying."""

    def __init__(self):
        self.model = "gemini-2.5-flash"

    def upload_to_gemini(self, file_bytes: bytes, filename: str) -> dict:
        """
        Upload file bytes to Gemini File API.
        Returns a dictionary with gemini_file_uri and gemini_expires_at.
        """
        if not gemini_client:
            raise Exception("Google GenAI client not initialized (missing API key).")

        # Determine file extension to preserve mime-type mapping correctly
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            ext = ".txt"

        # Write bytes to a temporary file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            logger.info(f"Uploading {filename} to Gemini File API...")
            uploaded = gemini_client.files.upload(file=tmp_path)
            
            # Expiration is exactly 48 hours. Let's set the db expiry to 47 hours to be safe.
            expires_at = datetime.now(timezone.utc) + timedelta(hours=47)
            
            logger.info(f"✓ Uploaded successfully to Gemini: {uploaded.name}")
            return {
                "gemini_file_uri": uploaded.name,
                "gemini_expires_at": expires_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to upload file to Gemini File API: {e}")
            raise Exception(f"Gemini upload failed: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def delete_from_gemini(self, gemini_file_uri: str) -> bool:
        """Delete a file from the Gemini File API servers."""
        if not gemini_client or not gemini_file_uri:
            return True
        try:
            gemini_client.files.delete(name=gemini_file_uri)
            logger.info(f"✓ File deleted from Gemini: {gemini_file_uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Gemini: {e}")
            return False

    def query_document(self, question: str, gemini_file_uri: str, chat_history: list = None) -> str:
        """
        Query the document directly using the Gemini File API reference.
        Passes chat history for contextual conversations.
        """
        if not gemini_client:
            raise Exception("Google GenAI client not initialized.")

        try:
            # Retrieve the file reference object from Google
            file_ref = gemini_client.files.get(name=gemini_file_uri)
            
            # Format chat history if present
            # We will use system instruction to enforce answering only from the document context.
            system_prompt = (
                "You are Vextral AI, a document assistant.\n"
                "Your task is to answer the user's question accurately using ONLY the attached document.\n"
                "Do not hallucinate or use any external knowledge. If the answer cannot be found in the "
                "document, state clearly that you cannot find it."
            )
            
            # Build the prompt parts:
            # 1. The document reference
            # 2. History context (if any)
            # 3. The new question
            contents = [file_ref]
            
            if chat_history:
                history_text = "\n[Previous Chat History]:\n"
                for msg in chat_history:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    history_text += f"{role}: {msg.get('content')}\n"
                contents.append(history_text)
                
            contents.append(f"\nUser Question: {question}")
            
            logger.info(f"Querying Gemini 2.5 Flash on file {gemini_file_uri}...")
            response = gemini_client.models.generate_content(
                model=self.model,
                contents=contents,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.2
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error querying document via Gemini: {e}")
            raise Exception(f"Gemini query execution failed: {str(e)}")


# Singleton instance
gemini_reader = GeminiReaderService()
