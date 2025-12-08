# 🍳 Cooking Bot

A simple Telegram bot that helps you find recipes and chat with AI about cooking!

---

## 🎯 What Does This Bot Do?

**For Regular Users:**
1. **🤖 Cook Companion AI** - Take a photo of your ingredients → Bot suggests recipes
2. **📚 Find Recipes by List** - Browse saved recipes and leave comments
3. **💬 Ask Questions** - Chat with AI about recipes

**For Admins:**
- Add new recipes to the database
- Read user comments

---

## ⚡ Quick Start (Easiest Way - Docker)

If you have Docker installed:

```bash
docker-compose up -d
```

That's it! The bot will be running.

---

## 🚀 Manual Setup (No Docker)

### Step 1: Install Python 3.13+
Download from https://python.org

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up `.env` File
Copy `.env.example` to `.env` and fill in:

```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
WEBHOOK_URL=https://your-ngrok-url.ngrok-free.app
ADMIN_IDS=your_telegram_user_id
```

**How to get these:**
- **BOT_TOKEN**: Message @BotFather on Telegram, create a bot, get the token
- **OPENAI_API_KEY**: Go to https://platform.openai.com/api-keys, create a key
- **WEBHOOK_URL**: Use ngrok (https://ngrok.com) or your own server
- **ADMIN_IDS**: Your Telegram user ID (message @userinfobot to get it)

### Step 5: Run the Bot
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 💻 How to Use

### Start the Bot
1. Find the bot on Telegram
2. Press `/start`
3. Choose what you want to do:
   - 🤖 Send a photo → Get recipes
   - 📚 Browse saved recipes
   - ⚙️ Admin panel (if you're an admin)

### Commands
- `/start` - Open main menu
- `/help` - Get help
- `/admin` - Admin panel (admin only)

---

## 📁 Files Explained

```
bot.py           ← Main bot code (handles everything)
config.py        ← Reads your .env file
main.py          ← Web server for receiving messages
requirements.txt ← List of tools the bot needs
.env             ← Your secret keys (DO NOT SHARE)
data/            ← Where recipes are saved
  ├── receipts.json  (recipes)
  └── comments.json  (user feedback)
```

---

## 🐳 Docker (Simple Cloud Hosting)

### Build Image
```bash
docker build -t cooking-bot .
```

### Run Container
```bash
docker run -d -p 8000:8000 --env-file .env cooking-bot
```

### Using Docker Compose (Easiest)
```bash
docker-compose up -d      # Start
docker-compose logs -f    # See logs
docker-compose down       # Stop
```

---

## 🆘 Troubleshooting

**Bot doesn't respond to messages?**
- Check BOT_TOKEN is correct
- Make sure WEBHOOK_URL is accessible
- Check the bot is running: `docker-compose logs`

**Recipe generation not working?**
- Check OPENAI_API_KEY is valid
- Make sure you have API credits

**Can't find the bot on Telegram?**
- Search for the exact bot username you created

---

## 📝 Notes

- All recipes are saved in `data/receipts.json`
- All comments are saved in `data/comments.json`
- Don't share your `.env` file with anyone!
- Docker is the easiest way to deploy this
