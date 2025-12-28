# Migration Guide - Project Structure Reorganization

## Overview

This guide helps you migrate from the current flat structure to the new organized structure.

## Current vs New Structure

### Current Structure
```
project-root/
├── src/              # Frontend
├── lambda/           # Backend
├── terraform/        # Infrastructure
├── scripts/          # All scripts
└── docs/             # Documentation
```

### New Structure
```
project-root/
├── frontend/         # All frontend code
├── backend/          # All backend code
├── infrastructure/   # All infrastructure code
├── shared/           # Shared resources
├── scripts/          # Organized scripts
├── tests/            # All tests
└── docs/             # Documentation
```

## Step-by-Step Migration

### Option 1: Automated Migration (Recommended)

```bash
# Run the migration script
bash scripts/migrate-structure.sh

# Update import paths
npm run fix-imports  # (if you create this script)
```

### Option 2: Manual Migration

#### Step 1: Create New Directories

```bash
mkdir -p frontend/src
mkdir -p backend/lambda
mkdir -p infrastructure/terraform
mkdir -p shared/{types,schemas,constants}
mkdir -p scripts/{deployment,testing,utilities}
mkdir -p tests/{integration,e2e,fixtures}
```

#### Step 2: Move Frontend Files

```bash
# Move frontend files
mv src frontend/
mv package.json frontend/
mv next.config.js frontend/
mv tailwind.config.ts frontend/
mv tsconfig.json frontend/
mv postcss.config.js frontend/
mv components.json frontend/
```

#### Step 3: Move Backend Files

```bash
# Move backend files
mv lambda backend/
mv requirements.txt backend/  # if exists at root
```

#### Step 4: Move Infrastructure Files

```bash
# Move infrastructure files
mv terraform infrastructure/
```

#### Step 5: Organize Scripts

```bash
# Move testing scripts
mv scripts/setup-local-env.sh scripts/testing/
mv scripts/test-local-api.sh scripts/testing/
mv scripts/load-test-data.py scripts/testing/

# Move utility scripts
mv scripts/test-webhook-signature.py scripts/utilities/
```

#### Step 6: Move Test Data

```bash
# Move test data
mv test-data tests/fixtures/
mv test-payloads tests/fixtures/
mv mock-api tests/fixtures/
```

## Update Import Paths

### Frontend Imports

**Before:**
```typescript
import { useAuth } from "@/components/auth-provider"
```

**After:**
```typescript
// Paths remain the same if using TypeScript path aliases
// Just ensure tsconfig.json paths are updated
```

Update `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Backend Imports

**Before:**
```python
from models import Review
```

**After:**
```python
# If you organize into subdirectories:
from backend.lambda.models import Review
# OR keep relative imports:
from .models import Review
```

### Terraform Paths

**Before:**
```hcl
source = "../modules/vpc"
```

**After:**
```hcl
source = "../../infrastructure/terraform/modules/vpc"
```

## Update Configuration Files

### package.json

Update scripts to work from `frontend/` directory:

```json
{
  "scripts": {
    "dev": "cd frontend && next dev",
    "build": "cd frontend && next build"
  }
}
```

### Makefile

Update paths in Makefile:

```makefile
dev:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest
```

### CI/CD

Update CI/CD pipeline paths:

```yaml
# Example GitHub Actions
- name: Build Frontend
  run: |
    cd frontend
    npm install
    npm run build

- name: Deploy Backend
  run: |
    cd backend
    # Deploy Lambda functions
```

## Verification

### 1. Test Frontend Build

```bash
cd frontend
npm install
npm run build
```

### 2. Test Backend

```bash
cd backend
pip install -r requirements.txt
pytest
```

### 3. Test Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform validate
```

## Rollback Plan

If something goes wrong:

1. **Git Checkout**: `git checkout main` (if using Git)
2. **Manual Restore**: Move files back to original locations
3. **Update Imports**: Revert import path changes

## Benefits After Migration

✅ **Clear Separation**: Frontend, backend, and infrastructure are clearly separated
✅ **Better Organization**: Related files are grouped together
✅ **Easier Navigation**: Easier to find files
✅ **Team Collaboration**: Different teams can work on different directories
✅ **Scalability**: Structure supports growth

## Common Issues

### Issue 1: Import Path Errors

**Solution**: Update `tsconfig.json` paths or use relative imports

### Issue 2: Build Scripts Fail

**Solution**: Update package.json scripts to use correct paths

### Issue 3: Terraform Module Paths

**Solution**: Update module source paths in Terraform files

## Next Steps

1. ✅ Run migration script
2. ✅ Update import paths
3. ✅ Update configuration files
4. ✅ Test builds
5. ✅ Update documentation
6. ✅ Commit changes

## Support

If you encounter issues:
1. Check `PROJECT_STRUCTURE.md` for structure details
2. Review import paths
3. Verify configuration files
4. Test each component separately

