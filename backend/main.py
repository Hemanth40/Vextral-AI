"""
Vextral API - Main FastAPI Application
Multi-Tenant RAG SaaS Platform for Document Intelligence
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import upload, chat
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Vextral API",
    description="Ask Your Documents - Multi-Tenant RAG Platform",
    version="1.0.0"
)
@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

# Configure CORS - Allow all origins for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("="*60)
    logger.info("🚀 Vextral API Started Successfully")
    logger.info("="*60)
    logger.info("📚 Multi-Tenant RAG Platform")
    logger.info("🤖 Powered by NVIDIA NIM")
    logger.info("="*60)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Vextral is running",
        "status": "ok",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    CRITICAL: Used by Render for monitoring and cron-job.org to prevent sleep
    """
    return {
        "status": "healthy",
        "service": "Vextral API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
