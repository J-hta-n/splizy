import os

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
TELEBOT_TOKEN = os.environ.get("TELEBOT_TOKEN")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")
PORT = int(os.environ.get("PORT", "8000"))
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MINIAPP_URL = os.environ.get("MINIAPP_URL", "http://localhost:3000").rstrip("/")
USE_MOCK_RECEIPT_PARSER = (
    os.environ.get("USE_MOCK_RECEIPT_PARSER", "false").lower() == "true"
)

# Receipt parser (Vision LLM)
RECEIPT_PARSER_PROVIDER = os.environ.get("RECEIPT_PARSER_PROVIDER", "gemini")
RECEIPT_PARSER_MODEL = os.environ.get("RECEIPT_PARSER_MODEL", "gemini-2.5-flash-lite")
RECEIPT_PARSER_TIMEOUT_SEC = int(os.environ.get("RECEIPT_PARSER_TIMEOUT_SEC", "45"))
RECEIPT_PARSER_MONTHLY_LIMIT = int(
    os.environ.get("RECEIPT_PARSER_MONTHLY_LIMIT", "100")
)
RECEIPT_PARSER_USAGE_FILE_PATH = os.environ.get(
    "RECEIPT_PARSER_USAGE_FILE_PATH", ".receipt_parser_usage.json"
)
GEMINI_BASE_URL = os.environ.get(
    "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"
).rstrip("/")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
