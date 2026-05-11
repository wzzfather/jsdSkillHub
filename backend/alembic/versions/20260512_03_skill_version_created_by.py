"""skill_versions.created_by

Revision ID: 20260512_03
Revises: 20260512_02
Create Date: 2026-05-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260512_03"
down_revision = "20260512_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "skill_versions",
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
    )
    op.create_foreign_key(
        "fk_skill_versions_created_by_users",
        "skill_versions",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_skill_versions_created_by_users", "skill_versions", type_="foreignkey")
    op.drop_column("skill_versions", "created_by")
