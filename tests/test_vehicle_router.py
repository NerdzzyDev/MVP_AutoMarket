import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_vehicle_workflow(client: AsyncClient, auth_token):
    """Полный workflow с машинами для одного пользователя"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Добавление первой машины (JSON)
    v1_resp = await client.post(
        "/vehicles/",
        headers=headers,
        json={"vin": "VIN1", "brand": "VW", "model": "Golf", "engine": "1.4", "kba_code": "111"},
    )
    assert v1_resp.status_code == 200
    v1 = v1_resp.json()
    assert v1["vin"] == "VIN1"

    # Добавление второй машины (JSON)
    v2_resp = await client.post(
        "/vehicles/",
        headers=headers,
        json={"vin": "VIN2", "brand": "VW", "model": "Polo", "engine": "1.6", "kba_code": "222"},
    )
    assert v2_resp.status_code == 200
    v2 = v2_resp.json()

    # Выбор второй машины
    select_resp = await client.patch(f"/vehicles/{v2['id']}/select", headers=headers)
    assert select_resp.status_code == 200
    selected = select_resp.json()
    assert selected["is_selected"] is True

    # Проверка списка машин
    list_resp = await client.get("/vehicles/", headers=headers)
    assert list_resp.status_code == 200
    vehicles = list_resp.json()
    assert any(v["id"] == v1["id"] for v in vehicles)
    assert any(v["id"] == v2["id"] for v in vehicles)

    # Удаление первой машины
    del_resp = await client.delete(f"/vehicles/{v1['id']}", headers=headers)
    assert del_resp.status_code == 200

    list_after_del = (await client.get("/vehicles/", headers=headers)).json()
    assert all(v["id"] != v1["id"] for v in list_after_del)
    assert any(v["id"] == v2["id"] for v in list_after_del)
