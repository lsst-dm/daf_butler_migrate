########################################
Migrations for dimensions-config manager
########################################

The ``dimensions-config`` is a special manager which does not have a corresponding Python implementation, but corresponds to the contents of the dimension configuration.
This configuration is stored in the ``config:dimensions.json`` key in ``butler_attributes``.
Different butler databases may have incompatible dimension configurations; to distinguish them the ``namespace`` key in the configuration defines a unique name for that configuration.
This namespace is used for revision branches in ``dimensions-config`` revision tree.
A standard dimensions configuration shipped with ``daf_butler`` defines its namespace as "daf_butler".

Migration scripts in ``daf_butler_migrate`` support


daf_butler 0 (from root)
========================

Migration script: `1601d5973bf8.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/f3bcee34f344.py>`_

Version 0 was the initial version of the dimensions configuration, and that version did not even have a ``namespace`` key.
The migration script is a placeholder; the migration methods are empty.


daf_butler 0 to 1
=================

Migration script: `380002bcbb26.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/380002bcbb26.py>`_

Changes in version 1:

- Add a ``namespace`` key to configuration with "daf_butler" as value.
- Add ``healpix`` to skypix configuration.

There is no actual changes to database schema, only configuration is updated.
Running this upgrade requires the ``--namespace=daf_butler`` option.


daf_butler 1 to 2
=================

Migration script: `bf6308af80aa.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/bf6308af80aa.py>`_

Changes in version 2:

- Updates related to visit system changes
- New ``visit_system_membership`` table and new columns in instrument, exposure and visit tables.

Running this upgrade requires the ``--options has_simulated=0`` (or ``1`` for simulated data) option.


daf_butler 2 to 3
=================

Migration script: `c5ae3a2cd7c2.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/c5ae3a2cd7c2.py>`_

Changes the size of the ``observation_reason`` column in visit and exposure tables from 32 characters to 68.


daf_butler 3 to 4
=================

Migration script: `9888256c6a18.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/9888256c6a18.py>`_

Does not change the schema, only updates the contents of ``config:dimensions.json``.
Three elements in dimensions configuration add ``populated_by: visit`` option.


daf_butler 4 to 5
=================

Migration script: `2a8a32e1bec3.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/2a8a32e1bec3.py>`_

Alters ``instrument`` table schema, changes ``name`` column size to 32 from 16.
Updates ``config:dimensions.json`` with a matching change to ``instrument`` element.

daf_butler 5 to 6
=================

Migration script: `1fae088c80b6.py  <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/1fae088c80b6.py>`_

Supports group and day_obs as dimensions.

- Add ``group`` table, and populate it based on the ``group_name`` field in the ``exposure`` table.
- Add ``day_obs`` table, and populate based on the ``day_obs`` field from the
  ``exposure`` table and timespan offsets from Butler ``Instrument`` classes.
- Rename ``group_name`` in the exposure table to ``group``.
- Update the ``exposure`` table so ``group`` and ``day_obs`` are foreign keys to the new tables.
- Remove ``group_id`` from ``exposure`` table.
- Update ``config:dimensions.json`` to universe 6.

daf_butler 6 to 7
=================

Migration script: `352c30854bb0.py  <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/352c30854bb0.py>`_

Adds ``can_see_sky`` column to the ``exposure`` table.
