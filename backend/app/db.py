from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings

from sqlalchemy.pool import NullPool

settings = get_settings()

connect_args: dict = {}
engine_kwargs: dict = {"pool_pre_ping": True}

if "pooler" in settings.database_url or "supabase" in settings.database_url or "neon" in settings.database_url:
    connect_args["statement_cache_size"] = 0
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def initialise_database() -> None:
    from app.models import Base

    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    await engine.dispose()
