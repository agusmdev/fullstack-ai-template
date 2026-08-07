"""Module for including all the app's routers"""

from fastapi import APIRouter

from app.modules.cycles.routers import cycles_router
from app.modules.issue_dependencies.routers import issue_dependencies_router
from app.modules.issues.routers import issues_router
from app.modules.labels.routers import labels_router
from app.modules.projects.routers import projects_router
from app.modules.teams.routers import teams_router
from app.modules.views.routers import views_router
from app.modules.workflows.routers import workflow_states_router
from app.user.auth.routers import auth_router
from app.user.routers import user_router


def get_app_router() -> APIRouter:
    router = APIRouter()

    router.include_router(
        auth_router,
        prefix="/auth",
        tags=["auth"],
    )

    router.include_router(
        user_router,
        prefix="/users",
        tags=["users"],
    )

    router.include_router(teams_router)
    router.include_router(workflow_states_router)
    router.include_router(labels_router)
    router.include_router(issues_router)
    router.include_router(projects_router)
    router.include_router(cycles_router)
    router.include_router(views_router)
    router.include_router(issue_dependencies_router)

    return router
