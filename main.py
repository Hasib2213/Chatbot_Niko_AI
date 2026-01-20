from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.LLM_Service.ai_service import generate_gemini_response, generate_summary, generate_context_aware_response
from app.schema.schema import (
    AIRequest, AIResponse, SummaryRequest, SummaryResponse,
    ContextAwareChatRequest, ThreadListResponse, ThreadDeleteResponse, ThreadInfo,
    ThreadMessagesRequest
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import db_client
from config import settings
import logging
from datetime import datetime
import asyncio
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI assistant")

app.add_middleware(
   CORSMiddleware,
  allow_origins=["*"],  # Configure appropriately for production
  allow_credentials=True,
    allow_methods=["*"],
   allow_headers=["*"],
)


async def auto_generate_summary(thread_id: str, user_id: str):
    """Auto-generate summary when thread has 10+ messages (counting pairs)"""
    try:
        if not db_client or not db_client.is_connected():
            return
        
        # Get current message count
        message_count = db_client.messages_collection.count_documents({"thread_id": thread_id})
        
        # Get thread info to check if summary already exists
        thread_info = db_client.get_thread_info(thread_id)
        has_summary = thread_info.get("summary") if thread_info else None
        
        # Generate summary every 10 messages (if not already generated)
        if message_count >= 10 and message_count % 10 == 0 and not has_summary:
            logger.info(f"Auto-generating summary for thread {thread_id} at {message_count} messages")
            try:
                summary_text = await generate_summary(thread_id, user_id)
                if summary_text:
                    db_client.save_thread_summary(thread_id, summary_text)
                    logger.info(f"Auto-summary generated and saved for thread {thread_id}")
            except Exception as e:
                logger.error(f"Error auto-generating summary: {str(e)}")
    except Exception as e:
        logger.error(f"Error in auto_generate_summary: {str(e)}")


@app.post("/api/chat", response_model=AIResponse)
async def generate(request: AIRequest):
    try:
        # Validate API key
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set")
            raise ValueError("API key is not configured")
        
        messages = [msg.model_dump() for msg in request.messages]
        
        # Generate unique thread_id for each new conversation
        thread_id = str(uuid.uuid4())
        
        logger.info(f"Generating response for user {request.user_id} with thread {thread_id}")
        
        # Save user message to database
        if messages and db_client and db_client.is_connected():
            user_message = messages[-1]  # Last message from user
            
            # Create thread if it doesn't exist
            if not db_client.get_thread_info(thread_id):
                # Generate title from message content (first 50 chars)
                msg_content = user_message.get("content", "")
                title = msg_content[:50] + "..." if len(msg_content) > 50 else msg_content
                db_client.create_thread(thread_id, request.user_id, title=title)
            
            db_client.save_message(thread_id, request.user_id, user_message.get("role", "user"), user_message.get("content", ""))
            
            # Use context-aware response to preserve conversation history
            response_text = await generate_context_aware_response(messages, thread_id, request.user_id)
            
            db_client.save_message(thread_id, request.user_id, "assistant", response_text)
            db_client.update_thread_message_count(thread_id)
            logger.info(f"Messages saved to database for thread {thread_id}")
            
            # Auto-generate summary in background (non-blocking)
            asyncio.create_task(auto_generate_summary(thread_id, request.user_id))
            
            return AIResponse(response=response_text, success=True, thread_id=thread_id)
        else:
            # Fallback if no database - use basic response
            response_text = await generate_gemini_response(messages, request.user_id)
            return AIResponse(response=response_text, success=True, thread_id=thread_id)
        
        return AIResponse(response=response_text, success=True)
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
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
            
        }
    
    except Exception as e:
        logger.error(f"Error retrieving thread messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/threads/{thread_id}/{user_id}/messages")
async def thread_messages_combined(
    thread_id: str, 
    user_id: str,
    request: ThreadMessagesRequest
):
    """
    Combined endpoint for GET/CHAT operations:
    - If 'messages' provided: Chat mode (generate response + save to thread + use summary context)
    - If 'messages' NOT provided: Fetch mode (retrieve messages + summary from thread)
    """
    try:
        if not db_client or not db_client.is_connected():
            raise ValueError("Database not connected")
        
        # CHAT MODE: If messages provided
        if request.messages and len(request.messages) > 0:
            if not settings.GROQ_API_KEY:
                logger.error("GROQ_API_KEY is not set")
                raise ValueError("API key is not configured")
            
            messages_list = [msg.model_dump() for msg in request.messages]
            
            logger.info(f"Chat mode: Generating context-aware response for thread {thread_id}, user {user_id}")
            
            # Generate response with thread context (uses stored summary)
            response_text = await generate_context_aware_response(
                messages_list, 
                thread_id, 
                user_id
            )
            
            # Save messages to database
            if db_client and db_client.is_connected():
                # Create thread if it doesn't exist
                if not db_client.get_thread_info(thread_id):
                    msg_content = messages_list[-1].get("content", "")
                    title = msg_content[:50] + "..." if len(msg_content) > 50 else msg_content
                    db_client.create_thread(thread_id, user_id, title=title)
                
                user_message = messages_list[-1]
                db_client.save_message(thread_id, user_id, user_message.get("role", "user"), user_message.get("content", ""))
                db_client.save_message(thread_id, user_id, "assistant", response_text)
                db_client.update_thread_message_count(thread_id)
                logger.info(f"Messages saved to thread {thread_id}")
                
                # Auto-generate summary in background
                asyncio.create_task(auto_generate_summary(thread_id, user_id))
            
            # Get updated summary
            thread_info = db_client.get_thread_info(thread_id)
            thread_summary = thread_info.get("summary") if thread_info else None
            
            return {
                "thread_id": thread_id,
                "user_id": user_id,
                "response": response_text,
               
            }
        
        # FETCH MODE: If messages NOT provided
        else:
            logger.info(f"Fetch mode: Retrieving messages from thread {thread_id}, user {user_id}")
            
          
            
            # Get messages from thread
            messages_list = db_client.get_thread_messages(thread_id, user_id)
            
            # Get thread summary for context
            thread_summary = None
            thread_info = db_client.get_thread_info(thread_id)
            if thread_info:
                thread_summary = thread_info.get("summary")
            
            logger.info(f"Retrieved {len(messages_list)} messages from thread {thread_id}")
            
            return {
                "thread_id": thread_id,
                "user_id": user_id,
                "messages": messages_list,
                "count": len(messages_list),
                
            }
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in thread_messages_combined: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    