from supabase import create_client, Client
from config import Config

def init_supabase() -> Client:
    url: str = Config.SUPABASE_URL
    key: str = Config.SUPABASE_KEY
    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in .env")
    return create_client(url, key)

supabase = init_supabase()
