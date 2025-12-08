from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATA_DIR = os.getenv("DATA_DIR", "./data")

# Admin user ID (supports ADMIN_ID for single admin or ADMIN_IDS for comma-separated)
ADMIN_IDS = []
_admin_id = os.getenv("ADMIN_ID")
if _admin_id:
	try:
		ADMIN_IDS = [int(_admin_id.strip())]
	except Exception:
		pass
# fallback to ADMIN_IDS if ADMIN_ID not set
if not ADMIN_IDS:
	_admin_env = os.getenv("ADMIN_IDS")
	if _admin_env:
		try:
			ADMIN_IDS = [int(x.strip()) for x in _admin_env.split(",") if x.strip()]
		except Exception:
			ADMIN_IDS = []