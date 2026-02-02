import os
from supabase import create_client, Client

def init_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    # Use SERVICE_KEY as primary (Railway), fallback to KEY for local development
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise RuntimeError("Supabase configuration missing: SUPABASE_URL and either SUPABASE_SERVICE_KEY or SUPABASE_KEY must be set.")
    
    return create_client(url, key)

supabase = init_supabase()
