import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_emergency_scenarios_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/emergency/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()
        assert len(scenarios) >= 8
        ids = [s["scenario_id"] for s in scenarios]
        assert "CHEST_PAIN" in ids
        assert "HYPOXIA" in ids
        assert "DECOMPRESSION_SICKNESS" in ids
        assert "RADIATION_EXPOSURE" in ids
        assert "LOSS_OF_CONSCIOUSNESS" in ids
        assert "DIZZINESS_DISORIENTATION" in ids
        assert "SEVERE_DEHYDRATION" in ids
        assert "DIFFICULTY_BREATHING" in ids

@pytest.mark.asyncio
async def test_emergency_simulation_and_chat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as Mark Watney
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "mark.watney@nasa.gov",
            "password": "MarsMission2026!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test Chat
        chat_resp = await client.post("/api/v1/clinical/chat", headers=headers, json={
            "message": "I have a severe headache and blurred vision.",
            "history": []
        })
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert len(chat_data["reply"]) > 20
        assert len(chat_data["follow_up_questions"]) > 0
        assert len(chat_data["suggested_actions"]) > 0

        # Test Emergency Simulation
        sim_resp = await client.post("/api/v1/emergency/simulate", headers=headers, json={
            "scenario_id": "CHEST_PAIN",
            "custom_symptoms": "Pain spreading down left arm and feeling dizzy",
            "trigger_telemetry": True
        })
        assert sim_resp.status_code == 201
        sim_data = sim_resp.json()
        assert sim_data["severity"] == "CRITICAL"
        assert "Chest Pain" in sim_data["scenario_title"]
        assert len(sim_data["immediate_actions"]) >= 4
        assert len(sim_data["possible_concerns"]) >= 2
        assert len(sim_data["monitoring_instructions"]) >= 2
        assert len(sim_data["citations"]) >= 1


@pytest.mark.asyncio
async def test_invalid_emergency_scenario_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "mark.watney@nasa.gov",
            "password": "MarsMission2026!"
        })
        headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
        resp = await client.post("/api/v1/emergency/simulate", headers=headers, json={
            "scenario_id": "NOT_A_REAL_SCENARIO",
            "trigger_telemetry": False
        })
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_SCENARIO"


@pytest.mark.asyncio
async def test_chat_keyword_matching_uses_whole_words():
    """Regression: 'seems' must not match 'see' (ocular), 'loses consciousness' must hit syncope."""
    from app.rag_engine import OfflineRulesProvider
    p = OfflineRulesProvider()
    r1 = await p.chat("I feel sick and my heart rate seems elevated.", [], [], "SYSTEMIC")
    assert r1["body_region"] == "CARDIOVASCULAR"
    r2 = await p.chat("What should we do if a crew member loses consciousness?", [], [], "SYSTEMIC")
    assert "Unresponsive" in r2["reply"]


@pytest.mark.asyncio
async def test_alert_generation_persists_without_fk_error():
    """Regression: alerts must be inserted after their telemetry reading (FK order)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        users = (await client.get("/api/v1/auth/users")).json()
        lewis = next(u for u in users if u["email"] == "cmo.lewis@nasa.gov")
        switch_resp = await client.post("/api/v1/auth/switch", json={"user_id": lewis["id"]})
        assert switch_resp.status_code == 200
        headers = {"Authorization": f"Bearer {switch_resp.json()['access_token']}"}
        for _ in range(4):
            r = await client.post("/api/v1/emergency/simulate", headers=headers, json={
                "scenario_id": "CHEST_PAIN", "trigger_telemetry": True
            })
            assert r.status_code == 201
