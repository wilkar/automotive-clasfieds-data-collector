"""add foreign keys

Revision ID: 4d38b822a901
Revises: 4d8e2bbc5c90
Create Date: 2024-03-14 00:47:25.058933

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d38b822a901"
down_revision: Union[str, None] = "4d8e2bbc5c90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import sqlalchemy as sa

from alembic import op


def upgrade():
    # Add foreign key constraints
    op.create_foreign_key(
        "fk_offer_details_clasfieds_id",
        "offers_details",
        "offers_base",
        ["clasfieds_id"],
        ["clasfieds_id"],
    )
    op.create_foreign_key(
        "fk_offer_location_clasfieds_id",
        "offer_location",
        "offers_base",
        ["clasfieds_id"],
        ["clasfieds_id"],
    )


def downgrade():
    # Remove foreign key constraints
    op.drop_constraint(
        "fk_offer_details_clasfieds_id", "offers_details", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_offer_location_clasfieds_id", "offer_location", type_="foreignkey"
    )
