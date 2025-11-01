import uuid

import pytest
from httpx import AsyncClient
from loguru import logger


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
    logger.info(f"Register with vehicle: {response1.status_code} {response1.text}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert "id" in data1
    assert "email" in data1

    # Пользователь без авто
    response2 = await client.post(
        "/auth/register",
        data={"email": f"minimal_{uuid.uuid4()}@example.com", "password": "pass123"},
    )
    logger.info(f"Register minimal: {response2.status_code} {response2.text}")
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
    logger.info(f"Register response: {resp.status_code} {resp.text}")
    assert resp.status_code == 200

    # Логин (JSON)
    login_resp = await client.post("/auth/login", json={"email": email, "password": "pass123"})
    logger.info(f"Login response: {login_resp.status_code} {login_resp.text}")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token

    # GET /auth/me
    me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    logger.info(f"/auth/me response: {me_resp.status_code} {me_resp.text}")
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == email


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    """Обновление пользователя"""
    email = f"updateuser_{uuid.uuid4()}@example.com"

    # Регистрация (форма)
    reg_resp = await client.post("/auth/register", data={"email": email, "password": "pass123"})
    logger.info(f"Register for update: {reg_resp.status_code} {reg_resp.text}")
    assert reg_resp.status_code == 200

    # Логин (JSON)
    login_resp = await client.post("/auth/login", json={"email": email, "password": "pass123"})
    logger.info(f"Login for update: {login_resp.status_code} {login_resp.text}")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Обновление email (JSON)
    new_email = f"updated_{uuid.uuid4()}@example.com"
    update_resp = await client.patch(
        "/auth/users/me",
        json={"email": new_email},
        headers={"Authorization": f"Bearer {token}"},
    )
    logger.info(f"Update response: {update_resp.status_code} {update_resp.text}")
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data.get("email") == new_email


@pytest.mark.asyncio
async def test_register_users_with_vehicle(client: AsyncClient):
    """Регистрация пользователя с авто и проверка полей авто"""
    email = f"autouser_{uuid.uuid4()}@example.com"

    response = await client.post(
        "/auth/register",
        data={
            "email": email,
            "password": "pass123",
            "vin": "VIN999",
            "brand": "BMW",
            "model": "X5",
            "engine": "3.0",
            "kba_code": "999",
        },
    )
    logger.info(f"Register user with vehicle: {response.status_code} {response.text}")
    assert response.status_code == 200
    user_data = response.json()
    assert "id" in user_data
    assert "email" in user_data


@pytest.mark.asyncio
async def test_add_vehicle_to_existing_user(client: AsyncClient):
    """Добавление нового авто к уже существующему пользователю"""
    email = f"vehuser_{uuid.uuid4()}@example.com"

    # Регистрация без авто (форма)
    reg_resp = await client.post("/auth/register", data={"email": email, "password": "pass123"})
    logger.info(f"Register for vehicle addition: {reg_resp.status_code} {reg_resp.text}")
    assert reg_resp.status_code == 200

    # Логин (JSON)
    login_resp = await client.post("/auth/login", json={"email": email, "password": "pass123"})
    logger.info(f"Login for vehicle addition: {login_resp.status_code} {login_resp.text}")
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Добавление нового авто (JSON!)
    vehicle_data = {"vin": "VINNEW", "brand": "Audi", "model": "A4", "engine": "2.0", "kba_code": "888"}
    add_resp = await client.post(
        "/vehicles/",
        headers={"Authorization": f"Bearer {token}"},
        json=vehicle_data,  # <-- поменяли с data= на json=
    )
    logger.info(f"Add vehicle response: {add_resp.status_code} {add_resp.text}")
    assert add_resp.status_code == 200

    vehicle = add_resp.json()
    assert vehicle["vin"] == "VINNEW"
    assert vehicle["brand"] == "Audi"
    assert vehicle["model"] == "A4"
    assert vehicle["engine"] == "2.0"
    assert vehicle["kba_code"] == "888"
    assert vehicle.get("is_selected") is False
