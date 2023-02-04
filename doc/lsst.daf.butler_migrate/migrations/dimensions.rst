#################################
Migrations for dimensions manager
#################################

The ``dimensions`` tree has migrations defined for all manager versions that have existed in our code; only a few of these migrations were actually implemented.


StaticDimensionRecordStorageManager 6.0.0 to 6.0.1
==================================================

Migration script: `1601d5973bf8.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions/1601d5973bf8.py>`_

Adds indices to few skypix overlap tables to accelerate queries.


StaticDimensionRecordStorageManager 6.0.1 to 6.0.2
==================================================

Migration script: `035dcf13ef18.py <https://github.com/lsst-dm/daf_butler_migrate/blob/main/migrations/dimensions/035dcf13ef18.py>`_

Adds ``NOT NULL`` constraints to identifying foreign key columns.
