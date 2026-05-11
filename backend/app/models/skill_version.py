from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SkillVersion(Base, TimestampMixin):
    __tablename__ = "skill_versions"

    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    package_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    skill = relationship("Skill", back_populates="versions")
