"""
Configuration management utilities.
"""

from backend.core.settings import settings


def get_settings():
    """
    Get the global settings instance.
    
    Returns:
        Settings: Application settings
    """
    return settings


def get_database_url() -> str:
    """
    Get the database connection URL.
    
    Returns:
        str: PostgreSQL connection URL
    """
    return settings.database_url


def get_redis_url() -> str:
    """
    Get the Redis connection URL.
    
    Returns:
        str: Redis connection URL
    """
    return settings.redis_url


def is_development() -> bool:
    """
    Check if running in development mode.
    
    Returns:
        bool: True if development mode
    """
    return settings.is_development


def is_production() -> bool:
    """
    Check if running in production mode.
    
    Returns:
        bool: True if production mode
    """
    return settings.is_production

# Made with Bob
