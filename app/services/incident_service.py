from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models.incident import Incident
from backend.app.core.config import settings
from backend.app.schemas.incident import (
    AnalystAction,
    IncidentCategoryDefinition,
    IncidentCreate,
    IncidentUploadResponse,
    IncidentRead,
)


CATEGORY_DEFINITIONS = [
    IncidentCategoryDefinition(
        category="Flooding",
        icon="≈",
        severityHint="Severe",
        note="Floodwater, backflow, or embankment stress",
    ),
    IncidentCategoryDefinition(
        category="Sewage Leakage",
        icon="◉",
        severityHint="Moderate",
        note="Drainage leakage or untreated discharge",
    ),
    IncidentCategoryDefinition(
        category="Dead Fish",
        icon="◌",
        severityHint="Moderate",
        note="Fish mortality, odor, or stagnant water distress",
    ),
    IncidentCategoryDefinition(
        category="Plastic Waste",
        icon="□",
        severityHint="Low",
        note="Floating litter, ghat accumulation, or bank dumping",
    ),
    IncidentCategoryDefinition(
        category="Illegal Sand Mining",
        icon="△",
        severityHint="Severe",
        note="Unauthorized extraction near sensitive reaches",
    ),
    IncidentCategoryDefinition(
        category="Riverbank Erosion",
        icon="∿",
        severityHint="Severe",
        note="Slope instability or active bank cutting",
    ),
    IncidentCategoryDefinition(
        category="Biodiversity Threat",
        icon="✧",
        severityHint="Moderate",
        note="Habitat disruption or protected species threat",
    ),
    IncidentCategoryDefinition(
        category="Other",
        icon="+",
        severityHint="Low",
        note="Other environmental monitoring report",
    ),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _ensure_media_directory() -> Path:
    media_directory = Path(settings.media_root)
    media_directory.mkdir(parents=True, exist_ok=True)

    seeded_asset = media_directory / "seed-land-1.png"
    source_asset = Path("public/land-1.png")
    if source_asset.exists() and not seeded_asset.exists():
        copyfile(source_asset, seeded_asset)

    return media_directory


async def save_incident_evidence(file: UploadFile) -> IncidentUploadResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are supported for incident evidence.",
        )

    media_directory = _ensure_media_directory()
    suffix = Path(file.filename or "evidence-image").suffix or ".jpg"
    stored_name = f"{uuid4().hex}{suffix}"
    destination = media_directory / stored_name
    content = await file.read()

    destination.write_bytes(content)

    return IncidentUploadResponse(
        id=f"evidence-{uuid4().hex[:8]}",
        name=file.filename or stored_name,
        previewUrl=f"/media/{stored_name}",
        mimeType=file.content_type,
        sizeKb=max(1, round(len(content) / 1024)),
    )


def _to_schema(incident: Incident) -> IncidentRead:
    reported_at = _as_utc(incident.reported_at)
    updated_at = _as_utc(incident.updated_at)

    return IncidentRead(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        category=incident.category,
        severity=incident.severity,
        district=incident.district,
        locality=incident.locality,
        coordinates={"latitude": incident.latitude, "longitude": incident.longitude},
        status=incident.status,
        reportedAt=reported_at.isoformat().replace("+00:00", "Z"),
        updatedAt=updated_at.isoformat().replace("+00:00", "Z"),
        sourceLabel=incident.source_label,
        reporterRole=incident.reporter_role,
        verificationStatus=incident.verification_status,
        analystSeverity=incident.analyst_severity,
        trustedReporter=incident.trusted_reporter,
        suspiciousActivity=incident.suspicious_activity,
        duplicateClusterId=incident.duplicate_cluster_id,
        evidence=incident.evidence,
        operationalNotes=incident.operational_notes,
    )


def list_incidents(db: Session) -> list[IncidentRead]:
    incidents = db.scalars(select(Incident).order_by(desc(Incident.reported_at))).all()
    return [_to_schema(incident) for incident in incidents]


def get_incident_by_id(db: Session, incident_id: str) -> Incident | None:
    return db.get(Incident, incident_id)


def create_incident(db: Session, payload: IncidentCreate) -> IncidentRead:
    now = _now()
    incident = Incident(
        id=f"incident-{payload.district.lower().replace(' ', '-')}-{uuid4().hex[:8]}",
        title=payload.title,
        description=payload.description,
        category=payload.category,
        severity=payload.severity,
        district=payload.district,
        locality=payload.locality,
        latitude=float(payload.latitude or 25.5941),
        longitude=float(payload.longitude or 85.1376),
        status="Reported",
        reported_at=now,
        updated_at=now,
        source_label="Citizen incident intake",
        reporter_role="Citizen",
        verification_status="Pending Verification",
        analyst_severity=None,
        trusted_reporter=False,
        suspicious_activity=False,
        duplicate_cluster_id=None,
        evidence=[item.model_dump() for item in payload.evidence],
        operational_notes=["Awaiting analyst triage"],
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return _to_schema(incident)


def update_incident_status(db: Session, incident: Incident, action: AnalystAction) -> IncidentRead:
    incident.updated_at = _now()

    if action == "verify":
        incident.verification_status = "Verified"
        incident.status = "Under Review"
        incident.analyst_severity = incident.analyst_severity or incident.severity
        incident.operational_notes = ["Analyst verification completed", *incident.operational_notes]
    elif action == "escalate":
        incident.verification_status = "Escalated"
        incident.status = "Escalated"
        incident.analyst_severity = "Severe"
        incident.operational_notes = [
            "Escalated into operational incident layer",
            *incident.operational_notes,
        ]
    elif action == "resolve":
        incident.verification_status = "Resolved"
        incident.status = "Resolved"
        incident.operational_notes = [
            "Resolution logged by district operations",
            *incident.operational_notes,
        ]
    else:
        incident.verification_status = "Rejected"
        incident.status = "Under Review"
        incident.operational_notes = ["Rejected during analyst review", *incident.operational_notes]

    db.add(incident)
    db.commit()
    db.refresh(incident)
    return _to_schema(incident)


def seed_incidents_if_empty() -> None:
    from backend.app.db.session import SessionLocal

    _ensure_media_directory()

    seed_items = [
        {
            "id": "incident-patna-sewage-001",
            "title": "Untreated drain outfall near Gandhi Ghat",
            "description": "Dark discharge observed entering the river edge during late-morning flow. Odor persists across the steps and near the storm drain mouth.",
            "category": "Sewage Leakage",
            "severity": "Moderate",
            "district": "Patna",
            "locality": "Gandhi Ghat",
            "latitude": 25.6138,
            "longitude": 85.1647,
            "status": "Under Review",
            "reported_at": datetime(2026, 5, 21, 9, 18, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 5, 21, 9, 42, tzinfo=timezone.utc),
            "source_label": "Citizen river watch intake",
            "reporter_role": "Citizen",
            "verification_status": "Under Analyst Review",
            "analyst_severity": "Moderate",
            "trusted_reporter": False,
            "suspicious_activity": False,
            "duplicate_cluster_id": "cluster-gandhi-ghat-sewage",
            "evidence": [
                {
                    "id": "evidence-patna-001",
                    "name": "ghat-outfall.jpg",
                    "previewUrl": "/media/seed-land-1.png",
                    "mimeType": "image/jpeg",
                    "sizeKb": 428,
                }
            ],
            "operational_notes": [
                "Ward observer verification requested",
                "Water quality field strip recommended within 2 hrs",
            ],
        },
        {
            "id": "incident-munger-erosion-002",
            "title": "Riverbank erosion advancing near lowland edge",
            "description": "Fresh slumping visible along embankment-adjacent soil face after overnight rainfall.",
            "category": "Riverbank Erosion",
            "severity": "Severe",
            "district": "Munger",
            "locality": "Kasim Bazar lowland edge",
            "latitude": 25.3819,
            "longitude": 86.4804,
            "status": "Escalated",
            "reported_at": datetime(2026, 5, 21, 7, 54, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 5, 21, 8, 35, tzinfo=timezone.utc),
            "source_label": "District operations field channel",
            "reporter_role": "District Operations",
            "verification_status": "Escalated",
            "analyst_severity": "Severe",
            "trusted_reporter": True,
            "suspicious_activity": False,
            "duplicate_cluster_id": None,
            "evidence": [],
            "operational_notes": [
                "Escalated to embankment monitoring unit",
                "Bank saturation linked to severe flood-watch corridor",
            ],
        },
        {
            "id": "incident-bhagalpur-biodiversity-003",
            "title": "Boat disturbance inside dolphin-sensitive stretch",
            "description": "High-speed vessel movement reported near active dolphin channel window.",
            "category": "Biodiversity Threat",
            "severity": "Moderate",
            "district": "Bhagalpur",
            "locality": "Vikramshila stretch",
            "latitude": 25.2473,
            "longitude": 86.9862,
            "status": "Reported",
            "reported_at": datetime(2026, 5, 21, 10, 5, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 5, 21, 10, 5, tzinfo=timezone.utc),
            "source_label": "Boat community intake",
            "reporter_role": "Environmental Monitor",
            "verification_status": "Pending Verification",
            "analyst_severity": None,
            "trusted_reporter": True,
            "suspicious_activity": False,
            "duplicate_cluster_id": None,
            "evidence": [],
            "operational_notes": ["Habitat patrol notification pending"],
        },
    ]

    db = SessionLocal()
    try:
        existing = db.scalar(select(Incident.id).limit(1))
        if existing is not None:
            return

        for item in seed_items:
            db.add(Incident(**item))

        db.commit()
    finally:
        db.close()
