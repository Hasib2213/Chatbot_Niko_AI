from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.LLM_Service.ai_service import generate_gemini_response, generate_summary, generate_context_aware_response
from app.schema.schema import (
    AIRequest, AIResponse, SummaryRequest, SummaryResponse,
    ContextAwareChatRequest, ThreadListResponse, ThreadDeleteResponse, ThreadInfo
)
from app.database import db_client
from config import settings
import logging
from datetime import datetime

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
        
        messages = [msg.model_dump() for msg in request.messages]
        
        logger.info(f"Generating response for user {request.user_id}")
        response_text = await generate_gemini_response(messages, request.user_id)
        
        # Save user message to database
        if messages and db_client and db_client.is_connected():
            user_message = messages[-1]  # Last message from user
            thread_id = f"thread_{request.user_id}"  # Auto-generate thread ID
            
            # Create thread if it doesn't exist
            if not db_client.get_thread_info(thread_id):
                db_client.create_thread(thread_id, request.user_id, title=f"Chat with {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            db_client.save_message(thread_id, request.user_id, user_message.get("role", "user"), user_message.get("content", ""))
            db_client.save_message(thread_id, request.user_id, "assistant", response_text)
            db_client.update_thread_message_count(thread_id)
            logger.info(f"Messages saved to database for thread {thread_id}")
        
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
        request: SummaryRequest containing thread_id and user_id
        
    Returns:
        SummaryResponse with the generated summary
    """
    try:
        # Validate API key
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set")
            raise ValueError("API key is not configured")
        
        logger.info(f"Generating summary for thread {request.thread_id}, user {request.user_id}")
        summary_text = await generate_summary(request.thread_id, request.user_id)
        
        return SummaryResponse(
            summary=summary_text,
            thread_id=request.thread_id,
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
            success=False,
            error=f"Error: {str(e)}"
        )

@app.post("/api/chat-context", response_model=AIResponse)
async def chat_with_context(request: ContextAwareChatRequest):
    """
    Chat with context awareness. If thread_id provided, it reads thread summary 
    and provides context-aware responses.
    
    Args:
        request: Chat request with optional thread_id
        
    Returns:
        AIResponse with context-aware response
    """
    try:
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set")
            raise ValueError("API key is not configured")
        
        # Auto-generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{request.user_id}"
        
        messages = [msg.model_dump() for msg in request.messages]
        
        logger.info(f"Generating context-aware response for thread {thread_id}, user {request.user_id}")
        
        # Generate response with thread context
        response_text = await generate_context_aware_response(
            messages, 
            thread_id, 
            request.user_id
        )
        
        # Save messages to database
        if messages and db_client and db_client.is_connected():
            # Create thread if it doesn't exist
            if not db_client.get_thread_info(thread_id):
                db_client.create_thread(thread_id, request.user_id, title=f"Chat with {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            user_message = messages[-1]
            db_client.save_message(thread_id, request.user_id, user_message.get("role", "user"), user_message.get("content", ""))
            db_client.save_message(thread_id, request.user_id, "assistant", response_text)
            db_client.update_thread_message_count(thread_id)
            logger.info(f"Messages saved to thread {thread_id}")
        
        return AIResponse(response=response_text, success=True)
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating context-aware response: {str(e)}")
        return AIResponse(response="", success=False, error=f"Error: {str(e)}")

@app.get("/api/threads/{user_id}", response_model=ThreadListResponse)
async def get_user_threads(user_id: str):
    """Get all threads for a user"""
    try:
        if not db_client or not db_client.is_connected():
            raise ValueError("Database not connected")
        
        # Get all unique thread_ids for user
        threads_data = db_client.threads_collection.find({"user_id": user_id}).sort("updated_at", -1)
        
        threads = []
        for thread in threads_data:
            thread.pop("_id", None)
            threads.append(ThreadInfo(
                thread_id=thread.get("thread_id"),
                user_id=thread.get("user_id"),
                title=thread.get("title", ""),
                message_count=thread.get("message_count", 0),
                created_at=str(thread.get("created_at")) if thread.get("created_at") else None,
                updated_at=str(thread.get("updated_at")) if thread.get("updated_at") else None
            ))
        
        logger.info(f"Retrieved {len(threads)} threads for user {user_id}")
        
        return ThreadListResponse(
            threads=threads,
            total=len(threads),
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error retrieving threads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving threads: {str(e)}")

@app.delete("/api/threads/{thread_id}/{user_id}", response_model=ThreadDeleteResponse)
async def delete_thread(thread_id: str, user_id: str):
    """Delete a thread and all its messages"""
    try:
        if not db_client or not db_client.is_connected():
            raise ValueError("Database not connected")
        
        # Delete all messages in thread
        result = db_client.messages_collection.delete_many({
            "thread_id": thread_id,
            "user_id": user_id
        })
        
        # Delete thread info
        db_client.threads_collection.delete_one({
            "thread_id": thread_id,
            "user_id": user_id
        })
        
        logger.info(f"Deleted thread {thread_id} with {result.deleted_count} messages")
        
        return ThreadDeleteResponse(
            thread_id=thread_id,
            success=True,
            message=f"Thread deleted successfully. Removed {result.deleted_count} messages."
        )
    
    except Exception as e:
        logger.error(f"Error deleting thread: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting thread: {str(e)}")

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

@app.get("/api/threads/{thread_id}/{user_id}/messages")
async def get_thread_all_messages(thread_id: str, user_id: str):
    """Get all messages from a thread"""
    try:
        if not db_client or not db_client.is_connected():
            raise ValueError("Database not connected")
        
        # Get all messages from thread
        messages = db_client.get_thread_messages(thread_id, user_id, limit=100)
        
        logger.info(f"Retrieved {len(messages)} messages from thread {thread_id}")
        
        return {
            "thread_id": thread_id,
            "user_id": user_id,
            "messages": messages,
            "count": len(messages),
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error retrieving thread messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")