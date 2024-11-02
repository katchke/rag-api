"""Create example table

Revision ID: c1240fc5b104
Revises: 
Create Date: 2024-09-09 01:11:28.494257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1240fc5b104'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('examples',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('examples')