import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_async_db
from app.main import app

# --- Тестовая база SQLite в памяти ---
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


# --- Подмена зависимости FastAPI ---
async def override_get_async_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_async_db] = override_get_async_db


# --- Фикстура клиента ---
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# --- Фикстура авторизации ---
@pytest_asyncio.fixture
async def auth_token(client: AsyncClient):
    await client.post("/auth/register", data={"email": "user@example.com", "password": "pass123"})
    resp = await client.post("/auth/login", json={"email": "user@example.com", "password": "pass123"})
    token = resp.json()["access_token"]
    return token
