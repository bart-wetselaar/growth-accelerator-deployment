"""
Services package for Growth Accelerator Staffing Platform
"""

def init_services(app):
    """Initialize services for the Flask app"""
    app.logger.info("Initializing services...")
    
    # Dictionary to hold service instances
    services = {}
    
    # Initialize services based on app configuration
    try:
        # Import and initialize Workable API service if configured
        if app.config.get("WORKABLE_API_KEY"):
            from services.workable_api import WorkableAPI
            services['workable'] = WorkableAPI(
                api_key=app.config.get("WORKABLE_API_KEY"),
                subdomain=app.config.get("WORKABLE_SUBDOMAIN", "growthacceleratorstaffing")
            )
            app.logger.info("Workable API service initialized")
    except Exception as e:
        app.logger.error(f"Error initializing Workable service: {str(e)}")
    
    return services