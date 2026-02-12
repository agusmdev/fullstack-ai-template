"""Main CLI entrypoint for ai-fsr."""

from pathlib import Path
from typing import Annotated

import typer

from ai_fsr import __version__
from ai_fsr.init import init_project, normalize_project_name

app = typer.Typer(
    name="ai-fsr",
    help="AI Full-Stack Ready - Generate production-ready full-stack projects",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo(f"ai-fsr version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """AI Full-Stack Ready - Generate production-ready full-stack projects."""
    pass


# Note: normalize_project_name is imported from ai_fsr.init


@app.command()
def init(
    project_name: Annotated[
        str,
        typer.Argument(
            help="Name of the project to create (will be normalized to kebab-case for directory)"
        ),
    ],
    # Service Ports
    backend_port: Annotated[
        int,
        typer.Option(
            "--backend-port",
            help="Backend port (default: 9095)",
        ),
    ] = 9095,
    frontend_port: Annotated[
        int,
        typer.Option(
            "--frontend-port",
            help="Frontend port (default: 3150)",
        ),
    ] = 3150,
    db_port: Annotated[
        int,
        typer.Option(
            "--db-port",
            help="Database port (default: 5432)",
        ),
    ] = 5432,
    # Database Configuration
    db_user: Annotated[
        str,
        typer.Option(
            "--db-user",
            help="Database user (default: app)",
        ),
    ] = "app",
    db_password: Annotated[
        str,
        typer.Option(
            "--db-password",
            help="Database password (default: app)",
        ),
    ] = "app",
    db_name: Annotated[
        str,
        typer.Option(
            "--db-name",
            help="Database name (default: app)",
        ),
    ] = "app",
    # AI Provider Configuration
    ai_provider: Annotated[
        str,
        typer.Option(
            "--ai-provider",
            help="AI provider: openai, anthropic, azure, or mock (default: mock)",
        ),
    ] = "mock",
    ai_api_key: Annotated[
        str,
        typer.Option(
            "--ai-api-key",
            help='API key for AI provider (optional, can be set later via .env)',
        ),
    ] = "",
    ai_model: Annotated[
        str,
        typer.Option(
            "--ai-model",
            help='AI model to use (optional, has sensible defaults per provider)',
        ),
    ] = "",
    ai_azure_endpoint: Annotated[
        str,
        typer.Option(
            "--ai-azure-endpoint",
            help='Azure OpenAI endpoint (required only for azure provider)',
        ),
    ] = "",
    # Feature Flags
    skip_frontend: Annotated[
        bool,
        typer.Option(
            "--skip-frontend",
            help="Skip frontend scaffolding",
        ),
    ] = False,
    skip_docker: Annotated[
        bool,
        typer.Option(
            "--skip-docker",
            help="Skip docker-compose generation",
        ),
    ] = False,
    skip_tests: Annotated[
        bool,
        typer.Option(
            "--skip-tests",
            help="Skip test files",
        ),
    ] = False,
    # Output Options
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory (default: current directory)",
            resolve_path=True,
        ),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing directory",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be created without creating files",
        ),
    ] = False,
    # Post-init Options
    git_init: Annotated[
        bool,
        typer.Option(
            "--git-init",
            help="Initialize git repository after project creation",
        ),
    ] = False,
    install_deps: Annotated[
        bool,
        typer.Option(
            "--install-deps",
            help="Install dependencies (uv sync for backend, bun install for frontend)",
        ),
    ] = False,
) -> None:
    """Initialize a new full-stack project from the template.

    Creates a new project directory with:
    - FastAPI backend (async, 3-layer architecture)
    - TanStack Start frontend (client-only, React Query, shadcn/ui)
    - PostgreSQL 18.1 via docker-compose
    - Auth system (session-based)
    - AI integration (Instructor)
    - Comprehensive docs and .claude skills

    Example usage:
        ai-fsr init my-project
        ai-fsr init my-project --backend-port 8080 --frontend-port 3000
        ai-fsr init my-project --ai-provider openai --ai-api-key sk-xxx
        ai-fsr init my-project --skip-frontend --output-dir ./projects
        ai-fsr init my-project --git-init --install-deps
    """
    # Normalize project name
    normalized_name = normalize_project_name(project_name)
    project_path = output_dir / normalized_name

    # Validate AI provider
    valid_providers = {"openai", "anthropic", "azure", "mock"}
    if ai_provider not in valid_providers:
        typer.echo(f"❌ Invalid AI provider: {ai_provider}")
        typer.echo(f"   Valid providers: {', '.join(sorted(valid_providers))}")
        raise typer.Exit(1)

    # Validate Azure-specific requirements
    if ai_provider == "azure" and not ai_azure_endpoint:
        typer.echo("❌ --ai-azure-endpoint is required when using azure provider")
        raise typer.Exit(1)

    # Check if directory exists
    if project_path.exists():
        if not force:
            typer.echo(f"❌ Directory already exists: {project_path}")
            typer.echo("   Use --force to overwrite")
            raise typer.Exit(1)
        typer.echo(f"⚠️  Overwriting existing directory: {project_path}")

    # Dry run output
    if dry_run:
        typer.echo("🔍 Dry run - would create:")
        typer.echo(f"   Project: {normalized_name}")
        typer.echo(f"   Path: {project_path}")
        typer.echo(f"   Backend port: {backend_port}")
        typer.echo(f"   Frontend port: {frontend_port}")
        typer.echo(f"   DB port: {db_port}")
        typer.echo(f"   DB: {db_user}/{db_name}")
        typer.echo(f"   AI provider: {ai_provider}")
        typer.echo(f"   Skip frontend: {skip_frontend}")
        typer.echo(f"   Skip docker: {skip_docker}")
        typer.echo(f"   Skip tests: {skip_tests}")
        typer.echo(f"   Git init: {git_init}")
        typer.echo(f"   Install deps: {install_deps}")
        typer.echo("")
        typer.echo("   Template files would be copied and substitutions applied.")
        typer.echo("   Use --force to overwrite existing directory.")
        raise typer.Exit()

    # Note: The actual template copying and substitution will be implemented
    # in a separate task (open-fullstack-template-8rm)
    typer.echo(f"🚀 Initializing project: {normalized_name}")
    typer.echo(f"📁 Output directory: {project_path}")
    typer.echo("🔧 Configuration:")
    typer.echo(f"   Backend port: {backend_port}")
    typer.echo(f"   Frontend port: {frontend_port}")
    typer.echo(f"   DB port: {db_port}")
    typer.echo(f"   DB: {db_user}/{db_name}")
    typer.echo(f"   AI provider: {ai_provider}")
    if skip_frontend:
        typer.echo("   Frontend: skipped")
    if skip_docker:
        typer.echo("   Docker: skipped")
    if skip_tests:
        typer.echo("   Tests: skipped")

    # Call the init module to copy template and apply substitutions
    success, message, modified_files, post_init_messages = init_project(
        project_name=normalized_name,
        target_dir=project_path,
        force=force or dry_run,
        git_init=git_init,
        install_backend=install_deps,
        install_frontend=install_deps,
    )

    if success:
        typer.echo(message)
        if modified_files:
            typer.echo(f"✨ Applied substitutions to {len(modified_files)} file(s)")
        if post_init_messages:
            typer.echo("")
            typer.echo("Post-init steps:")
            for msg in post_init_messages:
                typer.echo(f"  {msg}")
    else:
        typer.echo(f"❌ {message}", err=True)
        raise typer.Exit(code=1)


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
