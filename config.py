import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # GitHub configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    # WhatsApp configuration
    BROWSER_PATH = os.getenv('BROWSER_PATH', '')  # Optional browser path for pywhatkit
    
    # Scheduler configuration
    SCHEDULER_API_ENABLED = True