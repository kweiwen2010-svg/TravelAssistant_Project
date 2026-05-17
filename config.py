import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    GEMINI_MODEL = "gemini-1.5-flash" # 使用穩定版本