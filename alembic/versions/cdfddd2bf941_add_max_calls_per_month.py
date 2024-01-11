"""add-max-calls-per-month

Revision ID: cdfddd2bf941
Revises:
Create Date: 2023-12-20 16:34:37.784566

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cdfddd2bf941"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("contracts", sa.Column("max_calls_per_month", sa.Integer))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("contracts", "max_calls_per_month")
    # ### end Alembic commands ###