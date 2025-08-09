# jarvis-ai/config/settings.py

import os
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- NEW: Image Downloader Settings ---
# Create a folder named 'downloads' on your Desktop for the images
IMAGE_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "downloads")

# --- NEW: Unsplash API Keys ---
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "zce62AsAWCVrf7QTFXUKTlccdZiguiI6F1RL_mt-5Pg")
UNSPLASH_SECRET_KEY = os.getenv("UNSPLASH_SECRET_KEY", "jFWK4-FN6XW4Xf3vzhqsJUxOYo727NRw_CRbxw470ZU")


# --- Performance Settings ---
TTS_SPEED = 1.3 # Controls the playback speed of the voice (1.0 is normal, 1.3 is 30% faster)

# Path to the models directory
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Path to the data directory
DATA_DIR = os.path.join(BASE_DIR, 'data')

# --- Email Settings ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "mdsydurrahmansaeed@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "ozxt vtpd ilbo kxuf") # Use an App Password for security

# API Keys (Loaded from .env first, then fallback to hardcoded defaults)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCekw0uNXqx-4etAhabFzOHP-kOl1GCEno") # Not used for NLP, but kept for potential future use.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
# Default Groq model (e.g., for NLPProcessor) - This is required.
DEFAULT_GROQ_MODEL = os.getenv("DEFAULT_GROQ_MODEL", "llama3-8b-8192") # Using a faster Llama3 model

NASA_API_KEY = os.getenv("NASA_API_KEY", "d59lyr03QwPkgbJIANoIdAUiDngNYjsnnFb2prjj")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "EBJNR7Q5H8GB5XZZ")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "b05d9096053f46329f0d256f77f1dddb")

# Eleven Labs API Key (if you are still using it, otherwise remove)
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY", "sk_12e8dca768e7055bf1a2c56b1c2a87d2cf421b2280ecf144")

# Camb.AI Settings (if you are still using it, otherwise remove)
CAMB_AI_DEFAULT_VOICE_ID = os.getenv("CAMB_AI_DEFAULT_VOICE_ID", 20303)

# A4F TTS Settings (New - These are crucial for A4F to work)
A4F_TTS_MODEL = os.getenv("A4F_TTS_MODEL", "tts-1") # Default model from your example
A4F_TTS_VOICE = os.getenv("A4F_TTS_VOICE", "onyx") # Default voice from your example
A4F_TTS_VOICE_BN = os.getenv("A4F_TTS_VOICE_BN", "bn-BD-Standard-A") # Placeholder for Bangla voice
# If A4F requires an API key, uncomment and set this:
# A4F_API_KEY = os.getenv("A4F_API_KEY", "your_a4f_api_key_here")


# NEW: OpenWeatherMap API Key
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "d686d4a6c06e80756c79a27dc566f4f7")

# Google Custom Search API Key and CSE ID (needed for web search)
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "AIzaSyBREl33M9dhfdZqQEoSBLcrn1V28IqWzBE")
GOOGLE_CSE_CX_ID = os.getenv("GOOGLE_CSE_CX_ID", "00ac8bad843cf4217")

# NEW: Serper.dev API Key for real-time web search
SERPER_DEV_API_KEY = os.getenv("SERPER_DEV_API_KEY", "fcf5698d5d278cba11eafaa481683735f4a2736a")


# Default voice settings for TTS (These are from Eleven Labs, ensure consistency with A4F if used)
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Adam - a common, stable voice for ElevenLabs
DEFAULT_MODEL_ID = "eleven_multilingual_v2" # A common Eleven Labs model ID for TTS
DEFAULT_VOICE_RATE = 1.0
DEFAULT_VOICE_PITCH = 0.0

# Logging configuration (basic for now)
LOG_FILE = os.path.join(BASE_DIR, 'jarvis.log')
LOG_LEVEL = "INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL

# User ID (for multi-user support with Firestore later)
USER_ID = "NUHAN"

# Firestore configuration placeholders (will be populated by the environment)
FIREBASE_CONFIG = {}
INITIAL_AUTH_TOKEN = ""
APP_ID = ""