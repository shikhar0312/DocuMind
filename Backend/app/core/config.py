import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    VITE_SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
    VITE_SUPABASE_ANON_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

settings = Settings()
