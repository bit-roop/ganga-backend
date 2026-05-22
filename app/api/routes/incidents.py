from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.incident import (
    IncidentActionRequest,
    IncidentActionResponse,
    IncidentCategoryDefinition,
    IncidentCreate,
    IncidentUploadResponse,
    IncidentRead,
)
from backend.app.services.incident_service import (
    CATEGORY_DEFINITIONS,
    create_incident,
    get_incident_by_id,
    list_incidents,
    save_incident_evidence,
    update_incident_status,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
def fetch_incidents(db: Session = Depends(get_db)) -> list[IncidentRead]:
    return list_incidents(db)


@router.get("/categories", response_model=list[IncidentCategoryDefinition])
def fetch_categories() -> list[IncidentCategoryDefinition]:
    return CATEGORY_DEFINITIONS


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
def submit_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentRead:
    return create_incident(db, payload)


@router.post("/uploads", response_model=IncidentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_incident_evidence(file: UploadFile = File(...)) -> IncidentUploadResponse:
    return await save_incident_evidence(file)


@router.patch("/{incident_id}", response_model=IncidentActionResponse)
def patch_incident(
    incident_id: str,
    payload: IncidentActionRequest,
    db: Session = Depends(get_db),
) -> IncidentActionResponse:
    incident = get_incident_by_id(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    updated_incident = update_incident_status(db, incident, payload.action)
    return IncidentActionResponse(incident=updated_incident)
