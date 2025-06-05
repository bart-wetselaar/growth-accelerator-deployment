# Growth Accelerator - Staffing Platform

A comprehensive staffing and deployment acceleration platform leveraging AI-driven technologies.

## Features

- **Staffing Module**: Complete workflow with Workable API integration
- **Services Workspace**: LinkedIn and desktop app integrations  
- **Contracting System**: API integration for hourly registration and payments
- **AI Matching**: Intelligent candidate-job matching algorithms
- **Real-time Monitoring**: 24/7 availability with health checks

## Deployment

This application is automatically deployed to Azure Web App at https://app.growthaccelerator.nl

### Azure Deployment
- **Environment**: Azure Web App (Linux)
- **Runtime**: Python 3.11
- **Framework**: Flask with Gunicorn
- **Database**: PostgreSQL
- **Monitoring**: Built-in health checks

### CI/CD Pipeline
- GitHub Actions for automated deployment
- Azure Web App deployment with publish profile
- Automated dependency installation
- Health check verification

## API Integrations

- **Workable API**: Recruitment and job management
- **LinkedIn API**: Professional networking integration
- **Azure APIs**: Cloud deployment and monitoring

## Local Development

```bash
pip install -r requirements.txt
python main.py
```

Application will be available at http://localhost:5000

## Production

Live deployment: https://app.growthaccelerator.nl

## Architecture

- Python-driven microservices architecture
- GitHub Actions CI/CD pipeline
- Azure Web App deployment with Linux runtime
- Multi-cloud platform integration
- Automated deployment workflows
- Real-time recruitment platform synchronization
