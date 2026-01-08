from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional
from app.LLM_Service.ai_service import generate_gemini_response
from config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI assistant")

class Message(BaseModel):
    role: str    # "user" or "assistant"
    content: str
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ["user", "assistant"]:
            raise ValueError('role must be "user" or "assistant"')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('content cannot be empty')
        return v

class AIRequest(BaseModel):
    messages: List[Message]
    user_id: str
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('messages list cannot be empty')
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not v.strip():
            raise ValueError('user_id cannot be empty')
        return v

class AIResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None

@app.post("/api/generate_chat", response_model=AIResponse)
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