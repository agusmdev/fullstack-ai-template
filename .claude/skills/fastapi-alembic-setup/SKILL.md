---
name: fastapi-alembic-setup
description: Configure Alembic for async SQLAlchemy migrations with PostgreSQL
---

# FastAPI Alembic Setup

## Overview

This skill covers setting up Alembic for database migrations with async SQLAlchemy 2.0 and PostgreSQL.

## Initialize Alembic

```bash
# Initialize alembic in the project root
uv run alembic init alembic
```

## Create alembic.ini

Create/update `alembic.ini` in project root:

```ini
# Alembic Configuration

[alembic]
# Path to migration scripts
script_location = alembic

# Template used to generate migration files
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(slug)s

# Set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# Truncate table name in version files
truncate_slug_length = 40

# Set to 'true' to allow .pyc and .pyo files without
# having their source .py files alongside them
# prepend_sys_path = .

# Timezone for file generation
timezone = UTC

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

## Create alembic/env.py

Replace `alembic/env.py` with:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.core.models import Base

# Import all models here to ensure they're registered with Base.metadata
# This is crucial for autogenerate to detect all tables
# from app.items.models import Item
# from app.users.models import User

# Alembic Config object
config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", str(settings.database_url))

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    allowing us to generate SQL scripts without a live database.
    
    Usage: alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with the given connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.
    
    Creates an async engine and runs migrations within a connection.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Uses asyncio to run migrations with a live database connection.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Create alembic/script.py.mako

Create/update `alembic/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade database schema."""
    ${downgrades if downgrades else "pass"}
```

## Create alembic/versions/.gitkeep

```bash
touch alembic/versions/.gitkeep
```

## Important: Register Models

In `alembic/env.py`, you MUST import all models for autogenerate to work:

```python
# Import all models to register them with Base.metadata
from app.items.models import Item  # noqa: F401
from app.users.models import User  # noqa: F401
from app.orders.models import Order  # noqa: F401
```

## Alembic Commands

### Create a New Migration

```bash
# Autogenerate migration from model changes
uv run alembic revision --autogenerate -m "add items table"

# Create empty migration
uv run alembic revision -m "add custom index"
```

### Run Migrations

```bash
# Upgrade to latest
uv run alembic upgrade head

# Upgrade one step
uv run alembic upgrade +1

# Upgrade to specific revision
uv run alembic upgrade abc123

# Generate SQL without running (offline mode)
uv run alembic upgrade head --sql
```

### Downgrade

```bash
# Downgrade one step
uv run alembic downgrade -1

# Downgrade to specific revision
uv run alembic downgrade abc123

# Downgrade to nothing (empty database)
uv run alembic downgrade base
```

### Check Status

```bash
# Show current revision
uv run alembic current

# Show migration history
uv run alembic history

# Show pending migrations
uv run alembic history --indicate-current
```

## Migration Best Practices

### 1. Review Autogenerated Migrations

Always review autogenerated migrations before running:

```python
# Check that it detected all changes
# Add any missing indexes or constraints
# Verify the downgrade path works
```

### 2. Add Data Migrations When Needed

```python
def upgrade() -> None:
    # Schema change
    op.add_column("items", sa.Column("status", sa.String(50), nullable=True))
    
    # Data migration
    op.execute("UPDATE items SET status = 'active' WHERE status IS NULL")
    
    # Make column non-nullable after data migration
    op.alter_column("items", "status", nullable=False)


def downgrade() -> None:
    op.drop_column("items", "status")
```

### 3. Use Batch Operations for SQLite Compatibility

```python
# If you need SQLite support (e.g., for tests)
with op.batch_alter_table("items") as batch_op:
    batch_op.add_column(sa.Column("new_col", sa.String(50)))
```

### 4. Handle Enum Types

```python
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # Create enum type
    status_enum = postgresql.ENUM("active", "inactive", "deleted", name="item_status")
    status_enum.create(op.get_bind())
    
    # Use enum in column
    op.add_column(
        "items",
        sa.Column("status", status_enum, nullable=False, server_default="active"),
    )


def downgrade() -> None:
    op.drop_column("items", "status")
    
    # Drop enum type
    status_enum = postgresql.ENUM("active", "inactive", "deleted", name="item_status")
    status_enum.drop(op.get_bind())
```

### 5. Add Indexes Explicitly

```python
def upgrade() -> None:
    # Create index
    op.create_index("ix_items_name", "items", ["name"])
    
    # Create unique index
    op.create_index("ix_items_email", "items", ["email"], unique=True)
    
    # Create composite index
    op.create_index("ix_items_status_category", "items", ["status", "category"])


def downgrade() -> None:
    op.drop_index("ix_items_status_category")
    op.drop_index("ix_items_email")
    op.drop_index("ix_items_name")
```

## Sample Migration File

```python
"""add items table

Revision ID: 20250105_120000_add_items
Revises: 
Create Date: 2025-01-05 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20250105_120000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index("ix_items_name", "items", ["name"])
    op.create_index("ix_items_deleted_at", "items", ["deleted_at"])


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index("ix_items_deleted_at")
    op.drop_index("ix_items_name")
    op.drop_table("items")
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Check current state
uv run alembic current

# Stamp the database to a revision without running migrations
uv run alembic stamp head
```

### Autogenerate Not Detecting Changes

1. Ensure all models are imported in `env.py`
2. Check that models inherit from `Base`
3. Verify `target_metadata = Base.metadata` is set

### Multiple Heads

```bash
# Show heads
uv run alembic heads

# Merge multiple heads
uv run alembic merge heads -m "merge branches"
```
