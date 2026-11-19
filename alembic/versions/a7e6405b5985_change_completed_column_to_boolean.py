"""change completed column to boolean

Revision ID: a7e6405b5985
Revises: 7bbd7faf302f
Create Date: 2026-10-06 14:45:59.711347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7e6405b5985'
down_revision: Union[str, Sequence[str], None] = '7bbd7faf302f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "lessonprogresses",
        "completed",
        existing_type=sa.VARCHAR(),
        type_=sa.Boolean(),
        existing_nullable=False,
        postgresql_using="completed::boolean"
    )





def downgrade() -> None:
    """Downgrade schema."""
    pass