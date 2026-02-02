import os
from app import create_app

# Create the flask app instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    # Get port from environment variable, default to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 to allow external access in production
    app.run(host="0.0.0.0", port=port)
