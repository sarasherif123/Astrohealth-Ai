import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

ASTRONAUT_EMAIL = "mark.watney@nasa.gov"
ASTRONAUT_PASSWORD = "MarsMission2026!"
ASTRONAUT_ID = "550e8400-e29b-41d4-a716-446655440000"

CMO_EMAIL = "cmo.lewis@nasa.gov"
CMO_PASSWORD = "MarsMission2026!"
CMO_ID = "660e8400-e29b-41d4-a716-446655440001"


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def astronaut_token(async_client: AsyncClient) -> str:
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": ASTRONAUT_EMAIL, "password": ASTRONAUT_PASSWORD},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
async def cmo_token(async_client: AsyncClient) -> str:
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": CMO_EMAIL, "password": CMO_PASSWORD},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_health_endpoint_public(async_client: AsyncClient):
    res = await async_client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "ai_provider_mode" in data


@pytest.mark.asyncio
async def test_trauma_protocols_zero_auth(async_client: AsyncClient):
    res = await async_client.get("/api/v1/trauma-protocols")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": ASTRONAUT_EMAIL, "password": ASTRONAUT_PASSWORD},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == ASTRONAUT_EMAIL
    assert body["user"]["role"] == "ASTRONAUT"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": ASTRONAUT_EMAIL, "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nasa.gov", "password": "MarsMission2026!"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(async_client: AsyncClient):
    res = await async_client.get("/api/v1/telemetry/latest")
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "NOT_AUTHENTICATED"


@pytest.mark.asyncio
async def test_invalid_token_rejected(async_client: AsyncClient):
    res = await async_client.get(
        "/api/v1/telemetry/latest",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_idor_astronaut_cannot_access_other_user_telemetry(
    async_client: AsyncClient, astronaut_token: str
):
    # Watney attempts to query CMO Lewis's telemetry
    res = await async_client.get(
        f"/api/v1/telemetry/latest?user_id={CMO_ID}",
        headers={"Authorization": f"Bearer {astronaut_token}"},
    )
    assert res.status_code == 403
    body = res.json()
    assert body["error"]["code"] == "FORBIDDEN_OWNERSHIP"


@pytest.mark.asyncio
async def test_cmo_can_access_other_user_telemetry(
    async_client: AsyncClient, cmo_token: str
):
    # CMO Lewis querying Astronaut Watney's telemetry is allowed
    res = await async_client.get(
        f"/api/v1/telemetry/latest?user_id={ASTRONAUT_ID}",
        headers={"Authorization": f"Bearer {cmo_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "readings" in body
    assert "region_statuses" in body


@pytest.mark.asyncio
async def test_idor_astronaut_cannot_access_other_user_sync_reports(
    async_client: AsyncClient, astronaut_token: str
):
    # Watney attempts to view CMO Lewis's reports
    res = await async_client.get(
        f"/api/v1/reports?user_id={CMO_ID}",
        headers={"Authorization": f"Bearer {astronaut_token}"},
    )
    assert res.status_code == 403
    body = res.json()
    assert body["error"]["code"] == "FORBIDDEN_OWNERSHIP"


@pytest.mark.asyncio
async def test_hmac_sync_and_tamper_detection(
    async_client: AsyncClient, astronaut_token: str
):
    headers = {"Authorization": f"Bearer {astronaut_token}"}

    # 1. Create a sync report
    sync_res = await async_client.post(
        "/api/v1/reports/sync",
        headers=headers,
        json={"notes": "Sol 42 health summary test"},
    )
    assert sync_res.status_code == 201
    report = sync_res.json()
    report_id = report["id"]
    assert report["integrity_hmac"] is not None

    # 2. Verify integrity -> should be True
    verify_res = await async_client.get(
        f"/api/v1/reports/{report_id}/verify",
        headers=headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True

    # 3. Simulate tamper
    tamper_res = await async_client.post(
        f"/api/v1/reports/{report_id}/tamper-demo",
        headers=headers,
    )
    assert tamper_res.status_code == 200
    assert tamper_res.json()["tampered"] is True

    # 4. Verify integrity again -> should now be False (tampered)
    verify_after_tamper = await async_client.get(
        f"/api/v1/reports/{report_id}/verify",
        headers=headers,
    )
    assert verify_after_tamper.status_code == 200
    assert verify_after_tamper.json()["verified"] is False


@pytest.mark.asyncio
async def test_crew_manifest_and_switching(async_client: AsyncClient, astronaut_token: str):
    headers = {"Authorization": f"Bearer {astronaut_token}"}

    # 1. List crew members
    list_res = await async_client.get("/api/v1/auth/users", headers=headers)
    assert list_res.status_code == 200
    crew = list_res.json()
    assert len(crew) >= 3
    names = [c["full_name"] for c in crew]
    assert any("Watney" in n for n in names)
    assert any("Lewis" in n for n in names)
    assert any("Cruz" in n for n in names)

    # 2. Add new astronaut
    create_res = await async_client.post(
        "/api/v1/auth/users",
        json={
            "full_name": "Major Tom (Test)",
            "role": "ASTRONAUT",
            "baseline_hr_bpm": 60,
            "baseline_spo2_pct": 99.0,
            "baseline_sys_bp": 115,
            "baseline_dia_bp": 72,
        },
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert "access_token" in created_data
    new_user = created_data["user"]
    assert new_user["full_name"] == "Major Tom (Test)"
    assert new_user["role"] == "ASTRONAUT"

    # 3. Switch user
    switch_res = await async_client.post(
        "/api/v1/auth/switch",
        json={"user_id": new_user["id"]},
    )
    assert switch_res.status_code == 200
    switch_data = switch_res.json()
    assert switch_data["user"]["id"] == new_user["id"]
    assert "access_token" in switch_data
