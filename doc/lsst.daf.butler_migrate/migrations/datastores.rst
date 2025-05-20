#################################
Migrations for datastores manager
#################################

The ``datastores`` tree has migrations defined for all manager versions that have existed in our code, but none of these migrations were actually implemented.

MonolithicDatastoreRegistryBridgeManager 0.2.0 to 0.2.1
=======================================================

Migration script: `a81dddabd837.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/datastores/a81dddabd837.py>`_

Reverses the order of columns in PK of ``dataset_location_trash`` table.
