from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    author_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    package_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    offline_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True,
        server_default=text("'{}'"),
    )
    homepage_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author = relationship("User", back_populates="skills_authored")
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")
    scan_results = relationship("ScanResult", back_populates="skill", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="skill", cascade="all, delete-orphan")
