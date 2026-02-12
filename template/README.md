# Full-Stack Application Template

A production-ready template for building full-stack applications with FastAPI backend, modern frontend, and PostgreSQL database.

## Quick Start

### Using Make (Recommended)

```bash
# View all available commands
make help

# Initial setup and start all services
make setup
make start

# Or start with fresh database
make dev-fresh

# Access the application
# Backend API: http://localhost:9095
# Frontend: http://localhost:3150
# API Docs: http://localhost:9095/docs
```

### Using Docker Compose Directly

```bash
# 1. Copy environment template (optional - defaults work out of the box)
cp .env.example .env

# 2. Start all services
docker-compose up

# 3. Access the application
# Backend API: http://localhost:9095
# Frontend: http://localhost:3150
# API Docs: http://localhost:9095/docs
```

That's it! The template uses sensible defaults that work without any configuration.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  Frontend   │────▶│   Backend    │────▶│ PostgreSQL │
│ (Port 3150) │     │ (Port 9095)  │     │ (Port 5432)│
└─────────────┘     └──────────────┘     └────────────┘
```

- **Backend**: FastAPI with async SQLAlchemy, Pydantic v2, structured 3-layer architecture
- **Frontend**: (To be scaffolded)
- **Database**: PostgreSQL 18.1 with automated migrations
- **Infrastructure**: Docker Compose with health checks

## Project Structure

```
template/
├── .env.example              # Docker Compose configuration
├── docker-compose.yml        # Service orchestration
├── ENV_STRATEGY.md          # Environment files documentation
├── backend/
│   ├── .env.example         # Backend app configuration
│   ├── pyproject.toml       # Python dependencies (uv)
│   ├── src/
│   │   ├── app.py          # FastAPI application factory
│   │   ├── core/           # Base models, repositories, services
│   │   ├── database/       # Database setup and sessions
│   │   └── ...
│   └── tests/
└── frontend/
    └── (to be scaffolded)
```

## Environment Configuration

See [ENV_STRATEGY.md](./ENV_STRATEGY.md) for detailed documentation.

### Default Configuration

The template works out of the box with these defaults:
- **Backend**: `http://localhost:9095`
- **Frontend**: `http://localhost:3150`
- **Database**: `postgresql://app:app@localhost:5432/app`

### Customizing Ports

#### Port Conflict Detection

If you encounter port conflicts when starting services, you'll see errors like:
```
Error starting userland proxy: listen tcp4 0.0.0.0:9095: bind: address already in use
```

#### Quick Fix

Create a `.env` file in the template root directory to override default ports:

```bash
# .env
BACKEND_PORT=9096    # Default: 9095
FRONTEND_PORT=3151   # Default: 3150
DB_PORT=5433         # Default: 5432
```

Then restart your services:
```bash
docker-compose down
docker-compose up
```

#### Checking for Port Conflicts

Before starting services, check if ports are available:

```bash
# Check if default ports are in use
lsof -i :9095  # Backend
lsof -i :3150  # Frontend
lsof -i :5432  # Database

# Or use netstat
netstat -an | grep -E ':(9095|3150|5432)'
```

#### Complete Override Example

If all default ports conflict with existing services:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your preferred ports
cat > .env << EOF
# Service Ports
BACKEND_PORT=8080
FRONTEND_PORT=3000
DB_PORT=5433

# Database Configuration
POSTGRES_USER=app
POSTGRES_PASSWORD=app
POSTGRES_DB=app
EOF

# Start services with custom ports
docker-compose up
```

Access your application at the new ports:
- Backend API: `http://localhost:8080`
- Frontend: `http://localhost:3000`
- Database: `localhost:5433`

**Note**: The `.env` file is ignored by git, so your local port overrides won't affect other developers.

## Development

### Using Make Commands

The project includes a comprehensive Makefile that simplifies all common development tasks:

```bash
# View all available commands
make help

# Start development environment
make dev                  # Start all services with logs
make dev-backend          # Start only backend and database
make dev-fresh            # Fresh start (clean, setup, start)

# Backend development
make backend-dev          # Run backend locally (outside Docker)
make backend-install      # Install dependencies
make backend-test         # Run tests
make backend-test-cov     # Run tests with coverage
make backend-format       # Format code
make backend-lint         # Lint code
make backend-lint-fix     # Lint and auto-fix
make backend-typecheck    # Type checking

# Database operations
make migrate              # Apply migrations
make migrate-create message="Add users table"  # Create new migration
make migrate-rollback     # Rollback last migration
make db-reset             # Reset database completely
make db-shell             # Open PostgreSQL shell

# Quality checks
make quality              # Run all quality checks (format, lint, typecheck)
make test                 # Run all tests
make lint-fix             # Lint and auto-fix all issues

# Docker operations
make up                   # Start services (foreground)
make start                # Start services (background)
make stop                 # Stop all services
make restart              # Restart all services
make logs                 # View all logs
make logs-backend         # View backend logs only
make clean                # Clean up containers and volumes

# Utilities
make check-ports          # Check if default ports are available
make api-docs             # Open API docs in browser
make api-health           # Check API health
```

### Backend Development (Manual Commands)

If you prefer not to use Make:

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 9095

# Run tests
uv run pytest

# Format and lint
uv run ruff format .
uv run ruff check . --fix
```

### Frontend Development

(To be documented when frontend is scaffolded)

## Backend Architecture

### 3-Layer Pattern

1. **Models** (`src/core/models/`) - SQLAlchemy ORM models with UUID primary keys
2. **Repositories** (`src/core/repositories/`) - Data access layer with CRUD operations
3. **Services** (`src/core/services/`) - Business logic layer
4. **Routers** (`src/api/`) - HTTP endpoints using services

### Key Features

- **Async SQLAlchemy 2.0** with type hints
- **Pydantic v2** for request/response validation
- **UUID primary keys** for all models
- **Soft delete** support via mixin
- **Timestamp tracking** (created_at, updated_at)
- **Repository pattern** for data access
- **Service layer** for business logic
- **Dependency injection** for database sessions

### Example: Creating a New Entity

```bash
# Use the fastapi-entity skill (if available)
# This creates model, schemas, repository, service, and router

# Manual approach:
# 1. Define model in src/core/models/
# 2. Create repository in src/core/repositories/
# 3. Create service in src/core/services/
# 4. Add router in src/api/
# 5. Generate migration: uv run alembic revision --autogenerate -m "Add entity"
```

## Database Migrations

```bash
cd backend

# Create a new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## Docker Commands

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (resets database)
docker-compose down -v

# Rebuild containers after code changes
docker-compose up --build
```

## Testing

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_example.py

# Run with verbose output
uv run pytest -v
```

## Code Quality

```bash
cd backend

# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check . --fix

# Type checking (if mypy is configured)
uv run mypy src/
```

## AI Provider Configuration

The backend includes support for structured LLM outputs via the `/api/v1/ai/extract` endpoint. You can configure different AI providers through environment variables.

### Supported Providers

- **mock** (default) - Returns fake data for development/testing
- **openai** - OpenAI GPT models
- **anthropic** - Anthropic Claude models
- **azure** - Azure OpenAI Service

### Configuration

Configure the AI provider in `backend/.env`:

```bash
# Provider Selection (required)
AI_PROVIDER=mock  # Options: mock, openai, anthropic, azure

# API Key (required for openai, anthropic, azure)
AI_API_KEY=your-api-key-here

# Model Selection (optional, provider-specific defaults used if not set)
AI_MODEL=gpt-4o-mini  # or claude-3-5-haiku-20241022, etc.

# Azure-specific (required only for azure provider)
AI_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
```

### Provider-Specific Configuration

#### OpenAI
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini  # Default if not specified
```

**Supported models**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, etc.

#### Anthropic
```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-...
AI_MODEL=claude-3-5-haiku-20241022  # Default if not specified
```

**Supported models**: `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, etc.

#### Azure OpenAI
```bash
AI_PROVIDER=azure
AI_API_KEY=your-azure-key
AI_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AI_MODEL=gpt-4o-mini  # Must match your Azure deployment
```

**Note**: The `AI_MODEL` must match your Azure OpenAI deployment name.

#### Mock Provider (Development)
```bash
AI_PROVIDER=mock
# No API key needed - returns fake data
```

The mock provider is perfect for:
- Local development without API costs
- Testing AI endpoints without external dependencies
- CI/CD pipelines

### Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **Azure**: https://portal.azure.com (create an OpenAI resource)

### Example API Usage

```bash
# Using the AI extract endpoint
curl -X POST http://localhost:9095/api/v1/ai/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "prompt": "Extract key information from: John Smith, age 30, lives in NYC",
    "response_model": {
      "name": "string",
      "age": "integer",
      "location": "string"
    }
  }'
```

### Error Handling

If the AI provider is misconfigured, you'll see helpful error messages:

- `AI_API_KEY environment variable is required for OpenAI provider`
- `AI_AZURE_ENDPOINT environment variable is required for Azure provider`
- `Unsupported AI provider: xyz. Supported providers: openai, anthropic, azure, mock`

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:9095/docs
- **ReDoc**: http://localhost:9095/redoc
- **OpenAPI JSON**: http://localhost:9095/openapi.json

### Authentication Endpoints

The template includes session-based authentication with the following endpoints:

#### POST /api/v1/auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "token": "session_token_here",
  "session": {
    "id": "uuid",
    "user_id": "uuid",
    "expires_at": "2026-01-29T10:00:00Z",
    "created_at": "2026-01-28T10:00:00Z"
  }
}
```

#### POST /api/v1/auth/login
Login with email and password to create a session.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "token": "session_token_here",
  "session": {
    "id": "uuid",
    "user_id": "uuid",
    "expires_at": "2026-01-29T10:00:00Z",
    "created_at": "2026-01-28T10:00:00Z"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid credentials"
}
```

#### GET /api/v1/auth/me
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer session_token_here
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2026-01-28T10:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

#### POST /api/v1/auth/logout
Logout and invalidate the current session.

**Headers:**
```
Authorization: Bearer session_token_here
```

**Response (204 No Content)**

### Items Endpoints (Protected)

All items endpoints require authentication via Bearer token in the Authorization header.

#### GET /api/v1/items
List all items for the current user.

**Headers:**
```
Authorization: Bearer session_token_here
```

**Response (200 OK):**
```json
[
  {
    "id": "uuid",
    "name": "My First Item",
    "description": "Item description",
    "user_id": "uuid",
    "created_at": "2026-01-28T10:00:00Z",
    "updated_at": "2026-01-28T10:00:00Z"
  }
]
```

#### POST /api/v1/items
Create a new item.

**Headers:**
```
Authorization: Bearer session_token_here
```

**Request:**
```json
{
  "name": "My New Item",
  "description": "Optional description"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "My New Item",
  "description": "Optional description",
  "user_id": "uuid",
  "created_at": "2026-01-28T10:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

#### GET /api/v1/items/{item_id}
Get a specific item by ID.

**Headers:**
```
Authorization: Bearer session_token_here
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "My Item",
  "description": "Item description",
  "user_id": "uuid",
  "created_at": "2026-01-28T10:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

#### PUT /api/v1/items/{item_id}
Update a specific item.

**Headers:**
```
Authorization: Bearer session_token_here
```

**Request:**
```json
{
  "name": "Updated Item Name",
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Updated Item Name",
  "description": "Updated description",
  "user_id": "uuid",
  "created_at": "2026-01-28T10:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

#### DELETE /api/v1/items/{item_id}
Delete a specific item (soft delete).

**Headers:**
```
Authorization: Bearer session_token_here
```

**Response (204 No Content)**

### API Usage Example

Here's a complete workflow using curl:

```bash
# 1. Register a new user
curl -X POST http://localhost:9095/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'

# Save the token from the response
TOKEN="session_token_from_response"

# 2. Create an item
curl -X POST http://localhost:9095/api/v1/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "My First Item",
    "description": "This is a test item"
  }'

# 3. List all items
curl http://localhost:9095/api/v1/items \
  -H "Authorization: Bearer $TOKEN"

# 4. Get current user info
curl http://localhost:9095/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 5. Logout
curl -X POST http://localhost:9095/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Port Already in Use

See the [Customizing Ports](#customizing-ports) section for detailed port override documentation.

**Quick fix options:**

1. **Override ports** (recommended):
```bash
# Create .env file with different ports
cp .env.example .env
# Edit BACKEND_PORT, FRONTEND_PORT, or DB_PORT
docker-compose down && docker-compose up
```

2. **Kill conflicting process**:
```bash
# Find process using port
lsof -i :9095

# Kill process (use with caution)
kill -9 <PID>
```

3. **Check what's using the port**:
```bash
# On macOS/Linux
lsof -i :9095
lsof -i :3150
lsof -i :5432

# Or use netstat
netstat -an | grep -E ':(9095|3150|5432)'
```

### Database Connection Issues
```bash
# Check database health
docker-compose ps

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d db
```

### Backend Won't Start
```bash
# Check backend logs
docker-compose logs backend

# Rebuild backend
docker-compose up --build backend

# Check if migrations are applied
docker-compose exec backend uv run alembic current
```

## Production Deployment

(To be documented)

Key considerations:
- Use production-grade secrets management
- Configure proper CORS origins
- Set DEBUG=false
- Use a production ASGI server (already using uvicorn)
- Set up database backups
- Configure logging and monitoring
- Use HTTPS/TLS

## Contributing

(To be documented)

## License

(To be specified)
