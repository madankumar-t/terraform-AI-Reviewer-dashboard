# Quick Start Guide

## 🚀 Getting Started

After the structure migration, here's how to get started:

## Installation

### Option 1: Use Root Package.json (Recommended)

```bash
# Install frontend dependencies
npm run install:frontend

# Install backend dependencies
npm run install:backend

# Or install both
npm run setup
```

### Option 2: Manual Installation

```bash
# Frontend
cd frontend
npm install
cd ..

# Backend
cd backend/lambda
pip install -r requirements.txt
cd ../..
```

## Development

### Start Frontend

```bash
# Option 1: From root
npm run dev

# Option 2: Use Makefile
make dev

# Option 3: Navigate to frontend
cd frontend
npm run dev
```

### Start Mock API

```bash
# Option 1: From root
npm run mock-api

# Option 2: Navigate to frontend
cd frontend
npm run mock-api
```

## Testing

### Run All Tests

```bash
# From root
npm run test:all

# Or use Makefile
make test
```

### Frontend Tests Only

```bash
npm test
# OR
make test-frontend
```

### Backend Tests Only

```bash
npm run test:backend
# OR
make test-backend
```

## Common Commands

```bash
# Development
npm run dev              # Start frontend dev server
npm run mock-api         # Start mock API

# Building
npm run build           # Build frontend

# Testing
npm test                # Frontend tests
npm run test:backend    # Backend tests
npm run test:all        # All tests

# Setup
npm run setup           # Install all dependencies
npm run install:frontend # Install frontend only
npm run install:backend  # Install backend only
```

## Directory Structure

Remember:
- **Frontend code**: `frontend/` directory
- **Backend code**: `backend/lambda/` directory
- **Infrastructure**: `infrastructure/terraform/` directory

## Troubleshooting

### Error: Cannot find package.json

**Solution**: Make sure you're running commands from the root directory, or navigate to the appropriate subdirectory.

```bash
# If in root, use npm scripts:
npm run dev

# Or navigate to frontend:
cd frontend
npm run dev
```

### Error: Module not found

**Solution**: Install dependencies first:

```bash
npm run setup
```

## Next Steps

1. ✅ Install dependencies: `npm run setup`
2. ✅ Start development: `npm run dev`
3. ✅ Read [LOCAL_TESTING.md](./LOCAL_TESTING.md) for testing
4. ✅ Read [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment

