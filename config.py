import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    # Check for either key to support different hosting conventions
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

    @staticmethod
    def validate():
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise RuntimeError("CRITICAL ERROR: SUPABASE_URL or SUPABASE_KEY is not set in Environment Variables!")
