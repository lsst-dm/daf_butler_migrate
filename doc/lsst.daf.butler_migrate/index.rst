.. py:currentmodule:: lsst.daf.butler_migrate

.. _lsst.daf.butler_migrate:

#######################
lsst.daf.butler_migrate
#######################

.. _lsst.daf.butler_migrate-using:

Using migration tools
=====================

This package provides tools for performing database schema migration on Butler registries.
Database migrations are defined as scripts executed by these tools, this package also serves as a repository for these scripts.

.. toctree::
   :maxdepth: 1

   concepts.rst
   command-line.rst
   migration-scripts.rst
   typical-tasks.rst
   common-migrations.rst

Migrations catalog
==================

Links below lead to the description of existing migration scripts for each of the manager types.

.. toctree::
   :maxdepth: 1

   migrations/collections.rst
   migrations/datasets.rst
   migrations/datastores.rst
   migrations/dimensions.rst
   migrations/dimensions-config.rst
   migrations/opaque.rst


Implementation details
======================

``daf_butler_migrate`` does not provide public API.
This package is also very special because it is supposed to work with database schemas created by different (even incompatible) releases.
Due to that it cannot depend directly on many features of ``daf_butler``, dependencies are limited to the most stable parts of its API.
A small subset of ``daf_butler`` API was re-implemented in this package to avoid dependency issues.

Even with the very limited dependencies it is not guaranteed that ``daf_butler_migrate`` will be completely backward compatible.
Migrating older registries may require use of older releases and older version of this package.
