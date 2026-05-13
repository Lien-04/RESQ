"""
Configuration settings for RESQ application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'resq-secret-key-2024')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'resq-salt')

    # ============================
    # DATABASE (CLOUD + LOCAL SAFE)
    # ============================
    DATABASE_URL = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('MYSQL_URL')
        or os.environ.get('CLEARDB_DATABASE_URL')
    )

    # Fix Railway / cloud MySQL format issue
    if DATABASE_URL:
        if DATABASE_URL.startswith("mysql://"):
            DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///resq.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ============================
    # SESSION CONFIG
    # ============================
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # True only in HTTPS production
    SESSION_COOKIE_HTTPONLY = True

    # ============================
    # API CONFIG
    # ============================
    RESTFUL_JSON = {'ensure_ascii': False}

    # Pagination
    ITEMS_PER_PAGE = 20

    # ============================
    # JWT CONFIG
    # ============================
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'resq-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS only


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}