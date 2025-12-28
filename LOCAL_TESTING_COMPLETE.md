# Local Testing - Complete Guide ✅

## Quick Start Options

### Option 1: Frontend Only (Fastest - 2 minutes)

```bash
# 1. Install and setup
npm install
cp .env.local.example .env.local
# Edit .env.local: set NEXT_PUBLIC_USE_MOCK_API=true

# 2. Start mock API (Terminal 1)
npm run mock-api

# 3. Start frontend (Terminal 2)
npm run dev
```

Open `http://localhost:3000` - You're done! ✅

### Option 2: Full Stack with Docker (5 minutes)

```bash
# 1. Start all services
make docker-up

# 2. Setup environment
make setup

# 3. Load test data
python scripts/load-test-data.py --endpoint http://localhost:8000

# 4. Start frontend
npm run dev
```

### Option 3: Complete Local Testing (10 minutes)

```bash
# 1. Full setup
make setup

# 2. Start services
make docker-up

# 3. Test backend
cd lambda && python -m pytest tests/ -v

# 4. Test frontend
cd .. && npm run dev
```

## Testing Checklist

### Frontend Testing
- [ ] All screens load
- [ ] Navigation works
- [ ] Mock authentication works
- [ ] Charts render
- [ ] Real-time updates work
- [ ] Responsive design works

### Backend Testing
- [ ] Lambda functions run
- [ ] DynamoDB operations work
- [ ] API endpoints respond
- [ ] Webhook verification works
- [ ] Error handling works

### Integration Testing
- [ ] Frontend → Backend communication
- [ ] End-to-end review flow
- [ ] Authentication flow
- [ ] Webhook processing

## Files Created

✅ `LOCAL_TESTING.md` - Complete testing guide
✅ `QUICK_START_LOCAL.md` - Quick start options
✅ `scripts/setup-local-env.sh` - Automated setup
✅ `scripts/start-local-services.sh` - Start services
✅ `scripts/test-local-api.sh` - API testing
✅ `scripts/test-webhook-signature.py` - Webhook testing
✅ `scripts/load-test-data.py` - Load test data
✅ `docker-compose.yml` - Docker services
✅ `Makefile` - Common commands
✅ `mock-api/db.json` - Mock API data
✅ `test-data/` - Test data files
✅ `lambda/tests/` - Backend tests

## Common Commands

```bash
# Setup everything
make setup

# Start frontend
npm run dev

# Start mock API
npm run mock-api

# Start Docker services
make docker-up

# Run tests
make test

# Clean up
make clean
```

## Testing Scenarios

1. **Frontend Only**: Use mock API (fastest)
2. **Backend Only**: Test Lambda functions
3. **Full Stack**: Frontend + Backend + DynamoDB
4. **Integration**: End-to-end flows

All testing options are ready! 🚀

