# Troubleshooting Guide

This guide covers common issues you might encounter when working with the full-stack template and their solutions.

## Table of Contents

- [Port Conflicts](#port-conflicts)
- [Database Issues](#database-issues)
- [Docker Issues](#docker-issues)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Migration Issues](#migration-issues)
- [Environment & Configuration](#environment--configuration)
- [Development Tools](#development-tools)

---

## Port Conflicts

### Problem: Port Already in Use

When starting services, you see errors like:
```
Error starting userland proxy: listen tcp4 0.0.0.0:9095: bind: address already in use
```

### Solutions

#### Option 1: Override Ports (Recommended)

1. Create a `.env` file in the template root directory:
```bash
cp .env.example .env
```

2. Edit `.env` to specify different ports:
```bash
# .env
BACKEND_PORT=9096    # Default: 9095
FRONTEND_PORT=3151   # Default: 3150
DB_PORT=5433         # Default: 5432
```

3. Restart services:
```bash
docker-compose down
docker-compose up
```

Your application will now be available at the new ports:
- Backend API: `http://localhost:9096`
- Frontend: `http://localhost:3151`
- Database: `localhost:5433`

#### Option 2: Check What's Using the Port

Find which process is using the port:

```bash
# On macOS/Linux
lsof -i :9095
lsof -i :3150
lsof -i :5432

# Or use netstat
netstat -an | grep -E ':(9095|3150|5432)'
```

#### Option 3: Kill the Conflicting Process

If you want to free up the port (use with caution):
```bash
# Find the process ID (PID)
lsof -i :9095

# Kill the process
kill -9 <PID>
```

#### Option 4: Use Make Command to Check Ports

```bash
make check-ports
```

This will show which default ports are in use and which are available.

---

## Database Issues

### Problem: Database Connection Failed

**Symptoms:**
- Backend logs show "could not connect to server"
- Backend health check fails
- Migration commands fail

**Solutions:**

1. **Check if database is running:**
```bash
docker-compose ps
```

2. **View database logs:**
```bash
docker-compose logs db
```

3. **Restart database service:**
```bash
docker-compose restart db
```

4. **Reset database completely:**
```bash
make db-reset
# Or manually:
docker-compose down -v
docker-compose up -d db
sleep 3
make migrate
```

### Problem: Database Migrations Not Applied

**Symptoms:**
- Backend fails with "relation does not exist"
- Tables are missing

**Solutions:**

1. **Check current migration status:**
```bash
cd backend
uv run alembic current
```

2. **Apply pending migrations:**
```bash
make migrate
# Or manually:
cd backend
uv run alembic upgrade head
```

3. **View migration history:**
```bash
cd backend
uv run alembic history
```

### Problem: Database Volume Corrupted

**Symptoms:**
- PostgreSQL won't start
- Database logs show corruption errors

**Solution:**

**⚠️ WARNING: This will delete all data**

```bash
# Stop services and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d db
make migrate
```

### Problem: Can't Connect to Database from Host

**Symptoms:**
- psql or database GUI tools can't connect
- Connection times out

**Solutions:**

1. **Check if database port is exposed:**
```bash
docker-compose ps
```
Look for `0.0.0.0:5432->5432/tcp`

2. **Verify database credentials:**
```bash
# Default credentials (check .env for custom values)
Host: localhost
Port: 5432
User: app
Password: app
Database: app
```

3. **Connect using docker-compose:**
```bash
make db-shell
# Or manually:
docker-compose exec db psql -U app -d app
```

---

## Docker Issues

### Problem: Docker Daemon Not Running

**Symptoms:**
- "Cannot connect to the Docker daemon"
- Docker commands fail

**Solutions:**

1. **Start Docker Desktop** (macOS/Windows)

2. **Check Docker status:**
```bash
docker ps
```

3. **Restart Docker service** (Linux):
```bash
sudo systemctl start docker
```

### Problem: Out of Disk Space

**Symptoms:**
- "no space left on device"
- Build fails
- Services won't start

**Solutions:**

1. **Clean up Docker resources:**
```bash
make clean
# Or manually:
docker-compose down -v
docker system prune -f
```

2. **Remove unused images:**
```bash
docker image prune -a
```

3. **Check disk usage:**
```bash
docker system df
```

### Problem: Docker Build Fails

**Symptoms:**
- "failed to build" error
- Dockerfile syntax errors

**Solutions:**

1. **Clean and rebuild:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

2. **Check Docker logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

3. **Rebuild specific service:**
```bash
make rebuild-backend
# Or manually:
docker-compose up --build backend
```

### Problem: Container Keeps Restarting

**Symptoms:**
- Service status shows "Restarting"
- Container exits immediately after starting

**Solutions:**

1. **Check container logs:**
```bash
docker-compose logs -f backend
```

2. **Check health status:**
```bash
docker-compose ps
```

3. **Inspect container:**
```bash
docker-compose exec backend /bin/sh
```

4. **Disable restart policy temporarily:**
Edit `docker-compose.yml` and comment out `restart: unless-stopped`

---

## Backend Issues

### Problem: Backend Won't Start

**Symptoms:**
- Backend container exits immediately
- Health check fails
- Port not accessible

**Solutions:**

1. **Check backend logs:**
```bash
docker-compose logs backend
make logs-backend
```

2. **Verify environment variables:**
```bash
docker-compose exec backend env | grep -E '(DATABASE_URL|AI_)'
```

3. **Check if dependencies are installed:**
```bash
docker-compose exec backend uv sync
```

4. **Rebuild backend:**
```bash
make rebuild-backend
```

### Problem: Import Errors or Module Not Found

**Symptoms:**
- "ModuleNotFoundError: No module named 'X'"
- Import fails

**Solutions:**

1. **Reinstall dependencies:**
```bash
cd backend
uv sync
```

2. **Clear Python cache:**
```bash
cd backend
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

3. **Rebuild Docker image:**
```bash
docker-compose build --no-cache backend
```

### Problem: AI Provider Configuration Errors

**Symptoms:**
- "AI_API_KEY environment variable is required"
- "Unsupported AI provider"

**Solutions:**

1. **Check AI provider configuration in `backend/.env`:**
```bash
cat backend/.env | grep AI_
```

2. **For development, use mock provider:**
```bash
# backend/.env
AI_PROVIDER=mock
```

3. **For production, set proper credentials:**
```bash
# backend/.env
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
```

See [AI_PROVIDERS.md](../template/backend/AI_PROVIDERS.md) for detailed configuration.

### Problem: API Endpoint Returns 500 Error

**Symptoms:**
- API calls fail with 500 Internal Server Error
- No clear error message

**Solutions:**

1. **Check backend logs for stack trace:**
```bash
docker-compose logs backend | tail -50
```

2. **Enable debug mode in `backend/.env`:**
```bash
DEBUG=true
```

3. **Test endpoint directly:**
```bash
curl -v http://localhost:9095/api/health
```

4. **Check database connection:**
```bash
docker-compose exec backend uv run python -c "from src.database import engine; print(engine)"
```

### Problem: Authentication Fails

**Symptoms:**
- Login returns 401 Unauthorized
- Token validation fails

**Solutions:**

1. **Check if user exists:**
```bash
make db-shell
SELECT * FROM users WHERE email = 'test@example.com';
```

2. **Verify password hashing:**
Ensure password is being hashed during registration.

3. **Check session table:**
```bash
make db-shell
SELECT * FROM sessions WHERE user_id = '<user_id>';
```

4. **Test auth flow:**
```bash
# Register
curl -X POST http://localhost:9095/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test"}'

# Login
curl -X POST http://localhost:9095/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

---

## Frontend Issues

### Problem: Frontend Won't Start

**Symptoms:**
- Frontend container exits
- Port 3150 not accessible

**Solutions:**

1. **Check frontend logs:**
```bash
docker-compose logs frontend
```

2. **Check if backend is healthy:**
```bash
curl http://localhost:9095/api/health
```

Frontend depends on backend being healthy.

3. **Rebuild frontend:**
```bash
docker-compose build --no-cache frontend
docker-compose up frontend
```

### Problem: Cannot Connect to Backend API

**Symptoms:**
- CORS errors
- Network errors in browser console
- API calls timeout

**Solutions:**

1. **Verify backend is running:**
```bash
curl http://localhost:9095/api/health
```

2. **Check CORS configuration in backend:**
Backend should allow requests from `http://localhost:3150`

3. **Check network configuration:**
```bash
docker-compose exec frontend ping backend
```

4. **Verify environment variables:**
Frontend should have correct backend URL in its environment.

### Problem: Hot Reload Not Working

**Symptoms:**
- Changes to code don't reflect in browser
- Need to manually refresh or restart

**Solutions:**

1. **Check volume mounts in `docker-compose.yml`:**
Ensure source code is mounted as a volume.

2. **Restart frontend service:**
```bash
docker-compose restart frontend
```

3. **Clear browser cache** and hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

---

## Migration Issues

### Problem: Migration Fails to Apply

**Symptoms:**
- `alembic upgrade head` fails
- Error during migration execution

**Solutions:**

1. **Check current migration status:**
```bash
cd backend
uv run alembic current
```

2. **View migration history:**
```bash
cd backend
uv run alembic history
```

3. **Rollback and retry:**
```bash
cd backend
uv run alembic downgrade -1
uv run alembic upgrade head
```

4. **Check database connection:**
```bash
docker-compose ps db
docker-compose logs db
```

### Problem: Auto-generated Migration is Wrong

**Symptoms:**
- Migration doesn't match your model changes
- Migration tries to drop tables unexpectedly

**Solutions:**

1. **Delete the bad migration file:**
```bash
cd backend/alembic/versions
rm <migration_file>.py
```

2. **Ensure models are imported in `env.py`:**
Check that all models are imported in `alembic/env.py`

3. **Regenerate migration:**
```bash
cd backend
uv run alembic revision --autogenerate -m "Your message"
```

4. **Manually edit migration file** if needed

### Problem: Migration Conflicts

**Symptoms:**
- Multiple migration heads
- "Multiple heads" error

**Solutions:**

1. **Check migration branches:**
```bash
cd backend
uv run alembic heads
```

2. **Merge heads:**
```bash
cd backend
uv run alembic merge -m "merge heads" <rev1> <rev2>
```

### Problem: Can't Rollback Migration

**Symptoms:**
- Downgrade fails
- Data loss concerns

**Solutions:**

1. **Check migration downgrade function:**
Open migration file and verify `downgrade()` is properly implemented

2. **Backup database first:**
```bash
docker-compose exec db pg_dump -U app app > backup.sql
```

3. **Force rollback with database reset:**
```bash
make db-reset
```

---

## Environment & Configuration

### Problem: Environment Variables Not Loading

**Symptoms:**
- Default values being used instead of .env values
- Configuration not taking effect

**Solutions:**

1. **Verify .env file exists:**
```bash
ls -la .env
ls -la backend/.env
```

2. **Check .env file format:**
- No spaces around `=`
- No quotes needed for simple values
- One variable per line

3. **Restart services after changing .env:**
```bash
docker-compose down
docker-compose up
```

4. **Check environment variables in container:**
```bash
docker-compose exec backend env
```

### Problem: Port Override Not Working

**Symptoms:**
- Services still use default ports after setting env vars

**Solutions:**

1. **Ensure .env is in template root:**
```bash
pwd  # Should be in template/
ls .env
```

2. **Verify .env syntax:**
```bash
# Correct
BACKEND_PORT=9096

# Wrong
BACKEND_PORT = 9096
BACKEND_PORT="9096"
```

3. **Restart Docker Compose:**
```bash
docker-compose down
docker-compose up
```

### Problem: Database Credentials Don't Match

**Symptoms:**
- Backend can't connect to database
- Authentication failed

**Solutions:**

1. **Check root .env for database credentials:**
```bash
cat .env | grep POSTGRES
```

2. **Ensure DATABASE_URL in docker-compose.yml matches:**
Should use same `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

3. **Reset with consistent credentials:**
```bash
docker-compose down -v
# Edit .env to ensure consistency
docker-compose up
```

---

## Development Tools

### Problem: Make Commands Not Working

**Symptoms:**
- `make: command not found`
- `make help` doesn't work

**Solutions:**

1. **Install make:**
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential

# Fedora
sudo dnf install make
```

2. **Use direct commands instead:**
All make commands are wrappers around docker-compose and other tools. See `Makefile` for the actual commands.

### Problem: uv Command Not Found (Local Development)

**Symptoms:**
- Can't run `uv sync`
- Backend commands fail

**Solutions:**

1. **Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Or use Docker instead:**
```bash
# Instead of: cd backend && uv run pytest
docker-compose exec backend pytest
```

### Problem: Can't Access Swagger/API Docs

**Symptoms:**
- `http://localhost:9095/docs` doesn't load
- 404 or connection refused

**Solutions:**

1. **Verify backend is running:**
```bash
docker-compose ps backend
```

2. **Check health endpoint:**
```bash
curl http://localhost:9095/api/health
```

3. **Check if port is correct:**
If you overrode ports, use your custom port:
```bash
# If BACKEND_PORT=9096 in .env
open http://localhost:9096/docs
```

4. **Use make command:**
```bash
make api-docs
```

### Problem: Tests Failing Locally

**Symptoms:**
- pytest fails
- Import errors in tests

**Solutions:**

1. **Ensure dependencies are installed:**
```bash
cd backend
uv sync
```

2. **Run tests with correct Python environment:**
```bash
cd backend
uv run pytest
```

3. **Check test database configuration:**
Tests should use a separate test database or in-memory database.

4. **Run tests in Docker:**
```bash
docker-compose exec backend pytest
```

---

## Quick Diagnostic Commands

Run these commands to get a quick overview of your system state:

```bash
# Check all services
docker-compose ps

# Check logs for errors
docker-compose logs --tail=50

# Check port availability
make check-ports

# Check database connection
docker-compose exec db psql -U app -d app -c "SELECT 1"

# Check backend health
curl http://localhost:9095/api/health

# Check migration status
docker-compose exec backend uv run alembic current

# Check environment variables
docker-compose exec backend env | grep -E '(DATABASE|AI_|BACKEND)'
```

---

## Getting Help

If you're still experiencing issues after trying these solutions:

1. **Check the logs** for detailed error messages:
```bash
docker-compose logs -f
```

2. **Review the documentation:**
- [README.md](../template/README.md) - General overview
- [ENV_STRATEGY.md](../template/ENV_STRATEGY.md) - Environment configuration
- [MIGRATIONS.md](../template/backend/MIGRATIONS.md) - Migration guide
- [AI_PROVIDERS.md](../template/backend/AI_PROVIDERS.md) - AI configuration

3. **Search for similar issues** in the project's issue tracker

4. **Provide detailed information** when asking for help:
- Error messages from logs
- Output of `docker-compose ps`
- Your .env configuration (without sensitive data)
- Steps to reproduce the issue
