"""create_available_trainings_table

Revision ID: 05568a397772
Revises: f668219954b1
Create Date: 2025-10-26 15:57:34.130081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05568a397772'
down_revision: Union[str, Sequence[str], None] = 'e5bff5408fcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'available_trainings',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('training_id', sa.Integer, sa.ForeignKey('trainings.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('available_trainings')