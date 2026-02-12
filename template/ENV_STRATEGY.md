# Environment Files Strategy

This project uses a standardized approach to environment configuration that works for both local development and Docker deployments.

## File Structure

```
template/
├── .env.example              # Docker Compose defaults (ports, DB config)
├── docker-compose.yml        # Uses ${VAR:-default} syntax
├── docker-compose.override.yml  # Local overrides (git-ignored)
├── backend/
│   └── .env.example         # Backend app configuration
└── frontend/
    └── .env.example         # Frontend app configuration
```

## Environment Files

### 1. Root `.env.example`
Docker Compose configuration for container orchestration:
- Service ports (BACKEND_PORT, FRONTEND_PORT, DB_PORT)
- Database credentials (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

**Usage:**
```bash
cp .env.example .env
# Edit .env with your local port preferences
```

### 2. Backend `.env.example`
Application-level configuration for FastAPI:
- APP_NAME, DEBUG mode
- HOST, PORT
- DATABASE_URL (constructed from docker-compose vars)
- CORS_ORIGINS

**Usage:**
```bash
cd backend
cp .env.example .env.local
# Edit .env.local with development settings
```

### 3. Frontend `.env.example` (future)
Frontend application configuration:
- API base URL
- Feature flags
- Public environment variables

## Local Override Pattern

### For Docker Compose
Create a local `.env` file (git-ignored):
```bash
cp .env.example .env
```

Or use `docker-compose.override.yml` for advanced container customization:
```yaml
# docker-compose.override.yml (git-ignored)
services:
  db:
    ports:
      - "5433:5432"  # Use different port locally
```

### For Applications
Create `.env.local` files (git-ignored):
```bash
# Backend
cd backend
cp .env.example .env.local
# Set DEBUG=true, custom DATABASE_URL, etc.

# Frontend (future)
cd frontend
cp .env.example .env.local
# Set development API URLs, feature flags, etc.
```

## Loading Order

### Docker Compose
```
1. docker-compose.yml (with ${VAR:-default} defaults)
2. .env (if exists, overrides defaults)
3. docker-compose.override.yml (if exists, overrides services)
```

### Backend (FastAPI)
```
1. .env.example (never loaded, just documentation)
2. .env.local (loaded in development)
3. Environment variables from docker-compose
```

## Git Ignore Rules

Already configured in `.gitignore`:
```gitignore
# Environment
.env
.env.local
.env.*.local

# Docker
docker-compose.override.yml
```

## Best Practices

1. **Never commit sensitive values**
   - Keep real credentials in `.env`, `.env.local`, not in `.env.example`
   - Use placeholder values in `.env.example` files

2. **Use meaningful defaults**
   - `.env.example` should work out-of-the-box for new developers
   - Port numbers should be uncommon to avoid conflicts (9095, not 8000)

3. **Document required variables**
   - Comment each variable in `.env.example`
   - Explain what it does and when to change it

4. **Environment-specific files**
   - `.env.development` for dev-specific settings
   - `.env.production` for production settings
   - `.env.test` for testing configuration
   - All should be git-ignored except `.example` versions

5. **Docker Compose variable interpolation**
   - Use `${VAR:-default}` syntax for optional vars with defaults
   - Use `${VAR}` syntax for required vars (will error if missing)
   - Reference example:
     ```yaml
     POSTGRES_USER: ${POSTGRES_USER:-app}  # Optional with default
     DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
     ```

## Port Conflict Handling

If default ports conflict with existing services:

1. **Quick fix** - Override in `.env`:
   ```bash
   BACKEND_PORT=9096
   FRONTEND_PORT=3151
   DB_PORT=5433
   ```

2. **Advanced** - Use `docker-compose.override.yml`:
   ```yaml
   services:
     backend:
       ports:
         - "9096:9095"
   ```

## Example Workflows

### New Developer Setup
```bash
# 1. Clone repository
git clone <repo>
cd open-fullstack-template/template

# 2. Copy environment files (optional - defaults work)
cp .env.example .env

# 3. Start services
docker-compose up
```

### Local Development with Custom Ports
```bash
# Create .env with custom ports
cat > .env << EOF
BACKEND_PORT=9096
FRONTEND_PORT=3151
DB_PORT=5433
EOF

docker-compose up
```

### Backend Development Outside Docker
```bash
cd backend

# Create local env with custom DATABASE_URL
cp .env.example .env.local
echo "DEBUG=true" >> .env.local
echo "DATABASE_URL=postgresql://app:app@localhost:5432/app" >> .env.local

# Run backend directly
uv run uvicorn src.app:app --reload
```

## Future Enhancements

- [ ] Add `.env.production.example` for production reference
- [ ] Add `.env.test.example` for testing configuration
- [ ] Frontend `.env.example` when frontend is scaffolded
- [ ] Validation script to check required env vars
- [ ] Documentation on secrets management for production
