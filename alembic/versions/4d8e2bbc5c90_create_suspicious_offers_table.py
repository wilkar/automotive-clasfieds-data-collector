"""create suspicious offers table

Revision ID: 4d8e2bbc5c90
Revises: 1d20cf487633
Create Date: 2024-03-13 21:45:40.103640

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d8e2bbc5c90"
down_revision: Union[str, None] = "1d20cf487633"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suspicious_offers",
        sa.Column("id", sa.Integer, sa.Identity(start=1, cycle=True), primary_key=True),
        sa.Column("suspicious_clasfieds_id", sa.Integer, nullable=False),
        sa.Column("is_suspicious", sa.Boolean, nullable=False),
        sa.ForeignKeyConstraint(
            ["suspicious_clasfieds_id"],
            ["offers_base.clasfieds_id"],
            name="fk_suspicious_clasfieds_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("suspicious_offers")
