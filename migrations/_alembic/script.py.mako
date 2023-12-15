<%!
def fmt(item):
    if item is None:
        return "None"
    elif isinstance(item, (list, tuple)):
        strings = [fmt(i) for i in item]
        return f'({", ".join(strings)},)'
    else:
        return f'"{item}"'
%>\
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import logging

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}
# revision identifiers, used by Alembic.
revision = ${up_revision | n,fmt}
down_revision = ${down_revision | n,fmt}
branch_labels = ${branch_labels | n,fmt}
depends_on = ${depends_on | n,fmt}

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")


def upgrade() -> None:
    """Perform schema upgrade."""
    ${upgrades if upgrades else "raise NotImplementedError()"}


def downgrade() -> None:
    """Perform schema downgrade."""
    ${downgrades if downgrades else "raise NotImplementedError()"}
