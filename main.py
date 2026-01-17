from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional
from app.LLM_Service.ai_service import generate_gemini_response, generate_summary
from app.schema.schema import AIRequest, AIResponse, SummaryRequest, SummaryResponse
from config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI assistant")


@app.post("/api/chat", response_model=AIResponse)
async def generate(request: AIRequest):
    try:
        # Validate API key
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set")
            raise ValueError("API key is not configured")
        
        messages = [msg.dict() for msg in request.messages]
        
        logger.info(f"Generating response for user {request.user_id}")
        response_text = await generate_gemini_response(messages, request.user_id)
        
        return AIResponse(response=response_text, success=True)
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return AIResponse(response="", success=False, error=f"Error: {str(e)}")

@app.post("/api/summarize", response_model=SummaryResponse)
async def summarize_thread(request: SummaryRequest):
    """
    Generate a summary of the last 10 messages in a thread.
    
    Args:
        request: SummaryRequest containing thread_id, messages (last 10), and user_id
        
    Returns:
        SummaryResponse with the generated summary
    """
    try:
        # Validate API key
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set")
            raise ValueError("API key is not configured")
        
        messages = [msg.dict() for msg in request.messages]
        
        logger.info(f"Generating summary for thread {request.thread_id}, user {request.user_id}")
        summary_text = await generate_summary(messages, request.thread_id, request.user_id)
        
        return SummaryResponse(
            summary=summary_text,
            thread_id=request.thread_id,
            message_count=len(messages),
            success=True
        )
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return SummaryResponse(
            summary="",
            thread_id=request.thread_id,
            message_count=len(request.messages),
            success=False,
            error=f"Error: {str(e)}"
        )

@app.get("/health")
async def health():
    try:
        # Check if API key is configured
        if not settings.GROQ_API_KEY:
            return {"status": "error", "message": "API key not configured"}
        
        return {"status": "ok", "model": settings.MODEL}
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "error", "message": str(e)}