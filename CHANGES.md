# Template Updates - Items Entity Integration

## Summary
Updated the template to work as a complete full-stack application with the "items" entity as the example. All demo content has been removed, and the template now focuses on the items CRUD functionality.

## Changes Made

### 1. Frontend API Endpoints Fixed
**File**: `template/frontend/src/lib/api-endpoints.ts`
- Changed `/api/v1/items` to `/items` to match backend routes
- Changed `/api/v1/items/{id}` to `/items/{id}`

### 2. Frontend Dockerfile Created
**File**: `template/frontend/Dockerfile`
- Created production-ready multi-stage Dockerfile for TanStack Start
- Builder stage installs dependencies and builds the application
- Production stage runs the built application
- Exposes port 3150
- Supports VITE_API_BASE_URL as build argument

**File**: `template/frontend/.dockerignore`
- Created to exclude unnecessary files from Docker build

### 3. Backend Port Configuration Fixed
**File**: `template/backend/Dockerfile`
- Changed exposed port from 10101 to 9095
- Updated uvicorn command to listen on port 9095
- Cleaned up commented code

### 4. Docker Compose Configuration Updated
**File**: `template/docker-compose.yml`
- Fixed backend healthcheck to use `/health` instead of `/api/health`
- Added build args for frontend to pass VITE_API_BASE_URL
- All services properly configured with health checks and dependencies

### 5. Homepage Updated
**File**: `template/frontend/src/routes/index.tsx`
- Removed TanStack demo content
- Now redirects to `/items` page for authenticated users
- Redirects to `/login` for unauthenticated users

### 6. Demo Routes Removed
**Deleted Files**:
- `template/frontend/src/routes/demo/ai-extract.tsx`
- `template/frontend/src/routes/demo/api.names.ts`
- `template/frontend/src/routes/demo/start.api-request.tsx`
- `template/frontend/src/routes/demo/start.css`
- `template/frontend/src/routes/demo/start.server-funcs.tsx`
- `template/frontend/src/routes/demo/start.ssr.data-only.tsx`
- `template/frontend/src/routes/demo/start.ssr.full-ssr.tsx`
- `template/frontend/src/routes/demo/start.ssr.index.tsx`
- `template/frontend/src/routes/demo/start.ssr.spa-mode.tsx`

### 7. TanStack Assets Removed
**Deleted Files**:
- `template/frontend/public/tanstack-circle-logo.png`
- `template/frontend/public/tanstack-word-logo-white.svg`
- `template/frontend/src/App.css`

## Verification

### Running the Template
```bash
cd template
docker compose up
```

### Expected Behavior
1. **Database** starts on port 5432
2. **Backend** starts on port 9095
   - Health check: http://localhost:9095/health
   - API docs: http://localhost:9095/docs
3. **Frontend** starts on port 3150
   - Homepage redirects to /login or /items
   - Items page shows CRUD interface for items

### Testing the Items Entity
1. Register a new user at http://localhost:3150/register
2. Login with credentials
3. Access items page at http://localhost:3150/items
4. Create, read, update, and delete items through the UI

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  Frontend   │────▶│   Backend    │────▶│ PostgreSQL │
│ (Port 3150) │     │ (Port 9095)  │     │ (Port 5432)│
└─────────────┘     └──────────────┘     └────────────┘
```

- **Frontend**: TanStack Start with React Query, shadcn/ui, authentication
- **Backend**: FastAPI with async SQLAlchemy, session-based auth
- **Database**: PostgreSQL 18.1 with Alembic migrations

## Items Entity Features

### Backend (`template/backend/app/modules/items/`)
- **Models**: SQLAlchemy model with UUID, timestamps, soft delete
- **Repository**: Base CRUD operations + custom `get_by_sku`
- **Service**: Business logic layer
- **Router**: RESTful endpoints (GET, POST, PATCH, DELETE)
- **Authentication**: All endpoints require Bearer token

### Frontend (`template/frontend/src/`)
- **Routes**: `/items` page with authentication guard
- **Hooks**: `useItems`, `useCreateItem`, `useUpdateItem`, `useDeleteItem`
- **Components**:
  - Items list with pagination and search
  - Create item dialog
  - Edit item dialog
  - Delete confirmation dialog
- **Features**:
  - Client-side search with debouncing
  - Optimistic updates
  - Error handling with toast notifications
  - Responsive design
  - Accessibility features (ARIA labels, keyboard navigation)

## Notes

- The template uses session-based authentication (not JWT)
- All API calls from frontend include Bearer token
- Frontend runs SSR with TanStack Start
- Backend uses 3-layer architecture (Model → Repository → Service → Router)
- Database migrations run automatically on backend startup
