import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# MongoDB settings
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')

# API Settings
DEBUG = os.getenv('DEBUG').lower()
API_HOST = os.getenv('API_HOST')
API_PORT = int(os.getenv('API_PORT')) 