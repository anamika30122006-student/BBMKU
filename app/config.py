import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bbmku-ufms-default-secure-key-2026'
    
    # Database configuration
    # Default to local PostgreSQL if available, otherwise fallback gracefully
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{BASE_DIR / 'instance' / 'bbmku_ufms.db'}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Uploads configuration
    UPLOAD_FOLDER = BASE_DIR / os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 32 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'}

    # SLA and Delay Thresholds (in days)
    SLA_DELAY_WARNING_DAYS = int(os.environ.get('SLA_DELAY_WARNING_DAYS', 3))
    SLA_DELAY_CRITICAL_DAYS = int(os.environ.get('SLA_DELAY_CRITICAL_DAYS', 7))
    SLA_DELAY_OVERDUE_DAYS = int(os.environ.get('SLA_DELAY_OVERDUE_DAYS', 15))

    # University Branding & Identity
    UNIVERSITY_NAME = os.environ.get('UNIVERSITY_NAME', 'Binod Bihari Mahto Koyalanchal University (BBMKU)')
    UNIVERSITY_LOCATION = os.environ.get('UNIVERSITY_LOCATION', 'Dhanbad, Jharkhand, India')
    UNIVERSITY_CODE = os.environ.get('UNIVERSITY_CODE', 'BBMKU')

    # Security Headers & Cookies
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400 * 7 # 7 days


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration using SQLite in-memory or file."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = BASE_DIR / 'tests' / 'test_uploads'


class ProductionConfig(Config):
    """Production environment configuration with strict security."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
