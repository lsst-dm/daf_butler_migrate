lsst-daf-butler-migrate v30.0.0 (2026-01-16)
============================================

New Features
------------

- Plugin discovery is now automated through Python entry points when using ``pip``.
  It is now an error if the ``DAF_BUTLER_PLUGINS`` environment variable is set for this package. (`DM-47143 <https://rubinobs.atlassian.net/browse/DM-47143>`_)
- Added migration script for MonolithicDatastoreRegistryBridgeManager 0.2.1.
  This migration reverses the order of columns in PK of `dataset_location_trash` table. (`DM-50958 <https://rubinobs.atlassian.net/browse/DM-50958>`_)
