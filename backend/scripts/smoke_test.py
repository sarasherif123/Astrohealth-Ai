"""
End-to-End Live Backend Smoke Test for AstroHealth AI (V2.2)
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000/api/v1"

def run_smoke_test():
    print("=== ASTROHEALTH AI V2.2 LIVE API SMOKE TEST ===")
    
    # 1. Health check
    print("\n[1/7] Testing GET /health...")
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    health_data = r.json()
    print(f" -> OK: status={health_data.get('status')}, mode={health_data.get('ai_provider_mode')}")

    # 2. Trauma protocols zero-auth
    print("\n[2/7] Testing GET /trauma-protocols (zero-auth)...")
    r = requests.get(f"{BASE_URL}/trauma-protocols", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    protocols = r.json()
    assert len(protocols) >= 3, f"Expected >= 3 protocols, got {len(protocols)}"
    print(f" -> OK: {len(protocols)} emergency trauma protocols returned without auth")

    # 3. Auth login
    print("\n[3/7] Testing POST /auth/login...")
    login_payload = {
        "email": "mark.watney@nasa.gov",
        "password": "MarsMission2026!"
    }
    r = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    token_data = r.json()
    token = token_data.get("access_token")
    assert token, "No access_token returned"
    print(f" -> OK: Logged in as Cmdr. Mark Watney, token received (len={len(token)})")

    headers = {"Authorization": f"Bearer {token}"}

    # 4. Telemetry latest
    print("\n[4/7] Testing GET /telemetry/latest...")
    r = requests.get(f"{BASE_URL}/telemetry/latest", headers=headers, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    telem_data = r.json()
    assert "readings" in telem_data and "region_statuses" in telem_data
    print(f" -> OK: status_level={telem_data.get('status_level')}, readings={len(telem_data['readings'])}, regions={list(telem_data['region_statuses'].keys())}")

    # 5. Simulate scenario
    print("\n[5/7] Testing POST /telemetry/simulate-scenario (SANS_OCULAR_AND_RADIATION_SPIKE)...")
    sim_payload = {
        "scenario": "SANS_OCULAR_AND_RADIATION_SPIKE",
        "time_compression": 1.0
    }
    r = requests.post(f"{BASE_URL}/telemetry/simulate-scenario", headers=headers, json=sim_payload, timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    sim_data = r.json()
    alerts_count = sim_data.get("alerts_triggered", len(sim_data.get("alerts", [])))
    print(f" -> OK: status={sim_data.get('status_level')}, alerts={alerts_count}")
    assert sim_data.get("status_level") == "YELLOW", f"Expected YELLOW, got {sim_data.get('status_level')}"
    assert alerts_count == 4, f"Expected 4 alerts, got {alerts_count}"

    # 6. Consultations RAG
    print("\n[6/7] Testing POST /consultations (RAG diagnosis)...")
    diag_payload = {
        "body_region": "OCULAR_EYES",
        "symptom_query": "my eyes feel blurry and my head hurts",
        "voice_stress_score": 0.65
    }
    r = requests.post(f"{BASE_URL}/consultations", headers=headers, json=diag_payload, timeout=15)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    diag_data = r.json()
    assert len(diag_data.get("citations", [])) > 0, "No citations returned"
    assert len(diag_data.get("generated_tasks", [])) > 0, "No allowlisted tasks generated"
    print(f" -> OK: mode={diag_data.get('execution_mode')}, match={diag_data.get('protocol_retrieval_match_pct')}%, citations={len(diag_data.get('citations'))}, tasks={len(diag_data.get('generated_tasks'))}")

    # 7. Sync report & HMAC Tamper Demo
    print("\n[7/7] Testing POST /reports/sync and tamper detection...")
    r = requests.post(f"{BASE_URL}/reports/sync", headers=headers, json={"notes": "Sol 42 Automated Mission Report"}, timeout=5)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    report_data = r.json()
    report_id = report_data["id"]
    print(f" -> Report created: {report_id}, HMAC={report_data.get('integrity_hmac')[:16]}...")

    # Verify original report
    r = requests.get(f"{BASE_URL}/reports/{report_id}/verify", headers=headers, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    verify_data = r.json()
    assert verify_data["verified"] is True, f"Expected True, got {verify_data['verified']}"
    print(" -> HMAC integrity verification: VERIFIED (True)")

    # Tamper demo
    r = requests.post(f"{BASE_URL}/reports/{report_id}/tamper-demo", headers=headers, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    print(" -> Tamper injected into report payload")

    # Verify tampered report
    r = requests.get(f"{BASE_URL}/reports/{report_id}/verify", headers=headers, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    tamper_verify_data = r.json()
    assert tamper_verify_data["verified"] is False, f"Expected False, got {tamper_verify_data['verified']}"
    print(" -> Cryptographic tamper detected: TAMPER DETECTED (False)")

    print("\n=== ALL 7 LIVE API SMOKE TESTS PASSED 100% ===")

if __name__ == "__main__":
    run_smoke_test()
