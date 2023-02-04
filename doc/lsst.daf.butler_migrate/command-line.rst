##################
Command line tools
##################

Command line interface for migration tools is implemented as a subcommand of ``butler`` command.
The top-level subcommand name is ``butler migrate`` which in turn has few other subcommands.
The commands implemented by ``butler migrate`` are mostly wrappers for corresponding Alembic commands/scripts, which hide complexity of the Alembic configuration and Butler-specific knowledge.


There are two classes of ``migrate`` commands.
Commands from the first class work with migration scripts and revision trees, and do not need access to Butler repository.
These commands are:

- ``show-trees``
- ``show-history``
- ``add-tree``
- ``add-revision``

Commands from other class work with database and require a Butler repository:

- ``show-current``
- ``stamp``
- ``upgrade``
- ``downgrade``

There are also few commands that were added for specific cases, not generally useful:

- ``dump-schema``
- ``set-namespace``
- ``rewrite-sqlite-registry``

Sections below describe individual commands and their options.

.. note::

  Please note that documentation of the default values for some options may refer to a file path at a time of documentation generation, actual default paths will be different when CLI command are executed.


.. click:: lsst.daf.butler_migrate.cli.cmd:migrate
   :prog: butler migrate
   :show-nested:
