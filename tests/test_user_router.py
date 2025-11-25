import uuid
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_users(client: AsyncClient):
    """Регистрация пользователей с разными наборами данных"""

    # Пользователь с авто (форма)
    response1 = await client.post(
        "/auth/register",
        data={
            "email": f"fulluser_{uuid.uuid4()}@example.com",
            "password": "pass123",
            "vin": "VIN123",
            "brand": "VW",
            "model": "Golf",
            "engine": "1.4",
            "kba_code": "111",
        },
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert "id" in data1
    assert "email" in data1

    # Пользователь без авто
    response2 = await client.post(
        "/auth/register",
        data={"email": f"minimal_{uuid.uuid4()}@example.com", "password": "pass123"},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert "id" in data2
    assert "email" in data2


@pytest.mark.asyncio
async def test_login_and_get_me(client: AsyncClient):
    """Логин и получение данных текущего пользователя"""
    email = f"loginuser_{uuid.uuid4()}@example.com"

    # Регистрация (форма)
    resp = await client.post("/auth/register", data={"email": email, "password": "pass123"})
    assert resp.status_code == 200

    # Логин (форма)
    login_resp = await client.post("/auth/login", data={"username": email, "password": "pass123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # GET /auth/me
    me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == email


@pytest.mark.asyncio
async def test_add_vehicle_to_existing_user(client: AsyncClient):
    """Добавление нового авто к уже существующему пользователю"""
    email = f"vehuser_{uuid.uuid4()}@example.com"

    # Регистрация без авто
    reg_resp = await client.post("/auth/register", data={"email": email, "password": "pass123"})
    assert reg_resp.status_code == 200

    # Логин
    login_resp = await client.post("/auth/login", data={"username": email, "password": "pass123"})
    token = login_resp.json()["access_token"]

    # Добавление нового авто (JSON)
    vehicle_data = {"vin": "VINNEW", "brand": "Audi", "model": "A4", "engine": "2.0", "kba_code": "888"}
    add_resp = await client.post(
        "/vehicles/",
        headers={"Authorization": f"Bearer {token}"},
        json=vehicle_data,  # <-- поменяли с data= на json=
    )
    assert add_resp.status_code == 200
    vehicle = add_resp.json()
    assert vehicle["vin"] == "VINNEW"
    assert vehicle["brand"] == "Audi"
    assert vehicle["model"] == "A4"
    assert vehicle["engine"] == "2.0"
    assert vehicle["kba_code"] == "888"