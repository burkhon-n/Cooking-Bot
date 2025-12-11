# MUST be first - clear proxy env vars before any imports to prevent telebot/openai issues
import os
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(proxy_var, None)

from telebot.async_telebot import AsyncTeleBot
from telebot import types
import json
import tempfile
import asyncio
from config import BOT_TOKEN, OPENAI_API_KEY, DATA_DIR, ADMIN_IDS


def make_openai_client():
    """Create an OpenAI client while safely handling proxy settings.
    The OpenAI SDK (>=1.x) does not accept a `proxies` kwarg, so if a proxy is
    configured via env vars we attach it using httpx instead of passing it
    directly. This prevents the "unexpected keyword argument 'proxies'" error.
    """
    from openai import OpenAI
    # Don't use proxy for OpenAI calls - we cleared them above
    return OpenAI(api_key=OPENAI_API_KEY)

bot = AsyncTeleBot(BOT_TOKEN)

# simple in-memory state per chat
user_states = {}

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def _load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_receipts():
    ensure_data_dir()
    return _load_json(os.path.join(DATA_DIR, 'receipts.json'), [])

def add_receipt(receipt):
    ensure_data_dir()
    receipts = get_receipts()
    receipts.append(receipt)
    _save_json(os.path.join(DATA_DIR, 'receipts.json'), receipts)

def get_comments():
    ensure_data_dir()
    return _load_json(os.path.join(DATA_DIR, 'comments.json'), [])

def add_comment(comment):
    ensure_data_dir()
    comments = get_comments()
    comments.append(comment)
    _save_json(os.path.join(DATA_DIR, 'comments.json'), comments)

def get_recipe_title(recipe_text):
    """Extract title from recipe text (first line or first 50 chars)"""
    lines = recipe_text.strip().split('\n')
    # Try to find a title-like line
    for line in lines[:3]:
        line = line.strip()
        if line and not line.startswith('Yield') and not line.startswith('Prep'):
            return line[:80] if len(line) > 80 else line
    # Fallback: use first 50 chars
    return recipe_text[:50].replace('\n', ' ') + '...'


async def chat_about_recipe(user_question, recipe_context):
    """Chat with AI about a recipe with off-topic detection."""
    if not OPENAI_API_KEY:
        return "I can't access the AI assistant right now."
    
    client = make_openai_client()
    
    def _call_openai():
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful cooking assistant. You only answer questions related to cooking, recipes, ingredients, and food preparation. If the user asks about anything unrelated to cooking or food, politely redirect them to ask about the recipes. Keep responses concise and friendly."
                    },
                    {
                        "role": "user",
                        "content": f"Here are the recipes I suggested:\n\n{recipe_context}\n\nUser question: {user_question}"
                    }
                ],
                max_tokens=500,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Chat Error: {e}")
            return "Sorry, I'm having trouble responding right now. Please try again."
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _call_openai)
    return result


async def generate_recipe_from_image(image_path, chat_id=None):
    """Generate recipe text for an image using OpenAI if available.
    This function will call OpenAI synchronously inside an executor to avoid blocking.
    If OPENAI_API_KEY is not set, returns a fallback message asking for a text list.
    """
    if not OPENAI_API_KEY:
        return ("I can't access the recipe generator right now. "
                "Please send me a text list of the ingredients instead, "
                "or set `OPENAI_API_KEY` in your environment.")

    import base64
    
    client = make_openai_client()

    def _call_openai():
        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            resp = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini (gpt-5 API access may require specific tier/format)
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are a helpful cooking assistant. Analyze this image of available ingredients and identify what you see. Then provide 2-3 recipe suggestions.\n\nFormat each recipe as:\n\n*Recipe Name*\n\n*Ingredients:*\n• ingredient 1\n• ingredient 2\n\n*Instructions:*\n1. Step one\n2. Step two\n\nUse simple markdown formatting. Keep it concise and friendly. Add relevant emojis for visual appeal."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Error: {e}")  # Log to console for debugging
            return f"I'm currently unable to analyze images directly. However, I can help you create recipes based on a list of ingredients you provide! Please send me a text list of your ingredients.\n\n(Error: {e})"

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _call_openai)
    return result


def make_main_keyboard(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton('🤖 Cook companion AI'), types.KeyboardButton('📚 Find recipes by list'))
    if is_admin:
        markup.row(types.KeyboardButton('⚙️ /admin'))
    return markup


@bot.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    is_admin = message.from_user and (message.from_user.id in ADMIN_IDS)
    text = (
        "🍽️ Glad to assist you today! Choose an option:\n"
        "🤖 Cook companion AI\n"
        "📚 Find recipes by list\n\n"
        "Send /help for more info."
    )
    await bot.send_message(message.chat.id, text, reply_markup=make_main_keyboard(is_admin))


@bot.message_handler(commands=['help'])
async def help_handler(message: types.Message):
    help_text = (
        "🍳 *Welcome to Cooking Bot!*\n\n"
        "Use the bot to get recipe suggestions from a photo or from saved recipes.\n\n"
        "🤖 *Cook companion AI* - Send a photo of your available ingredients.\n"
        "📚 *Find recipes by list* - Browse saved recipes from the database.\n\n"
        "⚙️ Admins can use /admin to add recipes or review comments."
    )
    await bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['admin'])
async def admin_handler(message: types.Message):
    if not message.from_user or message.from_user.id not in ADMIN_IDS:
        await bot.send_message(message.chat.id, "You are not authorized to use admin commands.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Add recipe', callback_data='admin_add'))
    markup.add(types.InlineKeyboardButton('💬 Review comments', callback_data='admin_review'))
    await bot.send_message(message.chat.id, '⚙️ Admin panel:', reply_markup=markup)


@bot.callback_query_handler(func=lambda c: True)
async def callback_query(call: types.CallbackQuery):
    data = call.data
    uid = call.from_user.id
    if data == 'admin_add':
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.message.chat.id, '📝 First, send the recipe *title*:', parse_mode='Markdown')
        user_states[uid] = {'state': 'awaiting_recipe_title'}
    elif data == 'admin_review':
        await bot.answer_callback_query(call.id)
        comments = get_comments()
        if not comments:
            await bot.send_message(call.message.chat.id, 'No comments yet.')
            return
        text = 'Comments:\n' + '\n---\n'.join([f"{c.get('user','unknown')}: {c.get('text','')}" for c in comments])
        await bot.send_message(call.message.chat.id, text)
    elif data.startswith('recipe_'):
        await bot.answer_callback_query(call.id)
        try:
            recipe_idx = int(data.split('_')[1])
            receipts = get_receipts()
            if 0 <= recipe_idx < len(receipts):
                recipe = receipts[recipe_idx]
                recipe_text = recipe.get('text', '')
                title = recipe.get('title') or get_recipe_title(recipe_text)
                
                # Format and send recipe
                formatted = f"*{title}*\n\n{recipe_text}"
                
                # Split if too long
                if len(formatted) > 4000:
                    parts = []
                    current = ""
                    for line in formatted.split('\n'):
                        if len(current) + len(line) + 1 > 4000:
                            parts.append(current)
                            current = line + '\n'
                        else:
                            current += line + '\n'
                    if current:
                        parts.append(current)
                    
                    for part in parts:
                        await bot.send_message(call.message.chat.id, part, parse_mode='Markdown')
                else:
                    await bot.send_message(call.message.chat.id, formatted, parse_mode='Markdown')
                
                # Add show comments button
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('📝 Show Comments', callback_data=f'show_comments_{recipe_idx}'))
                
                await bot.send_message(call.message.chat.id, '💬 Please leave your feedback or comment about this recipe:', reply_markup=markup)
                user_states[uid] = {'state': 'awaiting_recipe_comment', 'recipe_idx': recipe_idx}
        except Exception as e:
            await bot.send_message(call.message.chat.id, f'Error loading recipe: {e}')
    elif data.startswith('show_comments_'):
        await bot.answer_callback_query(call.id)
        try:
            recipe_idx = int(data.split('_')[2])
            comments = get_comments()
            receipts = get_receipts()
            
            if 0 <= recipe_idx < len(receipts):
                recipe = receipts[recipe_idx]
                title = recipe.get('title') or get_recipe_title(recipe.get('text', ''))
                
                # Filter comments for this specific recipe
                recipe_comments = [c for c in comments if c.get('recipe_idx') == recipe_idx]
                
                if not recipe_comments:
                    await bot.send_message(call.message.chat.id, f'📝 *Comments for {title}*\n\nNo comments yet. Be the first to leave feedback!', parse_mode='Markdown')
                else:
                    comment_text = f'📝 *Comments for {title}*\n\n'
                    for i, c in enumerate(recipe_comments, 1):
                        user = c.get('user', 'Anonymous')
                        text = c.get('text', '')
                        comment_text += f"{i}. *{user}*: {text}\n\n"
                    
                    await bot.send_message(call.message.chat.id, comment_text, parse_mode='Markdown')
        except Exception as e:
            await bot.send_message(call.message.chat.id, f'Error loading comments: {e}')
    else:
        await bot.answer_callback_query(call.id)


@bot.message_handler(content_types=['text'])
async def text_handler(message: types.Message):
    uid = message.from_user.id if message.from_user else message.chat.id
    txt = message.text.strip()

    # admin: saving new recipe
    st = user_states.get(uid)
    if st and st.get('state') == 'awaiting_recipe_title':
        user_states[uid] = {'state': 'awaiting_recipe_text', 'title': txt}
        await bot.send_message(message.chat.id, f'✅ Title: *{txt}*\n\nNow send the full recipe text (ingredients and instructions):', parse_mode='Markdown')
        return
    
    if st and st.get('state') == 'awaiting_recipe_text':
        title = st.get('title', 'Untitled Recipe')
        receipt = {'added_by': uid, 'title': title, 'text': txt}
        add_receipt(receipt)
        await bot.send_message(message.chat.id, f'Recipe "*{title}*" saved successfully! ✅', reply_markup=make_main_keyboard(uid in ADMIN_IDS), parse_mode='Markdown')
        user_states.pop(uid, None)
        return

    if txt == '🤖 Cook companion AI' or txt == 'Cook companion AI':
        user_states[uid] = {'state': 'awaiting_ingredients_photo'}
        await bot.send_message(message.chat.id, 'Glad to assist you today. Send me a photo of available ingredients and I will provide possible recipes.')
        return

    if txt == '📚 Find recipes by list' or txt == 'Find recipes by list':
        receipts = get_receipts()
        if not receipts:
            await bot.send_message(message.chat.id, 'No recipes available yet.')
            return
        
        # Create inline keyboard with recipe titles
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, r in enumerate(receipts):
            recipe_text = r.get('text', '')
            title = r.get('title') or get_recipe_title(recipe_text)
            button = types.InlineKeyboardButton(
                f"📖 {title}",
                callback_data=f"recipe_{i}"
            )
            markup.add(button)
        
        await bot.send_message(
            message.chat.id, 
            '📚 *Available Recipes*\n\nSelect a recipe to view details:', 
            reply_markup=markup,
            parse_mode='Markdown'
        )
        user_states[uid] = {'state': 'browsing_recipes'}
        return

    if txt == '🏠 Back to Home':
        is_admin = message.from_user and (message.from_user.id in ADMIN_IDS)
        user_states.pop(uid, None)
        await bot.send_message(message.chat.id, '🏠 Welcome back! Choose an option:', reply_markup=make_main_keyboard(is_admin))
        return

    # AI chat about recipe
    if st and st.get('state') == 'chatting_about_recipe':
        recipe_context = st.get('recipe_context', '')
        response = await chat_about_recipe(txt, recipe_context)
        
        # Format the response properly
        formatted_response = response.replace('###', '🍳').replace('**', '*')
        
        # Create keyboard with home button
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('🏠 Back to Home'))
        
        await bot.send_message(message.chat.id, formatted_response, parse_mode='Markdown', reply_markup=markup)
        return
    
    # comments flow
    if st and st.get('state') == 'awaiting_recipe_comment':
        # Get user display name with fallbacks
        if message.from_user:
            if message.from_user.username:
                username = message.from_user.username
            elif message.from_user.first_name:
                username = message.from_user.first_name
                if message.from_user.last_name:
                    username += f" {message.from_user.last_name}"
            else:
                username = f"User {uid}"
        else:
            username = f"User {uid}"
        
        recipe_idx = st.get('recipe_idx')
        comment = {'user': username, 'user_id': uid, 'text': txt, 'recipe_idx': recipe_idx}
        add_comment(comment)
        await bot.send_message(message.chat.id, 'Thank you for your comment! 🙏\n\n🏠 Returning to Home...', reply_markup=make_main_keyboard(uid in ADMIN_IDS))
        user_states.pop(uid, None)
        return
    
    # Handle comment after browsing recipes (general comment, not linked to specific recipe)
    if st and st.get('state') == 'browsing_recipes':
        # Get user display name with fallbacks
        if message.from_user:
            if message.from_user.username:
                username = message.from_user.username
            elif message.from_user.first_name:
                username = message.from_user.first_name
                if message.from_user.last_name:
                    username += f" {message.from_user.last_name}"
            else:
                username = f"User {uid}"
        else:
            username = f"User {uid}"
        
        comment = {'user': username, 'user_id': uid, 'text': txt, 'recipe_idx': None}
        add_comment(comment)
        await bot.send_message(message.chat.id, 'Thank you for your feedback! 🙏\n\n🏠 Returning to Home...', reply_markup=make_main_keyboard(uid in ADMIN_IDS))
        user_states.pop(uid, None)
        return

    # Handle text ingredients list when awaiting_ingredients_photo
    if st and st.get('state') == 'awaiting_ingredients_photo':
        # User sent text description of ingredients instead of photo
        ingredients_text = txt
        await bot.send_message(message.chat.id, '🔍 Processing your ingredients... this may take a few seconds.')
        
        # Call OpenAI to generate recipes from text description
        if not OPENAI_API_KEY:
            await bot.send_message(message.chat.id, "I can't access the AI assistant right now.")
            return
        
        client = make_openai_client()
        
        def _generate_from_text():
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful cooking assistant. Generate creative and delicious recipes based on the ingredients provided. Provide clear, step-by-step instructions. Format recipes with clear headers."
                        },
                        {
                            "role": "user",
                            "content": f"Based on these available ingredients, suggest 2-3 creative recipes I can make:\n\n{ingredients_text}\n\nPlease provide detailed recipes with ingredients and instructions."
                        }
                    ],
                    max_tokens=1000,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI Error: {e}")
                return "Sorry, I'm having trouble generating recipes right now. Please try again."
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _generate_from_text)
        
        # Format the response for better readability in Telegram
        formatted_result = result.replace('###', '🍳').replace('**', '*')
        
        # Split long messages if needed (Telegram has 4096 character limit)
        if len(formatted_result) > 4000:
            parts = []
            current_part = ""
            for line in formatted_result.split('\n'):
                if len(current_part) + len(line) + 1 > 4000:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            if current_part:
                parts.append(current_part)
            
            for part in parts:
                await bot.send_message(message.chat.id, part, parse_mode='Markdown')
        else:
            await bot.send_message(message.chat.id, formatted_result, parse_mode='Markdown')
        
        # Create keyboard with home button
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('🏠 Back to Home'))
        
        await bot.send_message(message.chat.id, '💬 Ask me anything about these recipes! (cooking tips, substitutions, variations, etc.)', reply_markup=markup)
        user_states[uid] = {'state': 'chatting_about_recipe', 'recipe_context': result}
        return

    # fallback
    await bot.send_message(message.chat.id, "I didn't understand that. Send /help for available commands.", reply_markup=make_main_keyboard(uid in ADMIN_IDS))


@bot.message_handler(content_types=['photo'])
async def photo_handler(message: types.Message):
    uid = message.from_user.id if message.from_user else message.chat.id
    st = user_states.get(uid)
    if not st or st.get('state') != 'awaiting_ingredients_photo':
        await bot.send_message(message.chat.id, "If you'd like a recipe from a photo, first choose 'Cook companion AI' from the menu.")
        return

    # get best quality photo
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    fp = await bot.download_file(file_path)

    # save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        tmp.write(fp)
        tmp_path = tmp.name

    await bot.send_message(message.chat.id, '🔍 Processing your photo... this may take a few seconds.')
    result = await generate_recipe_from_image(tmp_path, chat_id=uid)
    
    # Format the response for better readability in Telegram
    formatted_result = result.replace('###', '🍳').replace('**', '*')
    
    # Split long messages if needed (Telegram has 4096 character limit)
    if len(formatted_result) > 4000:
        parts = []
        current_part = ""
        for line in formatted_result.split('\n'):
            if len(current_part) + len(line) + 1 > 4000:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        if current_part:
            parts.append(current_part)
        
        for part in parts:
            await bot.send_message(message.chat.id, part, parse_mode='Markdown')
    else:
        await bot.send_message(message.chat.id, formatted_result, parse_mode='Markdown')
    
    # Create keyboard with home button
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🏠 Back to Home'))
    
    await bot.send_message(message.chat.id, '💬 Ask me anything about these recipes! (cooking tips, substitutions, variations, etc.)', reply_markup=markup)
    user_states[uid] = {'state': 'chatting_about_recipe', 'recipe_context': result}
