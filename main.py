"""
Main entry point for Growth Accelerator Staffing Platform on Azure
24/7 Production Environment with Reliability Monitoring
"""

# Import the complete staffing application
from staffing_app import app
import logging
import os

# Initialize 24/7 reliability monitoring
try:
    from services.reliability_monitor import reliability_monitor
    reliability_monitor.start_monitoring()
    app.config['RELIABILITY_MONITOR'] = reliability_monitor
    logging.info("24/7 reliability monitoring activated")
except Exception as e:
    logging.error(f"Failed to initialize reliability monitoring: {e}")

# Enhanced health endpoint for 24/7 monitoring
@app.route('/api/health')
def health_check():
    """Comprehensive health check for 24/7 monitoring"""
    try:
        monitor = app.config.get('RELIABILITY_MONITOR')
        if monitor:
            metrics = monitor.get_system_metrics()
            workable_ok, workable_msg = monitor.check_workable_api()
            db_ok, db_msg = monitor.check_database_connection()
            
            return {
                "status": "healthy" if workable_ok and db_ok else "degraded",
                "service": "Growth Accelerator Platform",
                "environment": "production",
                "uptime_hours": metrics.get('uptime_hours', 0),
                "uptime_percentage": metrics.get('uptime_percentage', 100),
                "avg_response_time_ms": metrics.get('avg_response_time_ms', 0),
                "workable_api": {
                    "connected": workable_ok,
                    "status": workable_msg
                },
                "database": {
                    "connected": db_ok,
                    "status": db_msg
                },
                "deployment": {
                    "always_on": True,
                    "monitoring": True,
                    "azure_ready": True
                },
                "modules": {
                    "staffing": "operational",
                    "services": "operational", 
                    "contracting": "operational"
                }
            }
        else:
            return {
                "status": "healthy",
                "service": "Growth Accelerator Platform",
                "monitoring": "basic"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }, 500

@app.route('/api/metrics')
def system_metrics():
    """Detailed system metrics for monitoring"""
    try:
        monitor = app.config.get('RELIABILITY_MONITOR')
        if monitor:
            return monitor.get_system_metrics()
        else:
            return {"error": "Monitoring not available"}, 503
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/landing')
@app.route('/home')
def landing_page():
    """Growth Accelerator Platform Landing Page"""
    from flask import render_template_string
    
    landing_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Growth Accelerator Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        :root {
            --ga-blue: #2563eb;
            --ga-light-blue: #3b82f6;
            --ga-dark: #1e293b;
            --ga-gray: #64748b;
        }
        
        .hero-section {
            background: linear-gradient(135deg, var(--ga-blue) 0%, var(--ga-light-blue) 100%);
            color: white;
            padding: 100px 0;
        }
        
        .feature-card {
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            width: 60px;
            height: 60px;
            background: var(--ga-blue);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        .stats-section {
            background-color: #f8fafc;
            padding: 80px 0;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--ga-blue);
        }
        
        .cta-section {
            background: var(--ga-dark);
            color: white;
            padding: 80px 0;
        }
        
        .btn-ga-primary {
            background-color: var(--ga-blue);
            border-color: var(--ga-blue);
            color: white;
            padding: 12px 30px;
            font-weight: 600;
            border-radius: 8px;
        }
        
        .btn-ga-primary:hover {
            background-color: var(--ga-light-blue);
            border-color: var(--ga-light-blue);
            color: white;
        }
        
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        .navbar {
            background-color: white !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white fixed-top">
        <div class="container">
            <a class="navbar-brand text-primary" href="#">
                <i class="bi bi-rocket-takeoff me-2"></i>Growth Accelerator
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#features">Features</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#about">About</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/login">
                            <i class="bi bi-box-arrow-in-right me-1"></i>Login
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-4 fw-bold mb-4">Accelerate Your Growth with AI-Powered Solutions</h1>
                    <p class="lead mb-4">
                        Transform your business with our comprehensive platform that combines advanced staffing solutions, 
                        intelligent services management, and streamlined contracting workflows.
                    </p>
                    <div class="d-flex gap-3">
                        <a href="/login" class="btn btn-light btn-lg">
                            <i class="bi bi-play-circle me-2"></i>Get Started
                        </a>
                        <a href="#features" class="btn btn-outline-light btn-lg">
                            <i class="bi bi-info-circle me-2"></i>Learn More
                        </a>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="text-center">
                        <i class="bi bi-graph-up-arrow" style="font-size: 15rem; opacity: 0.2;"></i>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-5">
        <div class="container">
            <div class="row">
                <div class="col-lg-12 text-center mb-5">
                    <h2 class="display-5 fw-bold">Complete Business Acceleration Platform</h2>
                    <p class="lead text-muted">Three powerful modules working together to drive your success</p>
                </div>
            </div>
            <div class="row g-4">
                <div class="col-lg-4">
                    <div class="card feature-card">
                        <div class="card-body p-4">
                            <div class="feature-icon">
                                <i class="bi bi-people-fill text-white" style="font-size: 1.5rem;"></i>
                            </div>
                            <h4 class="card-title">Staffing Module</h4>
                            <p class="card-text">
                                Complete recruitment workflow management with Workable API integration. 
                                Track candidates, manage job postings, and streamline your hiring process.
                            </p>
                            <ul class="list-unstyled">
                                <li><i class="bi bi-check-circle text-success me-2"></i>Workable API Integration</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Candidate Management</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Job Posting Automation</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Real-time Analytics</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card feature-card">
                        <div class="card-body p-4">
                            <div class="feature-icon">
                                <i class="bi bi-gear-fill text-white" style="font-size: 1.5rem;"></i>
                            </div>
                            <h4 class="card-title">Services Workspace</h4>
                            <p class="card-text">
                                Integrated services management with LinkedIn automation and desktop application support. 
                                Streamline your service delivery workflow.
                            </p>
                            <ul class="list-unstyled">
                                <li><i class="bi bi-check-circle text-success me-2"></i>LinkedIn Integration</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Desktop App Support</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Service Automation</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Workflow Management</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card feature-card">
                        <div class="card-body p-4">
                            <div class="feature-icon">
                                <i class="bi bi-file-earmark-text-fill text-white" style="font-size: 1.5rem;"></i>
                            </div>
                            <h4 class="card-title">Contracting System</h4>
                            <p class="card-text">
                                Comprehensive contracting platform with API integration for hourly registration 
                                and automated payment processing.
                            </p>
                            <ul class="list-unstyled">
                                <li><i class="bi bi-check-circle text-success me-2"></i>Hourly Registration</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Payment Automation</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Contract Management</li>
                                <li><i class="bi bi-check-circle text-success me-2"></i>Financial Reporting</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
        <div class="container">
            <div class="row text-center">
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-number">24/7</div>
                    <p class="text-muted">Always Available</p>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-number">99.9%</div>
                    <p class="text-muted">Uptime Guarantee</p>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-number">API</div>
                    <p class="text-muted">Integrated</p>
                </div>
                <div class="col-lg-3 col-md-6 mb-4">
                    <div class="stat-number">Cloud</div>
                    <p class="text-muted">Azure Powered</p>
                </div>
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-5">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h2 class="display-5 fw-bold mb-4">Built for Modern Businesses</h2>
                    <p class="lead">
                        Growth Accelerator Platform is designed to meet the demands of today's fast-paced business environment. 
                        Our platform combines cutting-edge technology with practical solutions to help you scale efficiently.
                    </p>
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <h5><i class="bi bi-shield-check text-primary me-2"></i>Secure & Reliable</h5>
                            <p>Enterprise-grade security with 24/7 monitoring and backup systems.</p>
                        </div>
                        <div class="col-md-6">
                            <h5><i class="bi bi-lightning-charge text-primary me-2"></i>Fast & Efficient</h5>
                            <p>Optimized performance with Azure cloud infrastructure for maximum speed.</p>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="text-center">
                        <i class="bi bi-building" style="font-size: 12rem; color: var(--ga-blue); opacity: 0.1;"></i>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
        <div class="container text-center">
            <h2 class="display-5 fw-bold mb-4">Ready to Accelerate Your Growth?</h2>
            <p class="lead mb-4">
                Join businesses worldwide that trust Growth Accelerator Platform to drive their success.
            </p>
            <a href="/login" class="btn btn-ga-primary btn-lg">
                <i class="bi bi-rocket-takeoff me-2"></i>Start Your Journey
            </a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-light py-4">
        <div class="container">
            <div class="row">
                <div class="col-lg-6">
                    <h5>Growth Accelerator Platform</h5>
                    <p class="text-muted">Empowering businesses with intelligent automation and seamless integrations.</p>
                </div>
                <div class="col-lg-6 text-lg-end">
                    <p class="text-muted">© 2024 Growth Accelerator. All rights reserved.</p>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    '''
    
    return render_template_string(landing_html)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    # Production configuration for 24/7 operation
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Starting Growth Accelerator Platform for 24/7 operation")
    logging.info(f"Always On enabled: {os.path.exists('.always_on_enabled')}")
    logging.info(f"Production mode: {not app.debug}")
    
    app.run(host='0.0.0.0', port=port, debug=False)