"""
WSGI Entry Point for Email Extractor

This file is used by Gunicorn to run the Flask application in production.
"""

from app import create_app

# Create Flask application instance
app = create_app()

if __name__ == "__main__":
    # This section is only used when running directly (not via Gunicorn)
    # For production, use: gunicorn wsgi:app
    from config import HOST, PORT
    app.run(host=HOST, port=PORT)
