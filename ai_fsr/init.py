"""Init command implementation for ai-fsr CLI."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Final

# Default values used in the template
DEFAULT_PROJECT_NAME: Final = "app"
DEFAULT_POSTGRES_USER: Final = "app"
DEFAULT_POSTGRES_PASSWORD: Final = "app"
DEFAULT_POSTGRES_DB: Final = "app"

# Files that need variable substitution
# Key: file pattern (relative to template root)
# Value: list of (placeholder, replacement_func) tuples
SUBSTITUTION_FILES: Final = {
    ".env.example": [
        ("POSTGRES_DB=app", None),  # Will use formatted replacement
    ],
    "backend/pyproject.toml": [
        ('name = "app"', None),
    ],
    "frontend/package.json": [
        ('"name": "frontend"', None),  # Frontend name is different
    ],
}


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
        'myapp'
        >>> normalize_project_name("my-app")
        'my-app'
    """
    # Convert spaces and underscores to hyphens
    normalized = name.replace(" ", "-").replace("_", "-")
    # Convert camelCase to kebab-case
    normalized = re.sub(r'(?<!^)(?=[A-Z])', '-', normalized).lower()
    # Remove any non-alphanumeric characters except hyphens
    normalized = re.sub(r'[^a-z0-9-]', '', normalized)
    # Remove consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
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
        errors.append("Project name must contain at least one valid character (a-z, 0-9)")

    # Check for reserved names
    if normalized in {"node", "npm", "test", "package", "frontend", "backend"}:
        errors.append(f"'{normalized}' is a reserved name and cannot be used")

    return errors if errors else None


def get_template_dir() -> Path:
    """Get the template directory path.

    The template directory is located at the repository root.

    Returns:
        Path to the template directory
    """
    # The template is at the root of the repository
    # ai_fsr/__file__ resolves to repo_root/ai_fsr/init.py when installed
    current_file = Path(__file__).resolve()

    # ai_fsr is a direct child of repo root (e.g., open-fullstack-template/ai_fsr/)
    repo_root = current_file.parent.parent
    template_dir = repo_root / "template"

    if not template_dir.exists():
        # Fallback: search up the directory tree
        search_path = current_file
        for _ in range(5):
            if (search_path / "template").exists():
                return search_path / "template"
            search_path = search_path.parent
        raise RuntimeError(f"Template directory not found at: {template_dir}")

    return template_dir


def get_substitutions(project_name: str) -> dict[str, str]:
    """Get substitution mappings for the project.

    Args:
        project_name: Normalized project name

    Returns:
        Dictionary mapping placeholder values to replacements
    """
    return {
        DEFAULT_PROJECT_NAME: project_name,
        DEFAULT_POSTGRES_DB: project_name,
        DEFAULT_POSTGRES_USER: project_name,
        DEFAULT_POSTGRES_PASSWORD: project_name,
    }


def apply_substitutions(content: str, substitutions: dict[str, str]) -> str:
    """Apply variable substitutions to file content.

    Args:
        content: Original file content
        substitutions: Dictionary of substitutions to apply

    Returns:
        Content with substitutions applied
    """
    result = content
    for placeholder, replacement in substitutions.items():
        result = result.replace(placeholder, replacement)
    return result


def should_skip_copy(path: Path) -> bool:
    """Check if a file/directory should be skipped during copy.

    Args:
        path: Path to check

    Returns:
        True if should skip, False otherwise
    """
    # Skip node_modules (very large, not needed in template)
    if path.name == "node_modules":
        return True

    # Skip .output (build artifacts)
    if path.name == ".output":
        return True

    # Skip __pycache__ and other Python cache dirs
    if path.name == "__pycache__" or path.name.startswith(".pytest_cache"):
        return True

    # Skip .DS_Store on macOS
    if path.name == ".DS_Store":
        return True

    # Skip various cache/log directories
    if path.name in {".uv", ".ruff_cache", ".nitro", ".terraform"}:
        return True

    return False


def copy_template(
    template_dir: Path,
    target_dir: Path,
    project_name: str,
    substitutions: dict[str, str],
) -> list[str]:
    """Copy template directory to target with substitutions.

    Args:
        template_dir: Source template directory
        target_dir: Target directory to create
        project_name: Normalized project name
        substitutions: Variable substitutions to apply

    Returns:
        List of files that were modified with substitutions
    """
    modified_files = []

    # Define substitution patterns
    # Files that need specific replacements
    substitution_patterns = {
        ".env.example": {
            "POSTGRES_DB=app": f"POSTGRES_DB={project_name}",
            "POSTGRES_USER=app": f"POSTGRES_USER={project_name}",
            "POSTGRES_PASSWORD=app": f"POSTGRES_PASSWORD={project_name}",
        },
        "backend/pyproject.toml": {
            'name = "app"': f'name = "{project_name}"',
        },
        "docker-compose.yml": {
            "${POSTGRES_DB:-app}": f"${{POSTGRES_DB:-{project_name}}}",
            "${POSTGRES_USER:-app}": f"${{POSTGRES_USER:-{project_name}}}",
            "${POSTGRES_PASSWORD:-app}": f"${{POSTGRES_PASSWORD:-{project_name}}}",
        },
    }

    for item in template_dir.iterdir():
        if should_skip_copy(item):
            continue

        target_path = target_dir / item.name

        if item.is_dir():
            # Recursively copy directory
            shutil.copytree(item, target_path, ignore=shutil.ignore_patterns(
                "node_modules", ".output", "__pycache__", ".pytest_cache",
                ".ruff_cache", ".uv", ".DS_Store", ".nitro", ".terraform",
            ))
            # Apply substitutions in subdirectory files
            modified_files.extend(apply_substitutions_in_dir(
                target_path, project_name, substitution_patterns
            ))
        else:
            # Copy file and apply substitutions if needed
            shutil.copy2(item, target_path)
            modified_files.extend(apply_substitutions_to_file(
                target_path, project_name, substitution_patterns
            ))

    return modified_files


def apply_substitutions_in_dir(
    directory: Path,
    project_name: str,
    patterns: dict[str, dict[str, str]],
) -> list[str]:
    """Apply substitutions to all files in a directory recursively.

    Args:
        directory: Directory to process
        project_name: Project name for replacements
        patterns: Substitution patterns organized by file path

    Returns:
        List of files that were modified
    """
    modified_files = []

    for root, dirs, files in os.walk(directory):
        # Skip cache directories
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", "__pycache__", ".pytest_cache",
            ".ruff_cache", ".uv", ".nitro", ".terraform",
        }]

        for file in files:
            file_path = Path(root) / file
            modified_files.extend(apply_substitutions_to_file(
                file_path, project_name, patterns
            ))

    return modified_files


def apply_substitutions_to_file(
    file_path: Path,
    project_name: str,
    patterns: dict[str, dict[str, str]],
) -> list[str]:
    """Apply substitutions to a single file.

    Args:
        file_path: Path to the file
        project_name: Project name for replacements
        patterns: Substitution patterns organized by file path

    Returns:
        List containing file_path if modified, empty list otherwise
    """
    # Get relative path from project root
    rel_path = str(file_path)

    # Check if this file should have substitutions applied
    file_pattern = None
    for pattern in patterns:
        if pattern in rel_path:
            file_pattern = pattern
            break

    if not file_pattern:
        return []

    # Skip binary files
    if file_path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2"}:
        return []

    try:
        content = file_path.read_text()
        file_substitutions = patterns[file_pattern]

        new_content = content
        for placeholder, replacement in file_substitutions.items():
            if placeholder in new_content:
                new_content = new_content.replace(placeholder, replacement)

        if new_content != content:
            file_path.write_text(new_content)
            return [str(file_path)]
    except (UnicodeDecodeError, OSError):
        # Skip files that can't be read as text
        pass

    return []


def check_docker_installed() -> bool:
    """Check if Docker is installed and available.

    Returns:
        True if Docker is available, False otherwise
    """
    import shutil
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
    if not backend_dir.exists():
        return False, "Backend directory not found"

    # Check if uv is installed
    if not shutil.which("uv"):
        return False, "uv is not installed or not in PATH. Install from: https://docs.astral.sh/uv/"

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
    if not frontend_dir.exists():
        return True, "Frontend directory not found (skipped)"

    # Check if bun is installed
    if not shutil.which("bun"):
        return False, "bun is not installed or not in PATH. Install from: https://bun.sh/"

    success, stdout, stderr = run_command(["bun", "install"], frontend_dir)
    if success:
        return True, "Frontend dependencies installed via bun install"
    else:
        error_msg = stderr or stdout or "Unknown error"
        return False, f"Failed to install frontend dependencies: {error_msg}"


def init_project(
    project_name: str,
    target_dir: Path | None = None,
    force: bool = False,
    git_init: bool = False,
    install_backend: bool = False,
    install_frontend: bool = False,
) -> tuple[bool, str, list[str], list[str]]:
    """Initialize a new project from the template.

    Args:
        project_name: Raw project name (will be normalized)
        target_dir: Optional target directory (defaults to normalized project name)
        force: Skip directory existence check
        git_init: Initialize git repository after project creation
        install_backend: Install backend dependencies after project creation
        install_frontend: Install frontend dependencies after project creation

    Returns:
        Tuple of (success, message, list of modified files, list of post-init messages)
    """
    # Validate project name
    validation_errors = validate_project_name(project_name)
    if validation_errors:
        return False, f"Invalid project name: {', '.join(validation_errors)}", [], []

    # Normalize project name
    normalized_name = normalize_project_name(project_name)

    # Determine target directory
    if target_dir is None:
        target_dir = Path.cwd() / normalized_name
    elif not target_dir.is_absolute():
        target_dir = Path.cwd() / target_dir

    # Check if directory already exists
    if target_dir.exists() and not force:
        return False, f"Directory '{target_dir}' already exists. Use --force to override.", [], []

    # Check Docker installation
    if not check_docker_installed():
        return False, "Docker is not installed or not in PATH. Docker is required for generated projects.", [], []

    # Get template directory
    template_dir = get_template_dir()
    if not template_dir.exists():
        return False, f"Template directory not found: {template_dir}", [], []

    # Create target directory
    try:
        target_dir.mkdir(parents=True, exist_ok=force)
    except Exception as e:
        return False, f"Failed to create directory: {e}", [], []

    # Get substitutions
    substitutions = get_substitutions(normalized_name)

    # Copy template and apply substitutions
    try:
        modified_files = copy_template(
            template_dir=template_dir,
            target_dir=target_dir,
            project_name=normalized_name,
            substitutions=substitutions,
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

    if install_backend:
        success, message = install_backend_deps(target_dir)
        if success:
            post_init_messages.append(f"✓ {message}")
        else:
            post_init_messages.append(f"✗ {message}")

    if install_frontend:
        success, message = install_frontend_deps(target_dir)
        if success:
            post_init_messages.append(f"✓ {message}")
        else:
            post_init_messages.append(f"✗ {message}")

    success_msg = f"""Project '{normalized_name}' created successfully at: {target_dir}

Next steps:
  cd {normalized_name}
  cp .env.example .env
  docker-compose up -d

The application will be available at:
  - Backend API: http://localhost:9095
  - Frontend: http://localhost:3150
  - API Docs: http://localhost:9095/docs
"""

    return True, success_msg, modified_files, post_init_messages
