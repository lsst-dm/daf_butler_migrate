<%!
def dq(item):
    if isinstance(item, str):
        return f'"{item}"'
    elif isinstance(item, tuple):
        r = ", ".join(dq(i) for i in item)
        if len(item) == 1:
            r += ","
        return f"({r})"
    elif isinstance(item, list):
        r = ", ".join(dq(i) for i in item)
        return f"[{r}]"
    else:
        return item
%>\
<%
tree_name = config.attributes.get("tree_name", "")
new_tree = config.attributes.get("new_tree", False)
patch_tree = tree_name.endswith("-patches")
new_version = config.attributes.get("new_version", "")
manager_class = config.attributes.get("manager_class", "")
%>\
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
% if not new_tree:
import logging

import sqlalchemy as sa
from alembic import op

from lsst.daf.butler_migrate.migration_context import MigrationContext
% endif
${imports if imports else ""}
# revision identifiers, used by Alembic.
revision = ${dq(up_revision)}
down_revision = ${dq(down_revision)}
branch_labels = ${dq(branch_labels)}
depends_on = ${dq(depends_on)}

% if not new_tree:
# Logger name should start with lsst to work with butler logging option.
_LOG = logging.getLogger(f"lsst.{__name__}")

% if patch_tree:
TREE_NAME = "${tree_name}"
% endif
% if tree_name != "dimensions-config":
MANAGER_NAME = "[Fill package and module name here].${manager_class}"
NEW_VERSION = "${new_version}"
OLD_VERSION = "Specify old version number here"
% endif
% endif


def upgrade() -> None:
% if new_tree:
    """Create alembic entry, this empty migration is equivalent to executing
    `stamp` command.
    """
    pass
% else:
    """Upgrade '...' tree from ... to ... (ticket ...).

    Summary of changes:
      - <Add summary of changes>.
    """
% if tree_name == "dimensions-config":
    ctx = MigrationContext()
    # Add code to upgrade the schema using `ctx` attributes.
    raise NotImplementedError()
% elif patch_tree:
    with MigrationContext(MANAGER_NAME, NEW_VERSION, patch=True, tree_name=TREE_NAME) as ctx:  # noqa: F841
        # Add code to upgrade the schema using `ctx` attributes.
        raise NotImplementedError()
% else:
    with MigrationContext(MANAGER_NAME, NEW_VERSION) as ctx:  # noqa: F841
        # Add code to upgrade the schema using `ctx` attributes.
        raise NotImplementedError()
% endif
% endif


def downgrade() -> None:
% if new_tree:
    raise NotImplementedError()
% else:
    """Undo changes applied in `upgrade`."""
% if tree_name == "dimensions-config":
    ctx = MigrationContext()
    # Add code to downgrade the schema using `ctx` attributes.
    raise NotImplementedError()
% elif patch_tree:
    with MigrationContext(MANAGER_NAME, OLD_VERSION, patch=True, tree_name=TREE_NAME) as ctx:  # noqa: F841
        # Add code to downgrade the schema using `ctx` attributes.
        raise NotImplementedError()
% else:
    with MigrationContext(MANAGER_NAME, OLD_VERSION) as ctx:  # noqa: F841
        # Add code to downgrade the schema using `ctx` attributes.
        raise NotImplementedError()
% endif
% endif
