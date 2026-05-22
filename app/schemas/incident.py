from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IncidentCategory = Literal[
    "Flooding",
    "Sewage Leakage",
    "Dead Fish",
    "Plastic Waste",
    "Illegal Sand Mining",
    "Riverbank Erosion",
    "Biodiversity Threat",
    "Other",
]
IncidentSeverity = Literal["Low", "Moderate", "Severe"]
IncidentStatus = Literal["Reported", "Under Review", "Escalated", "Resolved"]
IncidentRole = Literal["Citizen", "Analyst", "District Operations", "Environmental Monitor"]
VerificationStatus = Literal[
    "Pending Verification",
    "Under Analyst Review",
    "Verified",
    "Escalated",
    "Resolved",
    "Rejected",
]
AnalystAction = Literal["verify", "reject", "escalate", "resolve"]


class IncidentEvidence(BaseModel):
    id: str
    name: str
    previewUrl: str
    mimeType: str
    sizeKb: int


class IncidentCoordinates(BaseModel):
    latitude: float
    longitude: float


class IncidentRead(BaseModel):
    id: str
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    district: str
    locality: str
    coordinates: IncidentCoordinates
    status: IncidentStatus
    reportedAt: str
    updatedAt: str
    sourceLabel: str
    reporterRole: IncidentRole
    verificationStatus: VerificationStatus
    analystSeverity: IncidentSeverity | None = None
    trustedReporter: bool = False
    suspiciousActivity: bool = False
    duplicateClusterId: str | None = None
    evidence: list[IncidentEvidence]
    operationalNotes: list[str]

    model_config = ConfigDict(from_attributes=True)


class IncidentCreate(BaseModel):
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    district: str
    locality: str
    latitude: str
    longitude: str
    evidence: list[IncidentEvidence] = Field(default_factory=list)


class IncidentCategoryDefinition(BaseModel):
    category: IncidentCategory
    icon: str
    severityHint: IncidentSeverity
    note: str


class IncidentActionRequest(BaseModel):
    action: AnalystAction


class IncidentActionResponse(BaseModel):
    incident: IncidentRead


class IncidentUploadResponse(BaseModel):
    id: str
    name: str
    previewUrl: str
    mimeType: str
    sizeKb: int
