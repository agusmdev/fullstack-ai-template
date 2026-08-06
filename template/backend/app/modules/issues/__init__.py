"""Issues module — the core Issue entity (hub of the data model).

Internal namespace package. Import symbols from their submodules directly, e.g.
``from app.modules.issues.models import Issue``. The ``__init__`` is intentionally
lightweight to avoid module-load circular imports with ``labels`` and ``teams``.
"""
