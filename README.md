# Terraform + Spacelift AI Reviewer

## Enterprise-Grade AI-Powered Code Review Platform

Complete enterprise application for AI-powered Terraform code review with Spacelift integration, featuring security analysis, cost optimization, and reliability assessment.

## 📁 Project Structure

This project follows an organized structure:

```
├── frontend/          # Next.js 14 Frontend Application
├── backend/           # AWS Lambda Backend (Python)
├── infrastructure/   # Terraform Infrastructure as Code
├── shared/           # Shared resources (types, schemas, constants)
├── scripts/          # Automation scripts
├── tests/            # Test files and fixtures
└── docs/             # Documentation
```

See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for detailed structure.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- AWS Account
- Terraform >= 1.5.0

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Or use the Makefile:
```bash
make dev
```

### Backend Development

```bash
cd backend/lambda
pip install -r requirements.txt
pytest tests/
```

### Infrastructure Deployment

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## 🛠️ Available Commands

```bash
# Development
make dev              # Start frontend dev server
make mock-api         # Start mock API server

# Testing
make test             # Run all tests
make test-frontend    # Run frontend tests
make test-backend     # Run backend tests

# Docker
make docker-up        # Start Docker services
make docker-down      # Stop Docker services

# Setup
make setup           # Set up local environment
make clean           # Clean generated files
```

## 📚 Documentation

- [Architecture](./docs/architecture.md)
- [Platform Architecture](./docs/platform-architecture.md)
- [DynamoDB Schema](./docs/dynamodb-schema.md)
- [Bedrock Implementation](./docs/bedrock-implementation.md)
- [Azure SSO Setup](./docs/azure-sso-setup-guide.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Local Testing](./LOCAL_TESTING.md)
- [Production Hardening](./docs/production/)

## 🏗️ Architecture

```
Frontend (Next.js) → API Gateway → Lambda Functions → DynamoDB
                                    ↓
                              AWS Bedrock (AI)
```

## 🔒 Security

- Azure Entra ID SSO
- JWT validation
- Role-based access control
- WAF protection
- Rate limiting
- Secrets rotation

## 📊 Features

### Frontend
- Executive Dashboard
- PR Review Reports
- Spacelift Run History
- Fix Effectiveness Comparison
- Compliance Audit View

### Backend
- REST API
- AI Review Engine (AWS Bedrock)
- Webhook Handlers
- Historical Analysis
- Trend Aggregation

### Infrastructure
- Multi-account AWS setup
- VPC with private endpoints
- Auto-scaling
- Disaster recovery
- Cost optimization

## 🧪 Testing

See [LOCAL_TESTING.md](./LOCAL_TESTING.md) for complete testing guide.

Quick test:
```bash
# Frontend only (mock API)
cd frontend
npm install
npm run mock-api  # Terminal 1
npm run dev       # Terminal 2
```

## 📝 License

[Your License Here]

## 🤝 Support

For issues and questions, see documentation in `/docs` directory.
