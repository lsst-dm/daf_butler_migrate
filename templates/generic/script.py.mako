<%!
def dq(item):
    if isinstance(item, str):
        return f'"{item}"'
    elif isinstance(item, tuple):
        r = ", ".join(dq(i) for i in item)
        if len(item) == 1:
            r += ","
        return f"({r})"
    elif isinstance(item, (list, tuple)):
        r = ", ".join(dq(i) for i in item)
        return f"[{r}]"
    else:
        return item
%>\
<%
tree_name = config.attributes.get("tree_name", "")
new_version = config.attributes.get("new_version", "")
%>\
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import logging

import sqlalchemy as sa
from alembic import op

from lsst.daf.butler_migrate.migration_context import MigrationContext
${imports if imports else ""}
# revision identifiers, used by Alembic.
revision = ${dq(up_revision)}
down_revision = ${dq(down_revision)}
branch_labels = ${dq(branch_labels)}
depends_on = ${dq(depends_on)}

# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")

% if tree_name != "dimensions-config":
MANAGER_NAME = "Enter full manager class name here"
NEW_VERSION = "${new_version}"
OLD_VERSION = "Specify old version number here"
% endif


def upgrade() -> None:
    """Upgrade '...' tree from ... to ... (ticket ...).

    Summary of changes:
      - <Add summary of changes>.
    """
% if tree_name == "dimensions-config":
    ctx = MigrationContext()
    # Add code to upgrade the schema using `ctx` attributes.
    raise NotImplementedError()
% else:
    with MigrationContext(MANAGER_NAME, NEW_VERSION) as ctx:  # noqa: F841
        # Add code to downgrade the schema using `ctx` attributes.
        raise NotImplementedError()
% endif


def downgrade() -> None:
    """Undo changes applied in `upgrade`."""
% if tree_name == "dimensions-config":
    ctx = MigrationContext()
    # Add code to downgrade the schema using `ctx` attributes.
    raise NotImplementedError()
% else:
    with MigrationContext(MANAGER_NAME, OLD_VERSION) as ctx:  # noqa: F841
        # Add code to downgrade the schema using `ctx` attributes.
        raise NotImplementedError()
% endif
