"""
Base Service Class

This module provides a base service class for all service implementations
to inherit common functionality.
"""

import logging

logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self, app=None):
        """
        Initialize the service
        
        Args:
            app: Optional Flask application instance
        """
        self.app = app
        
    def get_config(self, key, default=None):
        """
        Get a configuration value from the Flask app
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        if self.app and hasattr(self.app, 'config'):
            return self.app.config.get(key, default)
        return default