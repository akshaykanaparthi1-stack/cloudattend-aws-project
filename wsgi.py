import os
from app import create_app

# Gunicorn entrypoint
app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run()
