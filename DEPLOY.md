# 🚀 Render Deployment Checklist

## Before You Deploy

- [ ] Push code to GitHub
- [ ] Create Render account at https://render.com
- [ ] Have your Telegram bot token ready (from @BotFather)
- [ ] Have your OpenAI API key ready (from https://platform.openai.com/api-keys)
- [ ] Know your Telegram user ID (message @userinfobot)

## Deployment Steps

1. **Create Web Service on Render**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the cooking-bot repo

2. **Configure Service**
   - **Name**: `cooking-bot` (or your preferred name)
   - **Environment**: Python 3
   - **Region**: Oregon (or closest to you)
   - **Branch**: main
   - **Build Command**: `bash setup.sh`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

3. **Add Environment Variables**
   Click "Advanced" → "Add Environment Variable" for each:
   
   | Key | Value | Where to get it |
   |-----|-------|-----------------|
   | `BOT_TOKEN` | Your bot token | Message @BotFather on Telegram |
   | `OPENAI_API_KEY` | Your OpenAI key | https://platform.openai.com/api-keys |
   | `WEBHOOK_URL` | `https://YOUR-APP-NAME.onrender.com` | Render gives you this after creation |
   | `ADMIN_IDS` | Your Telegram user ID | Message @userinfobot |
   | `DATA_DIR` | `/opt/render/project/src/data` | Default location |

4. **Deploy**
   - Click "Create Web Service"
   - Wait 2-3 minutes for deployment
   - Check logs for "✅ Webhook set successfully"

5. **Update Webhook URL**
   - After deployment, you'll get a URL like `https://cooking-bot-abc123.onrender.com`
   - Go back to Environment Variables
   - Update `WEBHOOK_URL` to your actual Render URL
   - Save (this will trigger a redeploy)

6. **Test Your Bot**
   - Find your bot on Telegram
   - Send `/start`
   - Try sending a photo or text ingredients

## Important Notes

⚠️ **Free Plan Limitations**:
- Service spins down after 15 min of inactivity
- First request after sleep takes ~30 seconds to wake up
- 750 hours/month free (enough for one service running 24/7)

💾 **Data Persistence**:
- Render free plan has persistent disk (unlike Vercel)
- Your recipes and comments will be saved
- Data persists across deploys in `/opt/render/project/src/data`

🔄 **Auto-Deploy**:
- Every git push to main triggers a new deployment
- Can disable in Render settings if needed

## Troubleshooting

**Bot not responding?**
- Check Render logs for errors
- Verify all environment variables are set correctly
- Make sure WEBHOOK_URL matches your Render URL exactly

**"Webhook setup failed"?**
- Wait 1 minute and check logs again (retry logic kicks in)
- Verify BOT_TOKEN is correct
- Check if Telegram is rate-limiting (wait a few minutes)

**OpenAI not working?**
- Verify OPENAI_API_KEY is correct
- Check you have API credits at https://platform.openai.com/usage

**Service keeps sleeping?**
- This is normal on free plan
- Upgrade to paid plan ($7/mo) for always-on
- Or set up a ping service to keep it awake

## Next Steps

Once deployed:
1. Share your bot with friends!
2. Monitor usage in Render dashboard
3. Add more recipes via `/admin`
4. Check OpenAI usage to stay within budget

Need help? Check the main README.md for more details.
