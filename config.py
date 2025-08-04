import os

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
TELEBOT_TOKEN = os.environ.get("TELEBOT_TOKEN")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")
PORT = int(os.environ.get("PORT", "8000"))
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
