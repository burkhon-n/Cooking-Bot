# Cooking Bot

A Telegram bot that helps users find recipes using AI or browse a recipe database.

## Features

### User Features
- **Cook Companion AI**: Upload a photo of available ingredients and get AI-generated recipe suggestions
- **Find Recipes by List**: Browse saved recipes from the database
- **Comment/Feedback**: Leave comments on recipes

### Admin Features
- **Add Recipes**: Add new recipes to the database
- **Review Comments**: View all user comments and feedback

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Your `.env` file is already configured with:
- `BOT_TOKEN` - Telegram bot token
- `OPENAI_API_KEY` - OpenAI API key for recipe generation
- `WEBHOOK_URL` - Your ngrok or public URL for webhooks
- `ADMIN_ID` - Your Telegram user ID (6302307151)

### 3. Run the Bot

The bot uses JSON files (`data/receipts.json` and `data/comments.json`) for storage.

#### Using Webhook (Production)
Make sure your `WEBHOOK_URL` is accessible (e.g., via ngrok):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Using Polling (Local Development)
Create a file `polling_runner.py`:

```python
from bot import bot
import asyncio

async def poll():
    await bot.delete_webhook()
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(poll())
```

Then run:
```bash
python3 polling_runner.py
```

## Usage

### User Commands
- `/start` - Start the bot and see main menu
- `/help` - Get help information

### Admin Commands
- `/admin` - Access admin panel (only for user ID: 6302307151)

## Project Structure

```
.
├── bot.py              # Main bot logic and handlers
├── config.py           # Configuration from environment variables
├── main.py             # FastAPI webhook server
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in git)
└── data/              # JSON storage
    ├── receipts.json
    └── comments.json
```

## Notes

- The bot uses JSON file storage in the `data/` folder
- OpenAI recipe generation requires a valid API key
- Admin access is restricted to the user ID specified in `ADMIN_ID`
