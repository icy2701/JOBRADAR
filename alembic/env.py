from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Alembic Config object — provides access to values in alembic.ini
config = context.config

# Set up loggers from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models so Alembic can detect table changes for autogenerate
from src.models import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configures context with just a URL — no live DB connection needed.
    Used when you want to generate SQL scripts without running them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Reads DATABASE_URL from environment via settings — not from alembic.ini.
    This ensures Docker uses 'db' as the hostname (not 'localhost').
    """
    from src.config import settings

    configuration = config.get_section(config.config_ini_section, {})
    # Override alembic.ini URL with real DATABASE_URL from environment
    # In Docker: DATABASE_URL uses 'db' as hostname
    # Locally: DATABASE_URL uses 'localhost'
    # Same code works in both environments
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()