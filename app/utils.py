from functools import wraps
from flask import request, redirect, url_for, g
from app.supabase_client import supabase

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.cookies.get('access_token')
        if not access_token:
            return redirect(url_for('auth.login'))

        try:
            # Verify the user using the token
            user_response = supabase.auth.get_user(access_token)
            if not user_response or not user_response.user:
                 return redirect(url_for('auth.login'))
            
            g.user = user_response.user
            
            # Fetch user profile including role
            # We use the anon key in 'supabase' client, so we can only query what RLS allows.
            # RLS allows "Users can insert their own profile" and "Public profiles are viewable by everyone".
            # So we can query the profile for this user.
            
            # However, for deeper queries (like doctor seeing patients), we might need to rely on the token being passed to Supabase
            # via postgrest client headers. The 'supabase' python client initializes with the key.
            # To execute queries AS THE USER, we should update the headers of the client or create a new client with the token.
            # But creating a new client every request might be heavy?
            
            # Supabase Python client 'postgrest' allow passing `auth` token.
            # Changing the auth header for the global client is BAD because it's shared.
            # We strictly need to scope it, but the Python library might not support easy per-request scoping without re-init?
            # Actually, `supabase.auth` manages the session for the `supabase` instance? No, `supabase-py` is stateless mostly regarding the client unless using `auth.sign_in`.
            
            # Best way: Use the service role key for backend operations if we trust the backend (Admin style) OR
            # Pass the user's JWT to Supabase for RLS to work on the DB side.
            
            # Given the requirements: "Patients can only see their own data" (RLS),
            # we MUST pass the user's token to the Supabase client when making queries.
            
            # Correct approach with supabase-py:
            # client.postgrest.auth(token)
            
            # But since `supabase` global object is shared, we should probably clone it or just use the REST API header manually if needed.
            # Using `client.options(headers=...)`?
            
            # Let's attach the token to the request context 'g' and use a helper to get an authenticated client.
            g.access_token = access_token

        except Exception as e:
            print(f"Auth Error: {e}")
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function

def get_authenticated_client(token):
    # This is a bit of a hack in the python client to set auth header dynamically?
    # Or we can just use the global client and set the header immediately before query? 
    # Not thread safe.
    
    # Alternatively, create a fresh client. Low overhead in Python? 
    # Just setting headers.
    
    # We will create a fresh client instance or use the supabase.client helper if available.
    # Actually, `create_client` is cheap if we don't do complex setup.
    from config import Config
    from supabase import create_client
    
    client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    client.postgrest.auth(token)
    return client

