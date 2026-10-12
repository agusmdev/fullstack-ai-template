"""Main CLI entrypoint for ai-fsr."""

from pathlib import Path
from typing import Annotated

import typer

from ai_fsr import __version__
from ai_fsr.init import init_project, normalize_project_name, validate_project_name

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


@app.command()
def init(
    project_name: Annotated[
        str,
        typer.Argument(
            help="Name of the project to create (will be normalized to kebab-case for directory)"
        ),
    ],
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
    - TanStack Start frontend (React Query, shadcn/ui)
    - PostgreSQL 18.1 via docker compose
    - Auth system (session-based)
    - AGENTS.md files and the project-standards skill for AI coding agents

    Example usage:
        ai-fsr init my-project
        ai-fsr init my-project --output-dir ./projects
        ai-fsr init my-project --git-init --install-deps
    """
    validation_errors = validate_project_name(project_name)
    if validation_errors:
        typer.echo(f"❌ Invalid project name: {', '.join(validation_errors)}")
        raise typer.Exit(1)

    normalized_name = normalize_project_name(project_name)
    project_path = output_dir / normalized_name

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
        typer.echo(f"   Git init: {git_init}")
        typer.echo(f"   Install deps: {install_deps}")
        typer.echo("")
        typer.echo("   Template files would be copied and substitutions applied.")
        raise typer.Exit()

    typer.echo(f"🚀 Initializing project: {normalized_name}")
    typer.echo(f"📁 Output directory: {project_path}")

    # Call the init module to copy template and apply substitutions
    success, message, modified_files, post_init_messages = init_project(
        project_name=normalized_name,
        target_dir=project_path,
        force=force,
        git_init=git_init,
        install_deps=install_deps,
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
