# This file is part of daf_butler_migrate.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Any

import click

from lsst.daf.butler.cli.opt import repo_argument
from lsst.daf.butler.cli.utils import ButlerCommand

from ... import script
from ..opt import (
    class_argument,
    dry_run_option,
    instrument_argument,
    manager_argument,
    mig_path_exist_option,
    mig_path_option,
    namespace_argument,
    namespace_option,
    one_shot_option,
    one_shot_tree_option,
    options_option,
    purge_option,
    revision_argument,
    sql_option,
    tables_argument,
    tree_name_argument,
    update_namespace_option,
    verbose_option,
    version_argument,
)


@click.group(short_help="Database schema migration commands.")
def migrate() -> None:
    """Set of command for managing and applying schema migrations."""
    pass


@migrate.command(short_help="Create new revision tree.", cls=ButlerCommand)
@mig_path_option
@one_shot_option
@tree_name_argument()
def add_tree(*args: Any, **kwargs: Any) -> None:
    """Create new revision tree for a specified manager type."""
    script.migrate_add_tree(*args, **kwargs)


@migrate.command(short_help="Show revision history.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
@tree_name_argument(required=False)
def show_history(*args: Any, **kwargs: Any) -> None:
    """Display revision history for a tree."""
    script.migrate_history(*args, **kwargs)


@migrate.command(short_help="Create migration script for a new revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_option
@tree_name_argument()
@class_argument()
@version_argument()
def add_revision(*args: Any, **kwargs: Any) -> None:
    """Create new revision."""
    script.migrate_revision(*args, **kwargs)


@migrate.command(short_help="Print a list of known revision trees.", cls=ButlerCommand)
@verbose_option
@mig_path_exist_option
@one_shot_option
def show_trees(*args: Any, **kwargs: Any) -> None:
    """Print a list of known revision trees (manager types)."""
    script.migrate_trees(*args, **kwargs)


@migrate.command(short_help="Stamp revision table with current registry versions.", cls=ButlerCommand)
@mig_path_exist_option
@purge_option
@namespace_option
@dry_run_option
@repo_argument(required=True)
@manager_argument()
def stamp(*args: Any, **kwargs: Any) -> None:
    """Stamp Alembic revision table (alembic_version) with current manager
    versions from butler_attributes.
    """
    script.migrate_stamp(*args, **kwargs)


@migrate.command(short_help="Display current revisions for a database.", cls=ButlerCommand)
@verbose_option
@click.option(
    "--butler",
    help=(
        "Display butler version numbers for managers from butler_attributes table. "
        "By default revisions from alembic_version table are displayed, if that table "
        "does not exist the output will be empty."
    ),
    is_flag=True,
)
@namespace_option
@mig_path_exist_option
@repo_argument(required=True)
def show_current(*args: Any, **kwargs: Any) -> None:
    """Display current revisions from either alembic_version or
    butler_attributes tables.
    """
    script.migrate_current(*args, **kwargs)


@migrate.command(short_help="Upgrade schema to a specified revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_tree_option
@sql_option
@namespace_option
@options_option
@repo_argument(required=True)
@revision_argument(required=True)
def upgrade(*args: Any, **kwargs: Any) -> None:
    """Upgrade schema to a specified revision."""
    script.migrate_upgrade(*args, **kwargs)


@migrate.command(short_help="Downgrade schema to a specified revision.", cls=ButlerCommand)
@mig_path_exist_option
@one_shot_tree_option
@sql_option
@namespace_option
@repo_argument(required=True)
@revision_argument(required=True)
def downgrade(*args: Any, **kwargs: Any) -> None:
    """Downgrade schema to a specified revision."""
    script.migrate_downgrade(*args, **kwargs)


@migrate.command(short_help="Upgrade a SQLite registry by rewriting it from scratch.", cls=ButlerCommand)
@click.argument("source", required=True)
def rewrite_sqlite_registry(**kwargs: Any) -> None:
    """Transfer registry information from one registry to a new registry.

    SOURCE is a URI to the Butler repository to be transferred.

    On completion a new registry will be written in its place and the
    old registry moved to a backup file.
    """
    script.rewrite_sqlite_registry(**kwargs)


@migrate.command(
    short_help="Add namespace attribute to the stored dimensions configuration.", cls=ButlerCommand
)
@update_namespace_option
@repo_argument(required=True)
@namespace_argument(required=False)
def set_namespace(**kwargs: Any) -> None:
    """Add or update namespace attribute to dimensions.json."""
    script.migrate_set_namespace(**kwargs)


@migrate.command(short_help="Dump schema of the database tables.", cls=ButlerCommand)
@repo_argument(required=True)
@tables_argument(required=False)
def dump_schema(**kwargs: Any) -> None:
    """Dump database schema in human-readable format."""
    script.migrate_dump_schema(**kwargs)


@migrate.command(
    short_help="Recalculate the day_obs values for exposures and visit for the given instrument.",
    cls=ButlerCommand,
)
@repo_argument(required=True)
@instrument_argument()
def update_day_obs(**kwargs: Any) -> None:
    """Update the day_obs values if needed."""
    script.update_day_obs(**kwargs)
