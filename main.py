"""
Growth Accelerator Platform - Azure Production Deployment
"""

import os
from flask import Flask, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "growth-accelerator-production")

@app.route('/')
@app.route('/landing')
@app.route('/home')
def landing_page():
    """Growth Accelerator Platform Landing Page"""
    
    landing_html = """
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
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white fixed-top" style="box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div class="container">
            <a class="navbar-brand text-primary fw-bold" href="#">
                <i class="bi bi-rocket-takeoff me-2"></i>Growth Accelerator
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="#features">Features</a>
                <a class="nav-link" href="#about">About</a>
                <a class="nav-link" href="/login">
                    <i class="bi bi-box-arrow-in-right me-1"></i>Login
                </a>
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
            <a href="/login" class="btn btn-primary btn-lg">
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
    """
    
    return render_template_string(landing_html)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Growth Accelerator Platform",
        "environment": "production",
        "deployment": "azure_web_app"
    }

@app.route('/login')
def login():
    """Login placeholder"""
    return "<h2>Login functionality will be implemented here</h2><p><a href='/'>Back to home</a></p>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
