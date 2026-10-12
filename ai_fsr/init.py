"""Init command implementation for ai-fsr CLI."""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Final

# Local build output, caches and secrets that must never reach a generated
# project, even when the generator runs from a developer checkout.
IGNORED_NAMES: Final = (
    "*.db",
    "*.log",
    ".DS_Store",
    ".coverage",
    ".desloppify",
    ".idea",
    ".mypy_cache",
    ".nitro",
    ".output",
    ".pytest_cache",
    ".ruff_cache",
    ".tanstack",
    ".ty_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "blob-report",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "playwright-report",
    "scorecard.png",
    "test-results",
)

_ignore_names = shutil.ignore_patterns(*IGNORED_NAMES)


def ignore_local_files(directory: str, names: list[str]) -> set[str]:
    """Skip IGNORED_NAMES and every .env file except the .env.example templates."""
    ignored = _ignore_names(directory, names)
    return ignored | {n for n in names if n.startswith(".env") and n != ".env.example"}


def normalize_project_name(name: str) -> str:
    """Normalize project name to kebab-case.

    Args:
        name: The raw project name input

    Returns:
        Normalized kebab-case name

    Examples:
        >>> normalize_project_name("My App")
        'my-app'
        >>> normalize_project_name("my_app")
        'my-app'
        >>> normalize_project_name("MyApp")
        'my-app'
        >>> normalize_project_name("my-app")
        'my-app'
    """
    # Convert spaces and underscores to hyphens
    normalized = name.replace(" ", "-").replace("_", "-")
    # Convert camelCase to kebab-case
    normalized = re.sub(r"(?<!^)(?=[A-Z])", "-", normalized).lower()
    # Remove any non-alphanumeric characters except hyphens
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)
    # Remove consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip("-")
    return normalized


def validate_project_name(name: str) -> list[str] | None:
    """Validate project name.

    Args:
        name: The project name to validate

    Returns:
        List of error messages, or None if valid
    """
    errors = []

    if not name:
        errors.append("Project name cannot be empty")
        return errors

    normalized = normalize_project_name(name)
    if not normalized:
        errors.append(
            "Project name must contain at least one valid character (a-z, 0-9)"
        )

    # Check for reserved names
    if normalized in {"node", "npm", "test", "package", "frontend", "backend"}:
        errors.append(f"'{normalized}' is a reserved name and cannot be used")

    return errors if errors else None


def get_template_dir() -> Path:
    """Get the template directory path.

    The wheel ships the template inside the package (ai_fsr/template); a
    source checkout keeps it next to the package (repo_root/template).

    Returns:
        Path to the template directory
    """
    package_dir = Path(__file__).resolve().parent
    for candidate in (package_dir / "template", package_dir.parent / "template"):
        if candidate.is_dir():
            return candidate
    raise RuntimeError(f"Template directory not found next to: {package_dir}")


def get_substitutions(project_name: str) -> dict[str, dict[str, str]]:
    """Get the placeholder replacements for each templated file.

    Args:
        project_name: Normalized project name

    Returns:
        Mapping of file path (relative to the project root) to
        {placeholder: replacement}
    """
    backend_name = f'name = "{project_name}-backend"'
    return {
        ".env.example": {
            "POSTGRES_USER=app": f"POSTGRES_USER={project_name}",
            "POSTGRES_PASSWORD=app": f"POSTGRES_PASSWORD={project_name}",
            "POSTGRES_DB=app": f"POSTGRES_DB={project_name}",
        },
        "docker-compose.yml": {
            "${POSTGRES_USER:-app}": f"${{POSTGRES_USER:-{project_name}}}",
            "${POSTGRES_PASSWORD:-app}": f"${{POSTGRES_PASSWORD:-{project_name}}}",
            "${POSTGRES_DB:-app}": f"${{POSTGRES_DB:-{project_name}}}",
        },
        "backend/.env.example": {
            "postgresql://app:app@localhost:5432/app": (
                f"postgresql://{project_name}:{project_name}"
                f"@localhost:5432/{project_name}"
            ),
        },
        "backend/pyproject.toml": {
            'name = "backend-template"': backend_name,
        },
        "backend/uv.lock": {
            'name = "backend-template"': backend_name,
        },
    }


def apply_substitutions(
    target_dir: Path,
    substitutions: dict[str, dict[str, str]],
) -> list[str]:
    """Replace the template placeholders in the copied project.

    Args:
        target_dir: Root of the generated project
        substitutions: Replacements per relative file path

    Returns:
        List of files that were modified

    Raises:
        RuntimeError: If a placeholder is missing, so template drift fails
            loudly instead of shipping unsubstituted values.
    """
    modified_files = []

    for relative_path, replacements in substitutions.items():
        file_path = target_dir / relative_path
        content = file_path.read_text(encoding="utf-8")

        for placeholder, replacement in replacements.items():
            if placeholder not in content:
                raise RuntimeError(
                    f"Placeholder {placeholder!r} not found in {relative_path}"
                )
            content = content.replace(placeholder, replacement)

        file_path.write_text(content, encoding="utf-8")
        modified_files.append(str(file_path))

    return modified_files


def check_docker_installed() -> bool:
    """Check if Docker is installed and available.

    Returns:
        True if Docker is available, False otherwise
    """
    return shutil.which("docker") is not None


def run_command(
    command: list[str],
    cwd: Path,
) -> tuple[bool, str, str]:
    """Run a command in a subprocess.

    Args:
        command: Command and arguments to run
        cwd: Working directory for the command

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except Exception as e:
        return False, "", str(e)


def init_git_repo(target_dir: Path) -> tuple[bool, str]:
    """Initialize a git repository in the target directory.

    Args:
        target_dir: Directory to initialize git in

    Returns:
        Tuple of (success, message)
    """
    if not shutil.which("git"):
        return False, "git is not installed or not in PATH"

    success, stdout, stderr = run_command(["git", "init"], target_dir)
    if success:
        return True, "Git repository initialized"
    else:
        error_msg = stderr or stdout or "Unknown error"
        return False, f"Failed to initialize git: {error_msg}"


def install_backend_deps(target_dir: Path) -> tuple[bool, str]:
    """Install backend dependencies using uv sync.

    Args:
        target_dir: Project root directory

    Returns:
        Tuple of (success, message)
    """
    backend_dir = target_dir / "backend"

    # Check if uv is installed
    if not shutil.which("uv"):
        return (
            False,
            "uv is not installed or not in PATH. Install from: https://docs.astral.sh/uv/",
        )

    success, stdout, stderr = run_command(["uv", "sync"], backend_dir)
    if success:
        return True, "Backend dependencies installed via uv sync"
    else:
        error_msg = stderr or stdout or "Unknown error"
        return False, f"Failed to install backend dependencies: {error_msg}"


def install_frontend_deps(target_dir: Path) -> tuple[bool, str]:
    """Install frontend dependencies using bun install.

    Args:
        target_dir: Project root directory

    Returns:
        Tuple of (success, message)
    """
    frontend_dir = target_dir / "frontend"

    # Check if bun is installed
    if not shutil.which("bun"):
        return (
            False,
            "bun is not installed or not in PATH. Install from: https://bun.sh/",
        )

    success, stdout, stderr = run_command(["bun", "install"], frontend_dir)
    if success:
        return True, "Frontend dependencies installed via bun install"
    else:
        error_msg = stderr or stdout or "Unknown error"
        return False, f"Failed to install frontend dependencies: {error_msg}"


def init_project(
    project_name: str,
    target_dir: Path,
    force: bool = False,
    git_init: bool = False,
    install_deps: bool = False,
) -> tuple[bool, str, list[str], list[str]]:
    """Initialize a new project from the template.

    Args:
        project_name: Normalized, validated project name
        target_dir: Directory to create the project in
        force: Write into target_dir even if it already exists
        git_init: Initialize git repository after project creation
        install_deps: Install backend and frontend dependencies after project
            creation

    Returns:
        Tuple of (success, message, list of modified files, list of post-init messages)
    """
    # Check Docker installation
    if not check_docker_installed():
        return (
            False,
            "Docker is not installed or not in PATH. Docker is required for generated projects.",
            [],
            [],
        )

    # Copy template and apply substitutions
    try:
        shutil.copytree(
            get_template_dir(),
            target_dir,
            ignore=ignore_local_files,
            dirs_exist_ok=force,
        )
        modified_files = apply_substitutions(
            target_dir, get_substitutions(project_name)
        )
    except Exception as e:
        return False, f"Failed to copy template: {e}", [], []

    # Run post-init steps
    post_init_messages = []

    if git_init:
        success, message = init_git_repo(target_dir)
        if success:
            post_init_messages.append(f"✓ {message}")
        else:
            post_init_messages.append(f"✗ {message}")

    if install_deps:
        for install in (install_backend_deps, install_frontend_deps):
            success, message = install(target_dir)
            if success:
                post_init_messages.append(f"✓ {message}")
            else:
                post_init_messages.append(f"✗ {message}")

    success_msg = f"""Project '{project_name}' created successfully at: {target_dir}

Next steps:
  cd {target_dir}
  cp .env.example .env
  docker compose up -d

The application will be available at:
  - Backend API: http://localhost:9095
  - Frontend: http://localhost:3000
  - API Docs: http://localhost:9095/docs
"""

    return True, success_msg, modified_files, post_init_messages
