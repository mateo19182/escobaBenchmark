import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Read the API key and default model from the environment, or fall back to defaults.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "default_openrouter_api_key")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "google/gemini-2.0-flash-001") 