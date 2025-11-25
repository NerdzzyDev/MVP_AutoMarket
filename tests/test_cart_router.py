# import uuid
# import pytest
# from httpx import AsyncClient
# from app.routers.user_router import get_current_user
# from app.models.user import User, Product

# @pytest.mark.asyncio
# async def test_cart_flow(client: AsyncClient, session):
#     """Добавление товара в корзину и проверка"""
#     # Создаем тестового пользователя
#     test_email = f"cartuser_{uuid.uuid4()}@example.com"
#     user = User(email=test_email, password_hash="hashed")
#     session.add(user)
#     await session.commit()
#     await session.refresh(user)

#     # Создаем тестовый продукт
#     product = Product(
#         title="Test Product",
#         product_url="http://example.com/product",
#         image_url="http://example.com/image.jpg",
#         price="10.00 €",
#         description="Test description",
#     )
#     session.add(product)
#     await session.commit()
#     await session.refresh(product)

#     # Мокаем текущего пользователя
#     async def override_get_current_user():
#         return user
#     client.app.dependency_overrides[get_current_user] = override_get_current_user

#     # Добавление товара в корзину через форму
#     response = await client.post("/cart/add", data={"product_id": product.id, "quantity": 2})
#     assert response.status_code == 200
#     data = response.json()
#     assert data["quantity"] == 2

#     # Проверка корзины
#     response = await client.get("/cart/")
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) == 1
#     assert data[0]["product"]["title"] == "Test Product"
#     assert data[0]["quantity"] == 2
