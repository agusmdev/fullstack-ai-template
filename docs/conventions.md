# Code Conventions

This document defines the code style, formatting, and best practices for this project.

## Table of Contents

1. [Backend (Python/FastAPI)](#backend-pythonfastapi)
2. [Frontend (React/TypeScript)](#frontend-reacttypescript)
3. [Database](#database)
4. [Git & Version Control](#git--version-control)
5. [Testing](#testing)
6. [Documentation](#documentation)

---

## Backend (Python/FastAPI)

### Code Formatting

#### Ruff Configuration

The project uses **Ruff** for linting and formatting. Configuration is in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "B",     # flake8-bugbear
    "SIM",   # flake8-simplify
    "UP",    # pyupgrade
    "ASYNC", # flake8-async
    "S",     # flake8-bandit (security)
    "RUF",   # ruff-specific rules
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

**Key rules:**
- **Line length**: 88 characters (Black-compatible)
- **Quotes**: Double quotes (`"`)
- **Indentation**: 4 spaces
- **Import sorting**: Automatic via isort integration
- **Security checks**: Enabled via flake8-bandit

#### Running Ruff

```bash
# Format and lint (auto-fix)
uv run lint

# Check without fixing
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Type Checking

#### ty Configuration

The project uses **ty** (based on pyright) for type checking. Configuration in `pyproject.toml`:

```toml
[tool.ty.src]
root = "./src"
include = ["src", "tests"]

[tool.ty.environment]
python-version = "3.12"
```

#### Running Type Checks

```bash
# Type check the entire codebase
uv run typecheck

# Type check specific files
uv run ty src/app/models/user.py
```

#### Type Annotation Standards

**Always use type hints:**

```python
# Good - Full type annotations
async def get_user(user_id: UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Bad - No type hints
async def get_user(user_id):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

**Use modern type syntax (Python 3.12+):**

```python
# Good - Python 3.12+ union syntax
def get_item(id: UUID) -> Item | None: ...

# Bad - Old-style Optional
from typing import Optional
def get_item(id: UUID) -> Optional[Item]: ...
```

**Generic types for repositories and services:**

```python
from typing import Generic, TypeVar
from app.core.models import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")

class BaseRepository(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    async def create(self, obj_in: CreateSchemaT) -> ModelT: ...
```

### Naming Conventions

#### Files and Modules

- **Snake_case** for all Python files: `user_service.py`, `item_repository.py`
- **Private modules** prefixed with underscore: `_cli.py`, `_internal.py`
- **Test files** prefixed with `test_`: `test_user_service.py`

#### Classes

- **PascalCase** for all classes:
  ```python
  class User(BaseModel): ...
  class UserService(BaseService): ...
  class ItemRepository(PostgresRepository): ...
  class CreateUserRequest(BaseModel): ...
  ```

#### Functions and Variables

- **Snake_case** for functions, methods, and variables:
  ```python
  def get_active_session(token: str) -> Session | None: ...
  async def create_item(item_data: ItemCreate) -> Item: ...

  user_id = uuid4()
  session_factory = async_sessionmaker(...)
  ```

#### Constants

- **UPPER_SNAKE_CASE** for module-level constants:
  ```python
  DEFAULT_SESSION_EXPIRY = 24 * 60 * 60  # 24 hours
  MAX_PAGE_SIZE = 100
  DATABASE_URL = "postgresql+asyncpg://..."
  ```

#### Private Members

- **Single underscore prefix** for internal/private:
  ```python
  class ItemRepository:
      def _base_query(self) -> Select: ...  # Internal method

  _ph = PasswordHasher()  # Module-private variable
  ```

### Import Organization

Imports are automatically organized by Ruff (isort). Standard order:

```python
# 1. Standard library imports
import secrets
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

# 2. Third-party imports
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application imports
from app.common.dependencies import get_current_user
from app.common.exceptions import NotFoundError
from app.core.models import BaseModel as DBBaseModel
from app.models.user import User

# 4. TYPE_CHECKING imports (avoid circular imports)
if TYPE_CHECKING:
    from app.models.session import Session
```

### Docstrings

Use **Google-style docstrings** for modules, classes, and functions:

```python
def create_user(email: str, password: str) -> User:
    """Create a new user with hashed password.

    Args:
        email: User's email address (must be unique).
        password: Plain-text password (will be hashed with Argon2).

    Returns:
        Newly created User instance.

    Raises:
        ConflictError: If email already exists.
        ValidationError: If email format is invalid.
    """
    ...
```

**Docstring rules:**
- All public modules, classes, and functions must have docstrings
- Private/internal functions (`_name`) can omit docstrings if obvious
- Keep docstrings concise - one line for simple functions
- Use multi-line format for complex functions with Args/Returns/Raises

### Architecture Patterns

#### 3-Layer Pattern

All domain entities follow the 3-layer architecture:

```
models/{entity}.py              # SQLAlchemy model
models/{entity}_schemas.py      # Pydantic schemas (Create/Update/Response)
models/{entity}_repository.py   # Data access layer
models/{entity}_service.py      # Business logic layer
api/v1/{entity}/router.py       # HTTP endpoints
```

**Example - User domain:**
```
models/user.py
models/user_schemas.py
models/user_repository.py
models/user_service.py
api/v1/auth/register.py  # Uses UserService
api/v1/auth/login.py
```

#### Repository Pattern

All repositories inherit from `PostgresRepository`:

```python
from app.core.repositories.postgres import PostgresRepository
from app.models.item import Item
from app.models.item_schemas import ItemCreate, ItemUpdate, ItemFilter

class ItemRepository(PostgresRepository[Item, ItemCreate, ItemUpdate, ItemFilter]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Item)

    # Add entity-specific queries
    async def get_by_user(self, user_id: UUID) -> list[Item]:
        query = self._base_query().where(Item.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
```

**Repository rules:**
- Inherit from `PostgresRepository` for standard CRUD
- Use `_base_query()` to automatically filter soft-deleted records
- Never put business logic in repositories
- Only database operations (queries, inserts, updates, deletes)

#### Service Pattern

All services inherit from `BaseService`:

```python
from app.core.services.base import BaseService
from app.models.item import Item
from app.models.item_schemas import ItemCreate, ItemUpdate, ItemFilter

class ItemService(BaseService[Item, ItemCreate, ItemUpdate, ItemFilter]):
    def __init__(self, repository: ItemRepository):
        super().__init__(repository)

    # Override lifecycle hooks
    async def before_create(self, data: ItemCreate) -> Item:
        # Business logic before creation
        return Item(**data.model_dump())

    async def after_create(self, entity: Item) -> None:
        # Post-creation logic (logging, events, etc.)
        logger.info(f"Created item {entity.id}")

    # Custom business methods
    async def delete_item(self, item_id: UUID, user_id: UUID) -> None:
        item = await self.repository.get(item_id)
        if item.user_id != user_id:
            raise ForbiddenError("Not authorized")
        await self.repository.soft_delete(item_id)
```

**Service rules:**
- All business logic lives in services
- Authorization checks in services
- Use lifecycle hooks: `before_create`, `after_create`, `before_update`, `after_update`
- Raise domain exceptions (`NotFoundError`, `ForbiddenError`, etc.)
- Never access the database directly - use repository methods

#### Router Pattern

All routers use dependency injection:

```python
from fastapi import APIRouter, Depends
from app.common.dependencies import get_current_user, get_item_service
from app.models.user import User
from app.models.item_service import ItemService
from app.models.item_schemas import ItemCreate, ItemResponse

router = APIRouter()

@router.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_current_user),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    item = await item_service.create_item(item_data, current_user.id)
    return ItemResponse.model_validate(item)
```

**Router rules:**
- No business logic - delegate to services
- Use dependency injection for services and auth
- Return Pydantic response models
- Set appropriate status codes (201 for creation, 204 for deletion)
- Let exceptions bubble up to global handlers

### Exception Handling

Use custom exceptions from `common/exceptions.py`:

```python
from app.common.exceptions import NotFoundError, ForbiddenError, ConflictError

# Instead of:
if not user:
    return JSONResponse(status_code=404, content={"error": "User not found"})

# Do this:
if not user:
    raise NotFoundError(f"User {user_id} not found")
```

**Available exceptions:**
- `NotFoundError(detail)` → 404
- `BadRequestError(detail)` → 400
- `UnauthorizedError(detail)` → 401
- `ForbiddenError(detail)` → 403
- `ConflictError(detail)` → 409

### Async/Await

**Always use async for I/O operations:**

```python
# Good - Async all the way
async def get_items(user_id: UUID) -> list[Item]:
    result = await session.execute(
        select(Item).where(Item.user_id == user_id)
    )
    return list(result.scalars().all())

# Bad - Blocking sync call
def get_items(user_id: UUID) -> list[Item]:
    result = session.execute(...)  # Blocks event loop!
    return list(result.scalars().all())
```

**Async context managers:**

```python
# Good
async with async_session_factory() as session:
    await session.execute(...)

# Bad
session = async_session_factory()
await session.execute(...)
session.close()  # Manual cleanup is error-prone
```

### Database Patterns

#### Models

All models inherit from `BaseModel`:

```python
from app.core.models import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class Item(BaseModel):
    __tablename__ = "items"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
```

**Model rules:**
- Use SQLAlchemy 2.0+ syntax (`Mapped`, `mapped_column`)
- All models automatically get: `id` (UUID), `created_at`, `updated_at`, `deleted_at`
- Set `nullable=False` explicitly (don't rely on defaults)
- Add indexes for foreign keys and frequently queried columns
- Use `String(length)` instead of `Text` for better indexing

#### Soft Deletes

All models support soft deletes via `SoftDeleteMixin`:

```python
# Soft delete (sets deleted_at)
await repository.soft_delete(item_id)

# Queries automatically exclude soft-deleted
items = await repository.get_all()  # Only non-deleted items

# Include deleted items (rare - only for admin views)
query = select(Item).where(Item.id == item_id)  # Manual query
result = await session.execute(query)
```

**Soft delete rules:**
- Use `repository.soft_delete()` instead of `repository.delete()`
- Repository's `_base_query()` automatically filters out deleted records
- Hard deletes are only for cleaning up test data or PII compliance

---

## Frontend (React/TypeScript)

### Technology Stack

- **Framework**: React 19 + TanStack Start (SSR)
- **Routing**: TanStack Router v1
- **State Management**: TanStack Query v5
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Forms**: React Hook Form + Zod validation
- **Build Tool**: Vite

### Code Formatting

Frontend uses **Prettier** (configured via VSCode/editor) and **TypeScript strict mode**.

**TypeScript configuration standards:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### Naming Conventions

#### Files and Folders

- **PascalCase** for component files: `Header.tsx`, `CreateItemDialog.tsx`
- **camelCase** for utilities and hooks: `api.ts`, `useItems.ts`, `utils.ts`
- **lowercase** for route files: `index.tsx`, `login.tsx`, `items.tsx`

#### Components

- **PascalCase** for all React components:
  ```tsx
  export function Header() { ... }
  export function CreateItemDialog() { ... }
  ```

#### Functions and Variables

- **camelCase** for functions, hooks, and variables:
  ```tsx
  function handleSubmit() { ... }
  const userId = user.id;
  const { data, isLoading } = useItems();
  ```

#### Types and Interfaces

- **PascalCase** for types and interfaces:
  ```tsx
  interface Item { ... }
  type CreateItemRequest = { ... }
  ```

### Component Structure

**Functional components with hooks:**

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

interface HeaderProps {
  title: string;
  showLogo?: boolean;
}

export function Header({ title, showLogo = true }: HeaderProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { data: user } = useQuery({
    queryKey: ["user", "me"],
    queryFn: fetchCurrentUser,
  });

  return (
    <header className="flex items-center justify-between">
      {showLogo && <Logo />}
      <h1>{title}</h1>
    </header>
  );
}
```

**Component rules:**
- Use named exports (not default exports)
- Props interface above component
- Extract complex logic into custom hooks
- Keep components under 200 lines (split if larger)

### State Management

#### TanStack Query for Server State

```tsx
// hooks/useItems.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useItems() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["items"],
    queryFn: () => api.get("/items"),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateItemRequest) => api.post("/items", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });

  return {
    items: query.data,
    isLoading: query.isLoading,
    createItem: createMutation.mutate,
  };
}
```

**Query rules:**
- Use TanStack Query for all server state
- Define query keys at the top of hooks
- Invalidate queries after mutations
- Use optimistic updates for better UX

#### useState for UI State

```tsx
// Local component state only
const [isDialogOpen, setIsDialogOpen] = useState(false);
const [selectedId, setSelectedId] = useState<string | null>(null);
```

### Styling Conventions

#### Tailwind CSS

Use **utility-first approach** with Tailwind:

```tsx
// Good - Utility classes
<button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
  Submit
</button>

// Bad - Inline styles
<button style={{ padding: "0.5rem 1rem", backgroundColor: "blue" }}>
  Submit
</button>
```

**Class organization:**
1. Layout (flex, grid, position)
2. Sizing (w-, h-, p-, m-)
3. Typography (text-, font-)
4. Colors (bg-, text-, border-)
5. States (hover:, focus:, active:)

#### Component Variants with CVA

Use `class-variance-authority` for component variants:

```tsx
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-white hover:bg-primary/90",
        outline: "border border-input bg-background hover:bg-accent",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

### API Integration

All API calls go through `lib/api.ts`:

```tsx
// lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = localStorage.getItem("auth_token");

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, data: unknown) =>
    request<T>(url, { method: "POST", body: JSON.stringify(data) }),
  put: <T>(url: string, data: unknown) =>
    request<T>(url, { method: "PUT", body: JSON.stringify(data) }),
  delete: (url: string) =>
    request(url, { method: "DELETE" }),
};
```

---

## Database

### Naming Conventions

- **Table names**: Plural snake_case (`users`, `items`, `user_sessions`)
- **Column names**: Snake_case (`user_id`, `created_at`, `password_hash`)
- **Indexes**: `ix_{table}_{column}` (e.g., `ix_users_email`)
- **Foreign keys**: `fk_{table}_{ref_table}_{column}`

### Migration Standards

**Always use Alembic for schema changes:**

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Add items table"

# Review the generated migration file
# Edit if needed (autogenerate isn't perfect)

# Apply migration
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

**Migration best practices:**
- Never edit old migrations (create new ones instead)
- Test both `upgrade` and `downgrade` paths
- Include data migrations when needed (not just schema)
- Review autogenerated migrations before committing

---

## Git & Version Control

### Commit Messages

Follow **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling

**Examples:**
```
feat(auth): add session-based authentication

Implements user registration, login, and logout endpoints
using secure session tokens with 24-hour expiration.

Closes #42
```

```
fix(items): prevent users from deleting other users' items

Added authorization check in ItemService.delete_item to verify
ownership before allowing deletion.
```

### Branch Naming

- `main` - Production-ready code
- `feature/short-description` - New features
- `fix/short-description` - Bug fixes
- `docs/short-description` - Documentation updates
- `refactor/short-description` - Code refactoring

---

## Testing

### Backend Testing

Use **pytest** with **pytest-asyncio**:

```python
# tests/test_user_service.py
import pytest
from app.models.user_schemas import UserCreate

@pytest.mark.asyncio
async def test_create_user(user_service):
    """Test user creation with password hashing."""
    user_data = UserCreate(
        email="test@example.com",
        password="SecureP@ssw0rd",
    )

    user = await user_service.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.password_hash != "SecureP@ssw0rd"  # Should be hashed
    assert user.verify_password("SecureP@ssw0rd")
```

**Test organization:**
```
tests/
├── conftest.py          # Shared fixtures
├── test_models/
│   ├── test_user.py
│   └── test_item.py
├── test_services/
│   ├── test_user_service.py
│   └── test_item_service.py
└── test_api/
    └── test_items.py
```

### Frontend Testing

Use **Vitest** with **React Testing Library**:

```tsx
// __tests__/Header.test.tsx
import { render, screen } from "@testing-library/react";
import { Header } from "@/components/Header";

describe("Header", () => {
  it("renders title correctly", () => {
    render(<Header title="Test App" />);
    expect(screen.getByText("Test App")).toBeInTheDocument();
  });
});
```

---

## Documentation

### Code Comments

**When to comment:**
- Complex algorithms or business logic
- Non-obvious workarounds
- Security considerations
- Performance optimizations

**When NOT to comment:**
- Obvious code (let the code speak for itself)
- Redundant docstrings (`# Set user_id` for `user.id = user_id`)

### README Files

Each major component should have a README:
- `template/backend/README.md` - Backend setup and development
- `template/frontend/README.md` - Frontend setup and development
- `docs/` - Project-wide documentation

---

## Summary

### Quick Reference

**Backend:**
- Format with Ruff: `uv run lint`
- Type check with ty: `uv run typecheck`
- Run tests: `uv run pytest`

**Frontend:**
- Start dev server: `npm run dev`
- Build: `npm run build`
- Run tests: `npm run test`

**Database:**
- Create migration: `uv run alembic revision --autogenerate -m "..."`
- Apply migrations: `uv run alembic upgrade head`

For more details, see:
- [Architecture Documentation](./architecture.md)
- [Troubleshooting Guide](./troubleshooting.md)
