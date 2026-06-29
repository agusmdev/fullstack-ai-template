# Dev Container

This dev container provides a complete development environment for the ai-fsr project.

## Features

- Python 3.12 with uv
- Node.js 20 with bun
- Docker-in-Docker for running docker-compose services
- VS Code extensions for Python, Ruff, Tailwind, Prettier, ESLint, Docker

## Usage

1. Open in VS Code with Dev Containers extension
2. Reopen in Container
3. Run `uv sync` to install Python dependencies
4. Run `cd template && docker compose up -d` to start services
