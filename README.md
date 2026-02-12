# AI Full-Stack Ready (ai-fsr)

A CLI generator for production-ready full-stack projects with FastAPI, TanStack Start, and PostgreSQL.

## Features

- **Backend**: FastAPI with async SQLAlchemy, 3-layer architecture (repo/service/router)
- **Frontend**: TanStack Start (client-only) with React Query and shadcn/ui
- **Database**: PostgreSQL 18.1 via docker-compose
- **Auth**: Session-based authentication with Bearer tokens
- **AI Integration**: Instructor for structured LLM interactions
- **Dev Tools**: uv, ruff, ty, bun, Tailwind CSS
- **AI-Ready**: Includes .claude/skills for AI-assisted development

## Installation

Run directly with uvx (no installation needed):

```bash
uvx --from git+https://github.com/your-org/open-fullstack-template ai-fsr init my-project
```

Or install locally for development:

```bash
# Clone the repository
git clone https://github.com/your-org/open-fullstack-template
cd open-fullstack-template

# Install with uv
uv sync

# Run the CLI
uv run ai-fsr --help
```

## Usage

### Create a New Project

```bash
ai-fsr init my-awesome-app
```

This will:
1. Create a new directory with your project name (normalized to kebab-case)
2. Copy the full-stack template
3. Apply project-specific substitutions
4. Set up docker-compose configuration

### Start Development

```bash
cd my-awesome-app
docker compose up -d
```

The following services will be available:
- **Backend**: http://localhost:9095/api
- **Frontend**: http://localhost:315
- **Database**: PostgreSQL on port 5432

## Project Structure

Generated projects include:

```
my-awesome-app/
├── backend/           # FastAPI application
│   ├── src/app/      # 3-layer architecture
│   ├── tests/        # pytest tests
│   └── pyproject.toml
├── frontend/         # TanStack Start application
│   ├── app/          # Routes and components
│   └── package.json
├── .claude/          # AI development skills
├── docs/             # Architecture and conventions
├── docker-compose.yml
└── README.md
```

## Documentation

- [Architecture](./docs/architecture.md) - System design and 3-layer architecture
- [Conventions](./docs/conventions.md) - Code style and best practices
- [Troubleshooting](./docs/troubleshooting.md) - Common issues and solutions

## Development

This is a generator repository. To work on the generator itself:

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .
```

The `template/` directory contains the source template that gets copied into new projects.

## Requirements

- Python 3.12+
- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- bun (for frontend package management)

## License

MIT
