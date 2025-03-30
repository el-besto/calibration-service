# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
#
# engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
# SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
#
#
# def get_session() -> AsyncSession:
#     return SessionLocal()


from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# import sqlalchemy as sa # No longer needed if User model is removed
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Remove the synchronous User model definition
# class User(Base):
#     __tablename__ = "user"
#     id = sa.Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
#     name = sa.Column(sa.String, nullable=False)


class DBSettings(BaseSettings):
    """Parses DATABASE_URL variable from environment on instantiation"""

    database_url: str

    class Config:
        # Get the project root directory (where .env is located)
        env_file_path = Path(__file__).parent.parent.parent / ".env"
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields in environment variables


@lru_cache
def get_db_settings() -> DBSettings:
    """Returns the database settings, loaded from environment."""
    # Instantiate DBSettings here to load from environment
    return DBSettings()  # pyright: ignore [reportCallIssue]


@lru_cache
def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Creates and caches the async session maker."""
    settings = get_db_settings()
    engine = create_async_engine(settings.database_url, echo=True)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that provides an sqlalchemy async session."""
    async_session = get_async_session_maker()
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Function to create tables (useful for testing or initial setup)
# async def create_db_and_tables():
#     settings = get_db_settings()
#     engine = create_async_engine(settings.database_uri)
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     await engine.dispose()
