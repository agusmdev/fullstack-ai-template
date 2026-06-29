#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to a JSON file.

Usage:
    cd template/backend && uv run python ../../scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path


def export_openapi() -> None:
    """Export OpenAPI schema from the FastAPI app."""
    try:
        from app.main import create_app
    except ImportError:
        print(
            "Error: Run this from the template/backend directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    app = create_app(add_sentry=False)
    schema = app.openapi()

    output_path = Path(__file__).parent.parent / "template" / "backend" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    export_openapi()
