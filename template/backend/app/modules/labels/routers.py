"""Labels router — CRUD endpoints for Label entities."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.labels.dependencies import get_label_service
from app.modules.labels.filters import LabelFilter
from app.modules.labels.schemas import LabelCreate, LabelResponse, LabelUpdate
from app.modules.labels.service import LabelService
from app.user.auth import require_current_user_id

labels_router = APIRouter(
    prefix="/labels",
    tags=["labels"],
    dependencies=[Depends(require_current_user_id)],
)


@labels_router.get(
    "",
    response_description="List labels",
    status_code=status.HTTP_200_OK,
)
async def list_labels(
    pagination: Params = Depends(),
    label_filter: LabelFilter = Depends(),
    team_id: uuid.UUID | None = Query(default=None, description="Restrict to a team"),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: LabelService = Depends(get_label_service),
) -> Page[LabelResponse]:
    """List labels for the authenticated user's teams."""
    log_action("list")
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=label_filter,
        user_id=user_id,
        team_id=team_id,
    )
    return cast(
        "Page[LabelResponse]",
        Page[LabelResponse].model_validate(
            {
                "items": [
                    LabelResponse.model_validate(label) for label in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@labels_router.get(
    "/{label_id}",
    response_description="Get label by ID",
    status_code=status.HTTP_200_OK,
)
async def get_label(
    label_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: LabelService = Depends(get_label_service),
) -> LabelResponse:
    """Get a label by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(label_id, user_id=user_id)
    return LabelResponse.model_validate(result)


@labels_router.post(
    "",
    response_description="Create a new label",
    status_code=status.HTTP_201_CREATED,
)
async def create_label(
    label: LabelCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: LabelService = Depends(get_label_service),
) -> LabelResponse:
    """Create a new label (member or admin)."""
    log_action("create")
    result = await service.create(label, user_id=user_id)
    log_entity("label", result.id)
    return LabelResponse.model_validate(result)


@labels_router.patch(
    "/{label_id}",
    response_description="Update a label",
    status_code=status.HTTP_200_OK,
)
async def update_label(
    label_id: uuid.UUID,
    label: LabelUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: LabelService = Depends(get_label_service),
) -> LabelResponse:
    """Update an existing label (member or admin)."""
    log_action("update")
    log_entity("label", label_id)
    result = await service.update(label_id, label, user_id=user_id)
    return LabelResponse.model_validate(result)


@labels_router.delete(
    "/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a label",
)
async def delete_label(
    label_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: LabelService = Depends(get_label_service),
) -> None:
    """Delete a label by ID (member or admin)."""
    log_action("delete")
    log_entity("label", label_id)
    await service.delete(label_id, user_id=user_id)
