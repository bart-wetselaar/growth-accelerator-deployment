import os
from functools import wraps
from flask import Flask, request, Response, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'growth-accelerator-production'

def check_auth(username, password):
    return username == 'admin' and password == 'GrowthAccelerator2024!'

def authenticate():
    return Response(
        'Authentication required', 401,
        {'WWW-Authenticate': 'Basic realm="Growth Accelerator Platform"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@requires_auth
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Growth Accelerator Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .header { text-align: center; color: white; margin-bottom: 3rem; }
        .header h1 { font-size: 3rem; margin-bottom: 1rem; }
        .status { background: rgba(40, 167, 69, 0.9); color: white; padding: 1rem 2rem; border-radius: 25px; display: inline-block; }
        .modules { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 3rem 0; }
        .module { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .info { background: white; padding: 2rem; border-radius: 10px; margin: 2rem 0; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Growth Accelerator Platform</h1>
            <p style="font-size: 1.2rem; margin-bottom: 2rem;">AI-Powered Staffing Solutions</p>
            <div class="status">Production Environment - Azure West Europe</div>
        </div>
        
        <div class="info">
            <h3>Deployment Information</h3>
            <p><strong>Primary URL:</strong> ga-hwaffmb0eqajfza5.westeurope-01.azurewebsites.net</p>
            <p><strong>Custom Domain:</strong> app.growthaccelerator.nl</p>
            <p><strong>Authentication:</strong> Basic Auth Active</p>
            <p><strong>Deployed:</strong> {{ timestamp }}</p>
        </div>
        
        <div class="modules">
            <div class="module">
                <h3>Staffing Module</h3>
                <p>Complete workflow from client onboarding through placement with Workable API integration</p>
            </div>
            
            <div class="module">
                <h3>Services Workspace</h3>
                <p>LinkedIn and desktop application integrations for enhanced productivity</p>
            </div>
            
            <div class="module">
                <h3>Contracting System</h3>
                <p>API integration for hourly registration and payment processing</p>
            </div>
        </div>
    </div>
</body>
</html>
    """, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "Growth Accelerator Platform",
        "environment": "production",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host="0.0.0.0", port=port)
