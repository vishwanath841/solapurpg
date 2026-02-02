import os
from supabase import create_client, Client

def init_supabase() -> Client:
    """
    Initialize Supabase client using environment variables.
    Works for both local development and Railway production.
    """
    url = os.environ.get("SUPABASE_URL")
    # SUPABASE_SERVICE_KEY is used for backend operations on Railway
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        # Clear error message without mentioning .env files
        raise RuntimeError("Supabase configuration missing: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in Environment Variables.")
    
    return create_client(url, key)

# Initialize global supabase client
supabase = init_supabase()
