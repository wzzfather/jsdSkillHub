"""add skill enhanced fields

Revision ID: 20260512_02
Revises: 20260506_01
Create Date: 2026-05-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260512_02"
down_revision = "20260506_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("skills", sa.Column("namespace", sa.String(length=128), nullable=True))
    op.add_column(
        "skills",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=True,
        ),
    )
    op.add_column("skills", sa.Column("homepage_url", sa.String(length=1024), nullable=True))
    op.add_column("skills", sa.Column("repository_url", sa.String(length=1024), nullable=True))
    op.add_column("skills", sa.Column("icon_url", sa.String(length=1024), nullable=True))
    op.add_column(
        "skills",
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("skills", sa.Column("status_message", sa.Text(), nullable=True))
    op.add_column("skills", sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("skills", "deprecated_at")
    op.drop_column("skills", "status_message")
    op.drop_column("skills", "metadata_json")
    op.drop_column("skills", "icon_url")
    op.drop_column("skills", "repository_url")
    op.drop_column("skills", "homepage_url")
    op.drop_column("skills", "tags")
    op.drop_column("skills", "namespace")
