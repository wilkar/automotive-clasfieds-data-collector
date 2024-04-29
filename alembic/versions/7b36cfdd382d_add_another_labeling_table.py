"""add another labeling table

Revision ID: 7b36cfdd382d
Revises: 4d38b822a901
Create Date: 2024-04-01 20:17:08.290818

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b36cfdd382d"
down_revision: Union[str, None] = "4d38b822a901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suspicious_offers_v2",
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
