import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
