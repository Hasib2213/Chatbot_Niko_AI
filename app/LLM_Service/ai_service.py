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