import os
from dotenv import load_dotenv
from app.prompts.system_prompt import SYSTEM_PROMPT


load_dotenv()

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    MODEL = os.getenv("MODEL", "llama-3.3-70b-versatile")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    
    # System prompt from system_prompt.py file
    SYSTEM_PROMPT = SYSTEM_PROMPT

settings = Settings()