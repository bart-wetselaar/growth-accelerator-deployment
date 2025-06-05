"""
Circuit Breaker Setup

This module initializes and configures circuit breakers for external API services.
"""

import logging
from services.auto_recovery import AutoRecovery, CircuitBreaker
from services.service_recovery import (
    recover_workable_service,
    recover_linkedin_service,
    recover_squarespace_service,
    recover_wavebox_service,
    recover_database_connection
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize auto recovery service
auto_recovery = AutoRecovery()

# Declare circuit breakers at module level so they can be imported directly
workable_circuit = None
linkedin_circuit = None
squarespace_circuit = None
wavebox_circuit = None

def init_circuit_breakers(app):
    """
    Initialize circuit breakers for all external services
    
    Args:
        app: Flask application instance
    """
    # We need to modify module-level variables
    global workable_circuit, linkedin_circuit, squarespace_circuit, wavebox_circuit
    
    logger.info("Initializing circuit breakers for external services")
    
    # Initialize auto recovery with the Flask app
    auto_recovery.init_app(app)
    
    # Create circuit breakers for each service
    workable_circuit = auto_recovery.create_circuit_breaker(
        name="workable_api",
        failure_threshold=3,
        recovery_timeout=60,
        half_open_max_calls=1,
        exception_types=[Exception]  # Consider narrowing this down to specific exceptions
    )
    
    linkedin_circuit = auto_recovery.create_circuit_breaker(
        name="linkedin_api",
        failure_threshold=3,
        recovery_timeout=120,
        half_open_max_calls=1
    )
    
    squarespace_circuit = auto_recovery.create_circuit_breaker(
        name="squarespace_api",
        failure_threshold=3,
        recovery_timeout=60,
        half_open_max_calls=1
    )
    
    wavebox_circuit = auto_recovery.create_circuit_breaker(
        name="wavebox_api",
        failure_threshold=3,
        recovery_timeout=60,
        half_open_max_calls=1
    )
    
    # Register recovery actions
    auto_recovery.register_recovery_action("workable_api", recover_workable_service)
    auto_recovery.register_recovery_action("linkedin_api", recover_linkedin_service)
    auto_recovery.register_recovery_action("squarespace_api", recover_squarespace_service)
    auto_recovery.register_recovery_action("wavebox_api", recover_wavebox_service)
    auto_recovery.register_recovery_action("database", recover_database_connection)
    
    logger.info("Circuit breakers initialized and registered")
    
    return {
        "workable_circuit": workable_circuit,
        "linkedin_circuit": linkedin_circuit,
        "squarespace_circuit": squarespace_circuit,
        "wavebox_circuit": wavebox_circuit
    }