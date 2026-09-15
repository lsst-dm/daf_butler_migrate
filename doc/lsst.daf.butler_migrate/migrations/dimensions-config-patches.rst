########################################
Migrations for dimensions-config manager
########################################

The ``dimensions-config-patches`` is a special Alembic tree to apply patches to the schema tables controlled by dimensions configuration that do not fit into a regular history of dimension updates.
Schema upgrades in this tree are supposed to fix issues due to either incomplete migrations (when migration resulted in a schema that did not match schema created later from scratch) or additional optimizations, e.g. new indices that accelerate queries.

Like ``dimensions-config`` tree, this tree uses dimension namespace as the name of the manager (tree branch).
The only known dimension namespace at this point is ``daf_butler``.


dimensions-config-patches tree
==============================

Migration script: `8a1a1665cc96.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config-patches/8a1a1665cc96.py>`_

Creates the branch of ``dimensions-config-patches`` tree.
Same effect can be achieved by executing ``butler migrate stamp dimensions-config-patches``


daf_butler v6-patch1
====================

Migration script: `ffe757e1ab0f.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config-patches/ffe757e1ab0f.py>`_

This migration adds a foreign key to a ``visit`` table that refers ``day_obs`` table and a corresponding index.
This is needed for repositories that were migrated earlier from version 5 to 6 as migration script did not add that FK.
Repositories created from scratch with dimensions version 6 or later have that FK, this script does not change them.

Depends on: ``1fae088c80b6`` (migration that upgrades ``dimensions-config`` from version 5 to 6).
