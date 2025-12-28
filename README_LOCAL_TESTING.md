# Local Testing - Quick Reference

## 🚀 Fastest Way to Test (2 minutes)

```bash
# 1. Install dependencies
npm install

# 2. Copy environment file
cp .env.local.example .env.local
# Edit .env.local and set: NEXT_PUBLIC_USE_MOCK_API=true

# 3. Start mock API (Terminal 1)
npm run mock-api

# 4. Start frontend (Terminal 2)
npm run dev
```

Open `http://localhost:3000` ✅

## 📚 Full Documentation

- **Quick Start**: See [QUICK_START_LOCAL.md](./QUICK_START_LOCAL.md)
- **Complete Guide**: See [LOCAL_TESTING.md](./LOCAL_TESTING.md)
- **Setup Script**: Run `make setup` or `bash scripts/setup-local-env.sh`

## 🛠️ Common Commands

```bash
# Setup everything
make setup

# Start frontend
npm run dev

# Start mock API
npm run mock-api

# Start Docker services (DynamoDB, etc.)
make docker-up

# Run tests
make test

# Clean up
make clean
```

## 🐳 Docker Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down
```

## 📝 Testing Options

1. **Frontend Only** (Mock API) - Fastest
2. **Backend Only** (Lambda tests) - Unit testing
3. **Full Stack** (Docker + Services) - Integration testing
4. **Real AWS** (Dev account) - Production-like testing

See [LOCAL_TESTING.md](./LOCAL_TESTING.md) for details.

