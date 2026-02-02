import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
# Partially hide key for security in logs
print(f"KEY: {key[:5]}...{key[-5:] if key else 'None'}")

if not url or not key:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY is missing in .env")
    exit(1)

try:
    print("Attempting to connect to Supabase...")
    supabase: Client = create_client(url, key)
    
    # Try a simple read (even if empty, it tests connection)
    # We'll try to read from 'profiles' or just get health
    # Actually, let's try to sign in with a fake user to see if Auth endpoint is reachable
    # OR just query a public table.
    
    print("Connection object created.")
    
    # Test Table Access
    try:
        response = supabase.table('profiles').select("count", count="exact").execute()
        print(f"✅ Connection Successful! Accessed 'profiles' table. Count: {response.count}")
    except Exception as table_error:
        print(f"⚠️  Connected, but table access failed: {table_error}")
        print("This might be due to RLS policies or the table not existing yet.")

    print("\nCheck your Supabase Dashboard:")
    print(f"1. Go to {url}")
    print("2. Look at 'Authentication' > 'Users' to see registered users.")
    print("3. Look at 'Table Editor' > 'profiles' (if you inserted data there).")

except Exception as e:
    print(f"❌ Connection Failed: {e}")
