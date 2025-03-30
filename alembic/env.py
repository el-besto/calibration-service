import asyncio
from logging.config import fileConfig

from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import Base from your models and DBSettings from your config
try:
    from src.config.database import get_db_settings
    from src.infrastructure.orm_models import Base
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Please ensure alembic commands are run from the project root directory")
    print("and PYTHONPATH is set correctly if needed.")
    raise

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get the database URL from environment using DBSettings."""
    try:
        settings = get_db_settings()
        return settings.database_url  # noqa: TRY300
    except Exception as e:
        print(f"Error loading database settings: {e}")
        raise ValueError(
            "Failed to load DATABASE_URL from environment. Ensure the variable is set (e.g., in .env or system env).",
        ) from e


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    loaded_db_url = get_database_url()
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = loaded_db_url
    connectable = create_async_engine(
        loaded_db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in a transaction."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
