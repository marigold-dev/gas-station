"""add-default-value-max-calls-per-month

Revision ID: a6daf80cf2a0
Revises: cdfddd2bf941
Create Date: 2023-12-21 10:24:29.992446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a6daf80cf2a0"
down_revision: Union[str, None] = "cdfddd2bf941"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('UPDATE "contracts" SET "max_calls_per_month"=-1')


def downgrade() -> None:
    op.execute('UPDATE "contracts" SET "max_calls_per_month"=NULL')
