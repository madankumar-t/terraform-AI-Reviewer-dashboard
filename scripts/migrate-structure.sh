#!/bin/bash
# Script to reorganize project structure

set -e

echo "🔄 Reorganizing project structure..."

# Create new directories
echo "Creating new directory structure..."
mkdir -p frontend/src
mkdir -p backend/lambda
mkdir -p infrastructure/terraform
mkdir -p shared/{types,schemas,constants}
mkdir -p scripts/{deployment,testing,utilities}
mkdir -p tests/{integration,e2e,fixtures}
mkdir -p config/environments

# Move frontend files
echo "Moving frontend files..."
if [ -d "src" ]; then
    mv src frontend/
fi
if [ -f "package.json" ]; then
    mv package.json frontend/
fi
if [ -f "next.config.js" ]; then
    mv next.config.js frontend/
fi
if [ -f "tailwind.config.ts" ]; then
    mv tailwind.config.ts frontend/
fi
if [ -f "tsconfig.json" ]; then
    mv tsconfig.json frontend/
fi
if [ -f "postcss.config.js" ]; then
    mv postcss.config.js frontend/
fi
if [ -f "components.json" ]; then
    mv components.json frontend/
fi
if [ -f "next-env.d.ts" ]; then
    mv next-env.d.ts frontend/
fi

# Move backend files
echo "Moving backend files..."
if [ -d "lambda" ]; then
    mv lambda backend/
fi
if [ -f "requirements.txt" ] && [ ! -f "backend/requirements.txt" ]; then
    mv requirements.txt backend/
fi

# Move infrastructure files
echo "Moving infrastructure files..."
if [ -d "terraform" ]; then
    mv terraform infrastructure/
fi

# Move scripts
echo "Organizing scripts..."
if [ -d "scripts" ]; then
    # Move testing scripts
    mv scripts/setup-local-env.sh scripts/testing/ 2>/dev/null || true
    mv scripts/test-local-api.sh scripts/testing/ 2>/dev/null || true
    mv scripts/load-test-data.py scripts/testing/ 2>/dev/null || true
    mv scripts/start-local-services.sh scripts/testing/ 2>/dev/null || true
    
    # Move utility scripts
    mv scripts/test-webhook-signature.py scripts/utilities/ 2>/dev/null || true
    
    # Evidence scripts stay in scripts/evidence/
fi

# Move test data
echo "Organizing test data..."
if [ -d "test-data" ]; then
    mv test-data tests/fixtures/
fi
if [ -d "test-payloads" ]; then
    mv test-payloads tests/fixtures/
fi
if [ -d "mock-api" ]; then
    mv mock-api tests/fixtures/
fi

# Move documentation
echo "Organizing documentation..."
if [ -d "docs" ]; then
    # Keep docs at root for now, but organize
    mkdir -p docs/architecture docs/compliance docs/deployment docs/production
fi

# Create symlinks for backward compatibility (optional)
echo "Creating backward compatibility..."
# Note: Symlinks may not work on all systems, so we'll create README files instead

echo "✅ Project structure reorganized!"
echo ""
echo "Next steps:"
echo "1. Update import paths in frontend code"
echo "2. Update import paths in backend code"
echo "3. Update Terraform paths"
echo "4. Test the build"
echo ""
echo "See PROJECT_STRUCTURE.md for details"

