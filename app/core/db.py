# --- Импорт всех моделей, чтобы Alembic их видел ---
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()


# --- Асинхронный движок ---
engine = create_async_engine(
    settings.database_url.replace("postgresql+psycopg2", "postgresql+asyncpg"),
    echo=False,
    future=True,
)

# --- Асинхронная сессия ---
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# --- Зависимость для FastAPI ---
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
