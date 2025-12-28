# Project Structure

## Overview

This document describes the organized project structure separating frontend, backend, infrastructure, and common resources.

## Directory Structure

```
terraform-spacelift-ai-reviewer/
│
├── frontend/                    # Next.js Frontend Application
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # React components
│   │   └── lib/                # Frontend utilities
│   ├── public/                 # Static assets
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                     # AWS Lambda Backend
│   ├── lambda/                 # Lambda function code
│   │   ├── handlers/           # Lambda handlers
│   │   ├── services/           # Business logic services
│   │   ├── models/             # Data models
│   │   ├── utils/              # Utility functions
│   │   └── tests/              # Unit tests
│   ├── requirements.txt
│   └── README.md
│
├── infrastructure/              # Terraform Infrastructure
│   ├── terraform/
│   │   ├── modules/            # Reusable Terraform modules
│   │   ├── environments/       # Environment-specific configs
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── README.md
│
├── shared/                      # Shared Resources
│   ├── types/                  # TypeScript type definitions
│   ├── schemas/                # JSON schemas
│   ├── constants/              # Shared constants
│   └── docs/                   # Documentation
│
├── scripts/                     # Automation Scripts
│   ├── deployment/             # Deployment scripts
│   ├── testing/                # Testing scripts
│   ├── evidence/               # Compliance evidence scripts
│   └── utilities/              # Utility scripts
│
├── tests/                       # Integration & E2E Tests
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
├── docs/                        # Documentation
│   ├── architecture/
│   ├── compliance/
│   ├── deployment/
│   └── production/
│
├── config/                      # Configuration Files
│   ├── environments/
│   └── templates/
│
└── README.md                    # Project root README
```

## Detailed Structure

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Auth routes group
│   │   ├── executive/         # Executive dashboard
│   │   ├── pr-review/         # PR review pages
│   │   ├── spacelift-runs/    # Spacelift runs
│   │   ├── compliance/        # Compliance pages
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   │
│   ├── components/            # React Components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── dashboard/         # Dashboard components
│   │   ├── reviews/           # Review components
│   │   └── shared/            # Shared components
│   │
│   └── lib/                   # Frontend Libraries
│       ├── api.ts             # API client
│       ├── auth.ts            # Authentication
│       └── utils.ts           # Utilities
│
├── public/                     # Static files
├── .env.local.example          # Environment template
└── package.json
```

### Backend (`backend/`)

```
backend/
├── lambda/
│   ├── handlers/              # Lambda Handlers
│   │   ├── api_handler.py
│   │   ├── webhook_handler.py
│   │   ├── ai_reviewer.py
│   │   └── jwt_authorizer.py
│   │
│   ├── services/             # Business Logic
│   │   ├── ai_service.py
│   │   ├── bedrock_service.py
│   │   └── dynamodb_client.py
│   │
│   ├── models/               # Data Models
│   │   └── models.py
│   │
│   ├── utils/                # Utilities
│   │   ├── logger.py
│   │   ├── secrets_manager.py
│   │   └── risk_scoring.py
│   │
│   └── tests/                # Tests
│       ├── unit/
│       ├── integration/
│       └── conftest.py
│
└── requirements.txt
```

### Infrastructure (`infrastructure/`)

```
infrastructure/
├── terraform/
│   ├── modules/               # Reusable Modules
│   │   ├── vpc/
│   │   ├── frontend/
│   │   ├── monitoring/
│   │   └── security/
│   │
│   ├── environments/          # Environment Configs
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   │
│   ├── main.tf               # Main configuration
│   ├── variables.tf          # Input variables
│   ├── outputs.tf            # Output values
│   └── README.md
│
└── README.md
```

### Shared (`shared/`)

```
shared/
├── types/                    # TypeScript Types
│   ├── api.ts               # API types
│   ├── models.ts            # Data models
│   └── auth.ts              # Auth types
│
├── schemas/                  # JSON Schemas
│   ├── review.schema.json
│   └── webhook.schema.json
│
└── constants/               # Constants
    ├── roles.ts
    └── config.ts
```

### Scripts (`scripts/`)

```
scripts/
├── deployment/              # Deployment Scripts
│   ├── deploy-frontend.sh
│   ├── deploy-backend.sh
│   └── deploy-infrastructure.sh
│
├── testing/                 # Testing Scripts
│   ├── setup-local-env.sh
│   ├── test-local-api.sh
│   └── load-test-data.py
│
├── evidence/                # Compliance Scripts
│   ├── generate-evidence.py
│   └── access-review-report.py
│
└── utilities/              # Utility Scripts
    └── test-webhook-signature.py
```

## Migration Plan

1. **Create new directory structure**
2. **Move files to appropriate locations**
3. **Update import paths**
4. **Update configuration files**
5. **Update documentation**

## Benefits

- ✅ Clear separation of concerns
- ✅ Easier to navigate
- ✅ Better for team collaboration
- ✅ Scalable structure
- ✅ Follows best practices

