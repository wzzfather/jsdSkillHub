from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ScanResult(Base, TimestampMixin):
    __tablename__ = "scan_results"

    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    result: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    skill = relationship("Skill", back_populates="scan_results")
