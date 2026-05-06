from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    skill = relationship("Skill", back_populates="reviews")
    reviewer = relationship("User")
