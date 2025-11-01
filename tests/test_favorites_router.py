# import uuid

# import pytest
# import pytest_asyncio
# from httpx import ASGITransport, AsyncClient
# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# from app.core.db import Base, get_async_db
# from app.main import app
# from app.models.user import Product, User
# from app.routers.user_router import get_current_user

# TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# engine = create_async_engine(TEST_DATABASE_URL, future=True)
# TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# # --- Создание/удаление таблиц ---
# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def setup_test_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)


# # --- Фикстура сессии для каждого теста с rollback ---
# @pytest_asyncio.fixture
# async def session() -> AsyncSession:
#     async with TestSessionLocal() as session:
#         async with session.begin():
#             yield session
#             # rollback после теста
#             await session.rollback()


# # --- Подмена зависимости FastAPI ---
# @pytest_asyncio.fixture(autouse=True)
# async def override_db_dependency():
#     async def _get_db_override():
#         async with TestSessionLocal() as session:
#             async with session.begin():
#                 yield session
#                 await session.rollback()

#     app.dependency_overrides[get_async_db] = _get_db_override


# # --- Клиент ---
# @pytest_asyncio.fixture
# async def client():
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
#         yield ac


# @pytest.mark.asyncio
# async def test_favorites_flow(client, session):
#     # Создаем тестового пользователя
#     test_email = f"favuser_{uuid.uuid4()}@example.com"
#     user = User(email=test_email, password_hash="hashed")
#     session.add(user)
#     await session.commit()
#     await session.refresh(user)

#     # Создаем тестовый продукт
#     product = Product(
#         title="Favorite Product",
#         product_url="http://example.com/fav_product",
#         image_url="http://example.com/fav_image.jpg",
#         price="20.00 €",
#         description="Favorite description",
#     )
#     session.add(product)
#     await session.commit()
#     await session.refresh(product)

#     # Mock зависимости текущего пользователя
#     async def override_get_current_user():
#         return user

#     app.dependency_overrides[get_current_user] = override_get_current_user

#     # 1. Добавление в избранное
#     response = await client.post(f"/favorites/{product.id}", data={"vin": "VIN123456"})
#     assert response.status_code == 200
#     data = response.json()
#     assert data["vin"] == "VIN123456"
#     assert data["product"]["title"] == "Favorite Product"

#     fav_id = data["id"]

#     # 2. Проверка списка избранного
#     response = await client.get("/favorites/")
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) == 1
#     assert data[0]["product"]["title"] == "Favorite Product"

#     # 3. Удаление из избранного
#     response = await client.delete(f"/favorites/{fav_id}")
#     assert response.status_code == 200
#     data = response.json()
#     assert data["message"] == "Removed from favorites"

#     # 4. Проверка, что список пуст
#     response = await client.get("/favorites/")
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) == 0
