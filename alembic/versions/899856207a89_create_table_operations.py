"""create-table-operations

Revision ID: 899856207a89
Revises: a6daf80cf2a0
Create Date: 2024-01-08 10:12:30.192936

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "899856207a89"
down_revision: Union[str, None] = "a6daf80cf2a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "cost",
            postgresql.INTEGER(),
            nullable=True,
        ),
        sa.Column(
            "contract_id", sa.UUID(), sa.ForeignKey("contracts.id"), nullable=True
        ),
        sa.Column(
            "entrypoint_id", sa.UUID(), sa.ForeignKey("entrypoints.id"), nullable=True
        ),
        sa.Column("hash", sa.TEXT(), nullable=True),
        sa.Column("status", sa.TEXT(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="operations_pkey"),
    )


def downgrade() -> None:
    op.drop_table("operations")
