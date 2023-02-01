########################################
Migrations for dimensions-config manager
########################################

``dimensions-config`` is a special manager which does not have corresponding Python implementation, but corresponds to the contents of dimension configuration.
This configuration is stored in ``config:dimensions.json`` key in ``butler_attributes``.
Different butler databases may have incompatible dimension configurations, to distinguish them the ``namespace`` key in configuration defines a unique name for configuration.
This namespace is used for revision branches in ``dimensions-config`` revision tree.
A standard dimensions configuration shipped with ``daf_butler`` defines its namespace as "daf_butler".

Migration scripts in ``daf_butler_migrate`` support


daf_butler 0 (from root)
========================

Migration script: `1601d5973bf8.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/f3bcee34f344.py>`_

Version 0 was the initial version of dimensions configuration, and that version did not even have a ``namespace`` key.
The migration script is a placeholder, the migration methods are empty.


daf_butler 0 to 1
=================

Migration script: `380002bcbb26.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/380002bcbb26.py>`_

Changes in version 1:

- Add a ``namespace`` key to configuration with "daf_butler" as value.
- Add ``healpix`` to skypix configuration.

There is no actual changes to database schema, only configuration is updated.
Running this upgrade requires ``--namespace=daf_butler`` option.


daf_butler 1 to 2
=================

Migration script: `bf6308af80aa.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/bf6308af80aa.py>`_

Changes in version 2:

- Updates related to visit system changes
- New ``visit_system_membership`` table and new columns in instrument, exposure and visit tables.

Running this upgrade requires ``--options has_simulated=0`` (or ``1`` for simulated data) option.


daf_butler 2 to 3
=================

Migration script: `c5ae3a2cd7c2.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions-config/c5ae3a2cd7c2.py>`_

Changes the size of the ``observation_reason`` column in visit and exposure tables from 32 characters to 68.
