# tests/conftest.py
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.main import app
from app.core.db import Base, get_async_db

# --- Тестовая база SQLite ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Создание/удаление таблиц ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- Фикстура сессии ---
@pytest_asyncio.fixture
async def session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session

# --- Подмена зависимости FastAPI ---
@pytest_asyncio.fixture(autouse=True)
async def override_db_dependency():
    async def _get_db_override():
        async with TestSessionLocal() as session:
            yield session
    app.dependency_overrides[get_async_db] = _get_db_override

# --- Фикстура клиента ---
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
