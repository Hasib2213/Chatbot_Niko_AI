from groq import Groq
from config import settings
from typing import List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Groq client initialization
try:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment")
    client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {str(e)}")
    client = None

class GroqService:
    def __init__(self):
        self.model_name = settings.MODEL
        self.client = client
        
        if not self.client:
            raise RuntimeError("Groq client is not initialized")
        
        if not self.model_name:
            raise ValueError("MODEL is not configured")
        
        logger.info(f"GroqService initialized with model: {self.model_name}")

    async def generate_response(self, messages: List[dict], user_id: str) -> str:
        try:
            if not messages:
                raise ValueError("Messages list cannot be empty")
            
            # system prompt add 
            formatted_messages = [
                {
                    "role": "system",
                    "content": settings.SYSTEM_PROMPT
                }
            ]
            
            # User messages add
            for msg in messages:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    raise ValueError("Invalid message format")
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Groq API call
            logger.info(f"Calling Groq API with {len(formatted_messages)} messages for user {user_id}")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            if not response.choices or not response.choices[0].message:
                raise ValueError("Empty response from Groq API")
            
            return response.choices[0].message.content.strip()
        
        except ValueError as e:
            logger.warning(f"Validation error for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating response for user {user_id}: {str(e)}")
            raise

# Singleton instance
try:
    groq_service = GroqService()
    logger.info("GroqService singleton created")
except Exception as e:
    logger.error(f"Failed to create GroqService: {str(e)}")
    groq_service = None

async def generate_gemini_response(messages: List[dict], user_id: str) -> str:
    if not groq_service:
        raise RuntimeError("GroqService is not available")
    return await groq_service.generate_response(messages, user_id)

async def generate_summary(messages: List[dict], thread_id: str, user_id: str) -> str:
    """
    Generate a summary of the last 10 messages in a thread.
    
    Args:
        messages: List of messages (dict with 'role' and 'content')
        thread_id: ID of the thread
        user_id: ID of the user
        
    Returns:
        Summary string
    """
    if not groq_service:
        raise RuntimeError("GroqService is not available")
    
    try:
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        # Prepare the conversation for summarization
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages[-10:]  # Last 10 messages
        ])
        
        # Create summary prompt
        summary_prompt = f"""Please provide a concise summary of the following conversation. 
The summary should be clear, accurate, and capture the main points discussed between the user and assistant.
Keep the summary to 3-5 sentences maximum.

Conversation:
{conversation_text}

Summary:"""
        
        # Prepare messages for API
        formatted_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that creates concise summaries of conversations."
            },
            {
                "role": "user",
                "content": summary_prompt
            }
        ]
        
        logger.info(f"Generating summary for thread {thread_id}, user {user_id}")
        
        # Call Groq API for summary
        response = groq_service.client.chat.completions.create(
            model=groq_service.model_name,
            messages=formatted_messages,
            temperature=0.3,  # Lower temperature for more consistent summaries
            max_tokens=300
        )
        
        if not response.choices or not response.choices[0].message:
            raise ValueError("Empty response from Groq API")
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Summary generated successfully for thread {thread_id}")
        
        return summary
        
    except ValueError as e:
        logger.warning(f"Validation error for thread {thread_id}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generating summary for thread {thread_id}: {str(e)}")
        raise