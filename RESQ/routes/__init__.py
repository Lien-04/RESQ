"""
Routes package initialization
"""
from .auth import auth_bp
from .incidents import incidents_bp
from .admin import admin_bp

__all__ = ['auth_bp', 'incidents_bp', 'admin_bp']
