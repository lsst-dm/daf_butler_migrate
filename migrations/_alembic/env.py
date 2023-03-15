from alembic import context
from sqlalchemy import engine, engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    schema = config.get_section_option("daf_butler_migrate", "schema")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # executemany_* arguments are postgres-specific, need to check dialect
    url_str = config.get_main_option("sqlalchemy.url")
    assert url_str is not None, "Expect URL connection defined."
    url = engine.url.make_url(url_str)
    if url.get_dialect().name == "postgresql":
        kwargs = dict(
            executemany_mode="values",
            executemany_values_page_size=10000,
            executemany_batch_page_size=500,
        )
    else:
        kwargs = {}

    config_dict = config.get_section(config.config_ini_section)
    assert config_dict is not None, "Expect non-empty configuration"
    connectable = engine_from_config(config_dict, prefix="sqlalchemy.", poolclass=pool.NullPool, **kwargs)

    schema = config.get_section_option("daf_butler_migrate", "schema")
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
