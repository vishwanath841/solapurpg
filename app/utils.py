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
            g.access_token = access_token
            # Specifically extract role for easy access in views and role_required
            g.user_role = user_response.user.user_metadata.get('role', 'patient')

        except Exception as e:
            print(f"Auth Error: {e}")
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # login_required should be called before role_required
            if not hasattr(g, 'user_role') or g.user_role != required_role:
                # Redirect to appropriate dashboard if role mismatch
                if g.user_role == 'doctor':
                    return redirect(url_for('doctor.dashboard'))
                return redirect(url_for('patient.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_authenticated_client(token):
    import os
    from supabase import create_client
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print(f"DEBUG: Missing Supabase config in get_authenticated_client. URL: {bool(url)}, Key: {bool(key)}")
        raise RuntimeError("Supabase configuration missing in get_authenticated_client")
        
    client = create_client(url, key)
    client.postgrest.auth(token)
    return client

