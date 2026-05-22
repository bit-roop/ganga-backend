from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    locality: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_label: Mapped[str] = mapped_column(String(160), nullable=False)
    reporter_role: Mapped[str] = mapped_column(String(80), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    analyst_severity: Mapped[str | None] = mapped_column(String(24), nullable=True)
    trusted_reporter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suspicious_activity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_cluster_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    operational_notes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
