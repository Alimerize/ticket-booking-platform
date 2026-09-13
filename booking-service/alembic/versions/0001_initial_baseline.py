"""initial baseline

Revision ID: 0001
Revises:
Create Date: 2026-09-13

Handles two scenarios:
  1. Fresh install  -> creates bookings table with full schema
  2. Existing install (pre-Alembic) -> aligns columns with models
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "bookings" not in tables:
        # Fresh install: create with full schema
        op.create_table(
            "bookings",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("seat_number", sa.String(), nullable=False),
            sa.Column(
                "is_confirmed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        op.create_index("ix_bookings_id", "bookings", ["id"])
        op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
        op.create_index("ix_bookings_event_name", "bookings", ["event_name"])
    else:
        # Existing install (pre-Alembic): align constraints with models
        op.execute(
            "UPDATE bookings SET is_confirmed = false "
            "WHERE is_confirmed IS NULL"
        )
        op.alter_column(
            "bookings", "user_id",
            existing_type=sa.Integer(), nullable=False,
        )
        op.alter_column(
            "bookings", "event_name",
            existing_type=sa.String(), nullable=False,
        )
        op.alter_column(
            "bookings", "seat_number",
            existing_type=sa.String(), nullable=False,
        )
        op.alter_column(
            "bookings", "is_confirmed",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )


def downgrade() -> None:
    op.drop_table("bookings")
