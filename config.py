import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.environ.get('MONGO_PUBLIC_URL', 'mongodb://mongo:tCvrFvMjzkRSNRDlWMLuDexKqVNMpgDg@metro.proxy.rlwy.net:52335')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'lipia')

# API Settings
API_KEY = os.environ.get('API_KEY', '7c8a3202ae14857e71e3a9db78cf62139772cae6')

# Service Configuration
BASE_URL = os.environ.get('BASE_URL', 'https://lipia-api.kreativelabske.com/api')
PAYMENT_URL = os.environ.get('PAYMENT_URL', 'https://lipia-online.vercel.app/link/andikartill')
CALLBACK_HOST = os.environ.get('CALLBACK_HOST', 'localhost')
CALLBACK_PORT = int(os.environ.get('CALLBACK_PORT', 8000))

# Application Settings
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
PORT = int(os.environ.get('PORT', 5000))

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'basic': {
        'amount': 20,
        'words': 100,
        'description': 'Basic Subscription - $20 for 100 words'
    },
    'premium': {
        'amount': 50,
        'words': 1000,
        'description': 'Premium Subscription - $50 for 1000 words'
    }
}
