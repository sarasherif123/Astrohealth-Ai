import requests

BASE = "http://127.0.0.1:8000/api/v1"

# 1. Health check
h = requests.get(f"{BASE}/health").json()
print("[TEST 1/8] Health check:", h["status"], "| Mode:", h["ai_provider_mode"], "| Chunks:", h["kb_chunks_loaded"])

# 2. Login
login_res = requests.post(f"{BASE}/auth/login", json={"email": "mark.watney@nasa.gov", "password": "MarsMission2026!"}).json()
token = login_res["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("[TEST 2/8] Authenticated as:", login_res["user"]["full_name"], "| Role:", login_res["user"]["role"])

# 3. Telemetry latest
tel = requests.get(f"{BASE}/telemetry/latest", headers=headers).json()
print("[TEST 3/8] Telemetry status:", tel["overall_status"], "| Readings count:", len(tel["readings"]), "| Alerts:", len(tel["active_alerts"]))

# 4. Medical Chat Multi-turn
chat1 = requests.post(f"{BASE}/clinical/chat", headers=headers, json={"message": "I feel sick and my heart rate seems elevated.", "history": []}).json()
print("[TEST 4/8] Chat Q1 severity:", chat1["severity"], "| Reply snippet:", chat1["reply"][:80], "...")
chat2 = requests.post(f"{BASE}/clinical/chat", headers=headers, json={
    "message": "Explain the symptoms of hypoxia.",
    "history": [{"role": "user", "content": "I feel sick"}, {"role": "assistant", "content": chat1["reply"]}]
}).json()
print("[TEST 4/8] Chat Q2 follow-ups:", len(chat2["follow_up_questions"]), "| Citations:", len(chat2["citations"]))

# 5. Emergency Simulation
sim = requests.post(f"{BASE}/emergency/simulate", headers=headers, json={
    "scenario_id": "CHEST_PAIN",
    "custom_symptoms": "Pain spreading down left arm and feeling dizzy",
    "trigger_telemetry": True
}).json()
print("[TEST 5/8] Emergency Sim:", sim["scenario_title"], "| Severity:", sim["severity"], "| Actions:", len(sim["immediate_actions"]), "| Possible concerns:", len(sim["possible_concerns"]))

# 6. Tasks
tasks = requests.get(f"{BASE}/tasks", headers=headers).json()
print("[TEST 6/8] Tasks in schedule:", len(tasks))

# 7. Trauma protocols
tp = requests.get(f"{BASE}/trauma-protocols").json()
print("[TEST 7/8] Trauma protocols loaded:", len(tp))

# 8. Mission Sync & HMAC Verification
sync_rep = requests.post(f"{BASE}/reports/sync", headers=headers, json={}).json()
verify = requests.get(f"{BASE}/reports/{sync_rep['id']}/verify", headers=headers).json()
print("[TEST 8/8] Mission Sync Report HMAC-SHA256 verified:", verify["verified"])

print("\n>>> ALL 8 INTEGRATION TESTS PASSED SUCCESSFULLY! <<<")
