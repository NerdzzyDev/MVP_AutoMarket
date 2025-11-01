# tests/test_vehicle_router_e2e.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_vehicle_workflow(client: AsyncClient, auth_token):
    """Полный E2E-тест workflow с машинами для одного пользователя"""

    headers = {"Authorization": f"Bearer {auth_token}"}

    # --- 1. Добавляем первую машину ---
    v1_resp = await client.post(
        "/vehicles/",
        headers=headers,
        json={
            "vin": "VIN1",
            "brand": "VW",
            "model": "Golf",
            "engine": "1.4",
            "kba_code": "111",
        },
    )
    assert v1_resp.status_code == 200
    v1 = v1_resp.json()
    assert v1["vin"] == "VIN1"
    assert v1["is_selected"] is False

    # --- 2. Добавляем вторую машину ---
    v2_resp = await client.post(
        "/vehicles/",
        headers=headers,
        json={
            "vin": "VIN2",
            "brand": "VW",
            "model": "Polo",
            "engine": "1.6",
            "kba_code": "222",
        },
    )
    assert v2_resp.status_code == 200
    v2 = v2_resp.json()
    assert v2["vin"] == "VIN2"
    assert v2["is_selected"] is False

    # --- 3. Выбираем вторую машину ---
    select_resp = await client.patch(f"/vehicles/{v2['id']}/select", headers=headers)
    assert select_resp.status_code == 200
    selected = select_resp.json()
    assert selected["id"] == v2["id"]
    assert selected["is_selected"] is True

    # --- 4. Проверяем список машин ---
    list_resp = await client.get("/vehicles/", headers=headers)
    assert list_resp.status_code == 200
    vehicles = list_resp.json()
    assert len(vehicles) >= 2

    v1_listed = next(v for v in vehicles if v["id"] == v1["id"])
    v2_listed = next(v for v in vehicles if v["id"] == v2["id"])

    assert v1_listed["is_selected"] is False
    assert v2_listed["is_selected"] is True

    # --- 5. Удаляем первую машину ---
    del_resp = await client.delete(f"/vehicles/{v1['id']}", headers=headers)
    assert del_resp.status_code == 200

    # --- 6. Проверяем, что первая машина удалена, вторая осталась ---
    list_after_del = (await client.get("/vehicles/", headers=headers)).json()
    assert all(v["id"] != v1["id"] for v in list_after_del)
    assert any(v["id"] == v2["id"] for v in list_after_del)
