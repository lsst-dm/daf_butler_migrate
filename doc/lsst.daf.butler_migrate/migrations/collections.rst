##################################
Migrations for collections manager
##################################

The ``collections`` tree has a number of migrations scripts created but there is no actual migration implemented in any of them.
These scripts reflect the history of versions that existed in ``daf_butler`` code, but all production version of database should have the latest version of the schema.
The ``collections`` tree has two branches, ``collections-SynthIntKeyCollectionManager`` and ``collections-NameKeyCollectionManager``, for two separate implementations.
