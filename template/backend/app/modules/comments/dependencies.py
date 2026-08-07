"""Dependency factory functions for the Comment module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.comments.repository import CommentRepository
from app.modules.comments.service import CommentService
from app.modules.issues.repository import IssueRepository
from app.modules.teams.dependencies import get_team_service


def get_comment_service(
    repo: CommentRepository = Depends(get_repository(CommentRepository)),
    team_service=Depends(get_team_service),
    issue_repo: IssueRepository = Depends(get_repository(IssueRepository)),
) -> CommentService:
    return CommentService(repo=repo, team_service=team_service, issue_repo=issue_repo)
