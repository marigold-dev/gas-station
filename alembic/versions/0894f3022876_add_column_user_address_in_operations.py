"""add-column-user-address-in-operations

Revision ID: 0894f3022876
Revises: 899856207a89
Create Date: 2024-01-04 16:56:40.833512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0894f3022876"
down_revision: Union[str, None] = "899856207a89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("operations", sa.Column("user_address", sa.String()))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("operations", "user_address")
    # ### end Alembic commands ###
