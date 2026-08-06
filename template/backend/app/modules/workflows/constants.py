"""Canonical default workflow states seeded for every new team.

Kept in its own module (no imports from ``teams``) so that ``teams.service`` can
import it without creating a load-time circular dependency.
"""

from app.modules.workflows.models import WorkflowStateType

# The canonical Linear-style workflow shipped with every new team.
# ``name`` is the display label; ``type`` is the behavioural enum.
# Ordered by ``position`` ascending.
DEFAULT_WORKFLOW_STATES: list[dict[str, object]] = [
    {
        "name": "Backlog",
        "type": WorkflowStateType.backlog,
        "position": 0.0,
        "color": "#bec2c8",
    },
    {
        "name": "Todo",
        "type": WorkflowStateType.unstarted,
        "position": 1.0,
        "color": "#95a2b3",
    },
    {
        "name": "In Progress",
        "type": WorkflowStateType.started,
        "position": 2.0,
        "color": "#f2c94c",
    },
    {
        "name": "Done",
        "type": WorkflowStateType.completed,
        "position": 3.0,
        "color": "#5e6ad2",
    },
    {
        "name": "Canceled",
        "type": WorkflowStateType.canceled,
        "position": 4.0,
        "color": "#95a2b3",
    },
]
