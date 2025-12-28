# Cognito Configuration Guide

## Where to Update Cognito Credentials

### File: `frontend/.env.local`

Create this file in the `frontend/` directory with your Cognito credentials.

## Required Environment Variables

```env
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_COGNITO_DOMAIN=terraform-ai-reviewer-dev
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
```

## How to Get These Values

### Option 1: From Terraform Outputs

After deploying infrastructure:

```bash
cd infrastructure/terraform
terraform output
```

Look for:
- `cognito_user_pool_id`
- `cognito_client_id`
- `cognito_domain`

### Option 2: From AWS Console

1. **User Pool ID**:
   - Go to AWS Cognito Console
   - Select your User Pool
   - Copy the User Pool ID (format: `us-east-1_XXXXXXXXX`)

2. **Client ID**:
   - In the same User Pool
   - Go to "App integration" → "App clients"
   - Copy the Client ID

3. **Domain**:
   - In the same User Pool
   - Go to "App integration" → "Domain"
   - Copy the domain prefix (without `.auth.region.amazoncognito.com`)

4. **Region**:
   - Check which AWS region your Cognito is in
   - Usually `us-east-1`, `us-west-2`, etc.

## Setup Steps

### 1. Create Environment File

```bash
cd frontend
cp .env.local.example .env.local
```

### 2. Edit `.env.local`

Open `frontend/.env.local` and update with your values:

```env
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_ABC123XYZ
NEXT_PUBLIC_COGNITO_CLIENT_ID=1a2b3c4d5e6f7g8h9i0j
NEXT_PUBLIC_COGNITO_DOMAIN=terraform-ai-reviewer-prod
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_API_URL=https://abc123xyz.execute-api.us-east-1.amazonaws.com
```

### 3. Restart Development Server

After updating `.env.local`:

```bash
# Stop the dev server (Ctrl+C)
# Then restart
npm run dev
```

## File Locations

- **Environment file**: `frontend/.env.local` (create this file)
- **Example file**: `frontend/.env.local.example` (template)
- **Code that uses it**: `frontend/src/lib/auth.ts` (reads the env vars)

## Important Notes

1. **`.env.local` is gitignored** - Never commit this file
2. **Restart required** - Next.js only reads env vars at startup
3. **NEXT_PUBLIC_ prefix** - Required for client-side access in Next.js
4. **No quotes needed** - Don't wrap values in quotes in `.env.local`

## Verification

After setting up, verify the configuration:

1. Start the dev server: `npm run dev`
2. Open browser console
3. Check if environment variables are loaded (they won't show in console, but auth should work)
4. Try logging in

## Troubleshooting

### Error: "User Pool ID is required"

**Solution**: Make sure `NEXT_PUBLIC_COGNITO_USER_POOL_ID` is set in `.env.local`

### Error: "Invalid client ID"

**Solution**: Verify `NEXT_PUBLIC_COGNITO_CLIENT_ID` matches the Client ID in Cognito

### Error: "Domain not found"

**Solution**: 
- Check `NEXT_PUBLIC_COGNITO_DOMAIN` is correct
- Make sure the domain is configured in Cognito
- Verify the region matches

### Environment variables not loading

**Solution**:
1. Make sure file is named `.env.local` (not `.env.local.example`)
2. Restart the Next.js dev server
3. Check file is in `frontend/` directory (not root)

## Example `.env.local` File

```env
# Production Cognito Configuration
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_ABC123XYZ
NEXT_PUBLIC_COGNITO_CLIENT_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
NEXT_PUBLIC_COGNITO_DOMAIN=terraform-ai-reviewer-prod
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_API_URL=https://abc123xyz.execute-api.us-east-1.amazonaws.com
```

## Next Steps

1. ✅ Create `frontend/.env.local` file
2. ✅ Add your Cognito credentials
3. ✅ Restart dev server
4. ✅ Test authentication

