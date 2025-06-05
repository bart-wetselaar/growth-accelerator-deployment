"""
Service Recovery Actions

This module contains specific recovery actions for external services
used by the Growth Accelerator Staffing Platform.
"""

import logging
import time
import os
import json
import shutil
from datetime import datetime

from services.auto_recovery import CircuitBreaker, CircuitBreakerOpenException

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================
# Workable Service Recovery
# ============================================================

def recover_workable_service():
    """
    Recovery action for Workable API service issues
    
    Steps:
    1. Clear expired cache entries
    2. Restore from backup cache if available
    3. Reset connection parameters
    """
    logger.info("Performing Workable service recovery")
    
    # 1. Clear any expired cache entries
    cache_cleared = clear_expired_cache("cache", service="workable")
    logger.info(f"Cleared expired Workable cache entries: {cache_cleared}")
    
    # 2. Restore from backup cache if main cache is corrupted
    restored = False
    if os.path.exists("cache_backup"):
        try:
            restored = restore_from_backup_cache(service="workable")
            logger.info(f"Restored Workable cache from backup: {restored}")
        except Exception as e:
            logger.error(f"Failed to restore from backup cache: {str(e)}")
    
    # 3. Force a clean reconnection on next API call
    try:
        from services.workable_service import workable_service
        # Reset connection state if the service instance exists
        if workable_service:
            workable_service.last_api_call = None
            workable_service.api_calls_count = 0
            workable_service.rate_limit_remaining = 5  # Conservative default
            logger.info("Reset Workable service connection state")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not reset Workable service instance: {str(e)}")
    
    return {
        "cache_cleared": cache_cleared,
        "cache_restored": restored,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# LinkedIn Service Recovery
# ============================================================

def recover_linkedin_service():
    """Recovery action for LinkedIn API service issues"""
    logger.info("Performing LinkedIn service recovery")
    
    # Clear any session data that might be corrupted
    cleared = clear_expired_cache("cache", service="linkedin")
    
    # Reset the OAuth session if possible
    try:
        from controllers.linkedin import reset_oauth_session
        reset_oauth_session()
        logger.info("Reset LinkedIn OAuth session")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not reset LinkedIn OAuth session: {str(e)}")
    
    return {
        "cache_cleared": cleared,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# Squarespace Service Recovery
# ============================================================

def recover_squarespace_service():
    """Recovery action for Squarespace API service issues"""
    logger.info("Performing Squarespace service recovery")
    
    # Clear any cached Squarespace data
    cleared = clear_expired_cache("cache", service="squarespace")
    
    # Restore from backup if available
    restored = False
    if os.path.exists("cache_backup"):
        try:
            restored = restore_from_backup_cache(service="squarespace")
        except Exception as e:
            logger.error(f"Failed to restore Squarespace cache: {str(e)}")
    
    return {
        "cache_cleared": cleared,
        "cache_restored": restored,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# Wavebox Service Recovery
# ============================================================

def recover_wavebox_service():
    """Recovery action for Wavebox API service issues"""
    logger.info("Performing Wavebox service recovery")
    
    # Clear any cached Wavebox data
    cleared = clear_expired_cache("cache", service="wavebox")
    
    return {
        "cache_cleared": cleared,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# Generic Helper Functions
# ============================================================

def clear_expired_cache(cache_dir, service=None, expiration_hours=24):
    """
    Clear expired cache entries for a specific service
    
    Args:
        cache_dir (str): Directory containing cache files
        service (str, optional): Name of service to clear cache for. If None, clear all.
        expiration_hours (int): Consider files older than this many hours as expired
        
    Returns:
        int: Number of cache entries cleared
    """
    if not os.path.exists(cache_dir):
        return 0
    
    cleared_count = 0
    now = datetime.now()
    
    for filename in os.listdir(cache_dir):
        if not filename.endswith('.json'):
            continue
            
        # Check if file belongs to the specified service
        if service and not (
            filename.startswith(service.lower()) or 
            service.lower() in filename.lower()
        ):
            continue
            
        file_path = os.path.join(cache_dir, filename)
        
        # Check file age
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        age_hours = (now - file_mod_time).total_seconds() / 3600
        
        if age_hours > expiration_hours:
            try:
                os.remove(file_path)
                cleared_count += 1
                logger.debug(f"Cleared expired cache file: {filename}")
            except Exception as e:
                logger.error(f"Failed to clear cache file {filename}: {str(e)}")
    
    return cleared_count

def restore_from_backup_cache(service=None):
    """
    Restore cache files from backup
    
    Args:
        service (str, optional): Name of service to restore cache for. If None, restore all.
        
    Returns:
        bool: True if restoration was successful
    """
    if not os.path.exists("cache_backup"):
        return False
        
    # Ensure cache directory exists
    os.makedirs("cache", exist_ok=True)
    
    restored_count = 0
    
    for filename in os.listdir("cache_backup"):
        if not filename.endswith('.json'):
            continue
            
        # Check if file belongs to the specified service
        if service and not (
            filename.startswith(service.lower()) or 
            service.lower() in filename.lower()
        ):
            continue
            
        source_path = os.path.join("cache_backup", filename)
        target_path = os.path.join("cache", filename)
        
        try:
            shutil.copy2(source_path, target_path)
            restored_count += 1
            logger.debug(f"Restored cache file from backup: {filename}")
        except Exception as e:
            logger.error(f"Failed to restore cache file {filename}: {str(e)}")
    
    return restored_count > 0

def create_cache_backup(service=None):
    """
    Create backup of cache files
    
    Args:
        service (str, optional): Name of service to backup cache for. If None, backup all.
        
    Returns:
        int: Number of cache files backed up
    """
    if not os.path.exists("cache"):
        return 0
        
    # Ensure backup directory exists
    os.makedirs("cache_backup", exist_ok=True)
    
    backed_up_count = 0
    
    for filename in os.listdir("cache"):
        if not filename.endswith('.json'):
            continue
            
        # Check if file belongs to the specified service
        if service and not (
            filename.startswith(service.lower()) or 
            service.lower() in filename.lower()
        ):
            continue
            
        source_path = os.path.join("cache", filename)
        target_path = os.path.join("cache_backup", filename)
        
        try:
            shutil.copy2(source_path, target_path)
            backed_up_count += 1
            logger.debug(f"Backed up cache file: {filename}")
        except Exception as e:
            logger.error(f"Failed to backup cache file {filename}: {str(e)}")
    
    return backed_up_count

# ============================================================
# Database Recovery
# ============================================================

def recover_database_connection():
    """
    Recovery action for database connection issues
    
    Steps:
    1. Attempt to reconnect to the database
    2. Verify connection with a simple query
    3. Reset connection pool if needed
    """
    logger.info("Performing database connection recovery")
    
    try:
        from app import db
        
        # Close all sessions that might be in a bad state
        db.session.remove()
        
        # Get the engine and dispose of all connections
        engine = db.get_engine()
        engine.dispose()
        
        # Test with a simple query
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            success = result.scalar() == 1
            
        logger.info(f"Database connection recovery {'successful' if success else 'failed'}")
        return {"success": success, "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"Database recovery failed: {str(e)}")
        return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}