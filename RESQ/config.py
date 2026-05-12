"""
Configuration settings for RESQ application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'resq-secret-key-2024')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'resq-salt')

    # ================================
    # DATABASE CONFIG (MYSQL + SQLITE FALLBACK)
    # ================================
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL:
        # Fix for cloud MySQL providers
        if DATABASE_URL.startswith("mysql://"):
            DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Local development fallback
        SQLALCHEMY_DATABASE_URI = 'sqlite:///resq.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ================================
    # SESSION CONFIG
    # ================================
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # True in production only
    SESSION_COOKIE_HTTPONLY = True

    # ================================
    # API CONFIG
    # ================================
    RESTFUL_JSON = {'ensure_ascii': False}

    # Pagination
    ITEMS_PER_PAGE = 20

    # JWT (if you use authentication tokens)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'resq-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Secure cookies in production
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

    # In-memory DB for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# ================================
# CONFIG MAPPING
# ================================
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
