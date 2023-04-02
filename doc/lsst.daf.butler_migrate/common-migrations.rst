
##########################
Common migration operatios
##########################

This page collects recipes for common migration tasks happening in the migration scripts.

The most important thing to remember is that due to the very limited support of ALTER TABLE syntax in SQLite backend, many migration operations have to use Alembic `batch migrations`_.


Defining constraints for string columns
=======================================

In daf_butler code string columns are naturally defined with a corresponding size.
SQLAlchemy has a very relaxed type system, to help us detect possible violations we also define check constraints on string columns.
In registry it all is handled transparently, but in migration script we cannot use that logic, so we have to reproduce it locally.

An example to defining check constraint for a string column::

    with op.batch_alter_table(table_name, schema=schema) as batch_op:
        # ... add or re-define string column
        batch_op.alter_column(...)
        if context.get_context().bind.dialect.name == "sqlite":
            constraint_name = f"{table_name}_len_{column}"
            constraint = f'length("{column}")<={column_size} AND length("{column}")>=1'
            batch_op.drop_constraint(constraint_name)  # only if re-defining existing string column
            batch_op.create_check_constraint(constraint_name, sqlalchemy.text(constraint))


Changing column type
====================

When type of an existing column has to be changed the main complication is how to calculate and fill values for the column after type change.

If the value of the updated column does not need any change (e.g. extending the size of a string column), then it should be trivial (but check above recipe for updating constraint)::

    with op.batch_alter_table(table_name, schema=schema) as batch_op:
        batch_op.alter_column(column_name, type=...)

If the values for the updated column need to be calculated and it can be done at SQL level then it can be possible to add a new column, fill it with ne values, drop the existing column and rename added one::

    with op.batch_alter_table(table_name, schema=schema) as batch_op:
        new_name = column_name + "_tmp"
        batch_op.add_column(new_name, type=..., nullable=True)
        # ... fill new column
        batch_op.drop_column(column_name)
        # "nullable" should be set to a correct value.
        batch_op.alter_column(new_name, new_column_name=column_name, nullable=...)

More complicated case is when the column is referenced from other tables, its values have to be consistently replaced in all tables.
This can be done by creating a temporary table which maps old values to new ones and then creating new column in every table and filling it from that temporary table.

PostgreSQL has a special syntax for updating column values when altering column type, in some cases it may be more efficient to use this syntax than creating temporary table.
An example of this special syntax::

    op.alter_column(
        "dataset",
        "ingest_date",
        schema=schema,
        type_=column_type,
        server_default=server_default,
        postgresql_using="TO_TIMESTAMP(ingest_date / 1000000000.)",
    )


Updating butler_attributes
==========================

Each migration script is responsible for updating the version of its corresponding manager (if there is a corresponding manager) in the ``butler_attributes`` table.
Easiest way to do that is by using ``ButlerAttributes`` class, here is a standard way to do it::

    from alembic import op, context
    from lsst.daf.butler_migrate.butler_attributes import ButlerAttributes

    MANAGER = "lsst.daf.butler.registry.dimensions.static.StaticDimensionRecordStorageManager"

    def upgrade():
        # Do actual schema upgrade then update butler_attributes
        mig_context = context.get_context()
        schema = mig_context.version_table_schema
        attributes = ButlerAttributes(op.get_bind(), schema)
        attributes.update_manager_version(MANAGER, "6.0.1")

The ``update_manager_version`` method will raise an exception if manager is not defined in ``butler_attributes`` table.


.. _batch migrations: https://alembic.sqlalchemy.org/en/latest/batch.html
