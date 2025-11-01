# import uuid

# import pytest
# from httpx import AsyncClient


# @pytest.mark.asyncio
# async def test_users_and_vehicles_e2e(client: AsyncClient):
#     """E2E тест: регистрация пользователей, авто, обновление данных"""

#     # -------------------------
#     # 1. Регистрация пользователей
#     # -------------------------
#     email1 = f"user_with_car_{uuid.uuid4()}@example.com"
#     email2 = f"user_without_car_{uuid.uuid4()}@example.com"

#     # Пользователь с авто сразу (data)
#     reg1 = await client.post(
#         "/auth/register",
#         data={
#             "email": email1,
#             "password": "pass123",
#             # можно сразу добавить авто, если нужно
#             # "vin": "VIN1001", "brand": "BMW", "model": "X5", "engine": "3.0", "kba_code": "100"
#         },
#     )
#     assert reg1.status_code == 200
#     user1 = reg1.json()

#     # Пользователь без авто
#     reg2 = await client.post(
#         "/auth/register",
#         data={"email": email2, "password": "pass123"},
#     )
#     assert reg2.status_code == 200
#     user2 = reg2.json()

#     # -------------------------
#     # 2. Логин пользователей
#     # -------------------------
#     login1 = await client.post("/auth/login", data={"email": email1, "password": "pass123"})
#     token1 = login1.json()["access_token"]
#     headers1 = {"Authorization": f"Bearer {token1}"}

#     login2 = await client.post("/auth/login", data={"email": email2, "password": "pass123"})
#     token2 = login2.json()["access_token"]
#     headers2 = {"Authorization": f"Bearer {token2}"}

#     # -------------------------
#     # 3. Добавление авто (у обоих пользователей)
#     # -------------------------
#     vehicle1 = await client.post(
#         "/vehicles/",
#         headers=headers1,
#         data={"vin": "VIN1001", "brand": "BMW", "model": "X5", "engine": "3.0", "kba_code": "100"},
#     )
#     assert vehicle1.status_code == 200

#     vehicle2 = await client.post(
#         "/vehicles/",
#         headers=headers2,
#         data={"vin": "VIN2001", "brand": "Audi", "model": "A4", "engine": "2.0", "kba_code": "200"},
#     )
#     assert vehicle2.status_code == 200

#     # -------------------------
#     # 4. Проверка авто
#     # -------------------------
#     vehicles1 = (await client.get("/vehicles/", headers=headers1)).json()
#     vehicles2 = (await client.get("/vehicles/", headers=headers2)).json()
#     assert any(v["vin"] == "VIN1001" for v in vehicles1)
#     assert any(v["vin"] == "VIN2001" for v in vehicles2)

#     # -------------------------
#     # 5. Обновление данных пользователя
#     # -------------------------
#     new_email1 = f"updated_{uuid.uuid4()}@example.com"
#     update_resp1 = await client.patch("/auth/users/me", headers=headers1, data={"email": new_email1})
#     assert update_resp1.status_code == 200
#     assert update_resp1.json()["email"] == new_email1

#     # -------------------------
#     # 6. Проверка /auth/me
#     # -------------------------
#     me_resp1 = await client.get("/auth/me", headers=headers1)
#     assert me_resp1.status_code == 200
#     assert me_resp1.json()["email"] == new_email1

#     me_resp2 = await client.get("/auth/me", headers=headers2)
#     assert me_resp2.status_code == 200
#     assert me_resp2.json()["email"] == email2
