import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing credentials")
    exit(1)

supabase: Client = create_client(url, key)

# Unique email for testing
test_email = f"test_user_{int(time.time())}@example.com"
test_password = "TestPassword123!"

print(f"--- Testing Authentication Flow ---")
print(f"Target: {test_email}")

# 1. Try to Register
print("\n[1] Attempting Registration...")
try:
    auth_response = supabase.auth.sign_up({
        "email": test_email,
        "password": test_password
    })
    
    user = auth_response.user
    session = auth_response.session
    
    if user:
        print(f"✅ Registration Successful! User ID: {user.id}")
        if session:
            print("✅ Session received immediately (Email Confirmation is likely OFF or Auto-Confirm ON).")
        else:
            print("⚠️  No session received. **Email Confirmation is likely ON**.")
            print("   You MUST click the link in the email or disable 'Confirm Email' in Supabase Dashboard.")
    else:
        print("❌ Registration returned no user.")

except Exception as e:
    print(f"❌ Registration Failed with Exception: {e}")

# 2. Try to Login (Only if registration didn't throw)
print("\n[2] Attempting Login...")
try:
    login_response = supabase.auth.sign_in_with_password({
        "email": test_email,
        "password": test_password
    })
    
    if login_response.session:
        print("✅ Login Successful! Token received.")
    else:
        print("❌ Login returned no session.")

except Exception as e:
    print(f"❌ Login Failed: {e}")
    if "Invalid login credentials" in str(e):
        print("\n>>> DIAGNOSIS: This error usually means the user is NOT CONFIRMED yet.")
