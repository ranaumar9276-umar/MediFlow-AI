"""phase 1 - add waiting-time tracking columns to appointments

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-01 00:00:00

Additive-only migration: adds two nullable columns to the existing
`appointments` table so that real waiting-time analytics can be computed
(started_at - checked_in_at) once staff begin recording check-in/start
events. Existing rows are unaffected (both columns default to NULL).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "started_at")
    op.drop_column("appointments", "checked_in_at")
