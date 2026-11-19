from datetime import datetime, timedelta, timezone
import pytest

from app.rules import TelemetryPacket, UserBaseline, create_anomaly_engine
from app.rag_engine import RAGService


def _make_pkt(
    idx: int,
    *,
    hr: int = 64,
    spo2: float = 98.5,
    sys_bp: int = 118,
    dia_bp: int = 75,
    temp: float = 36.8,
    rad: float = 0.3,
    sleep: int = 82,
    fatigue: float = 0.20,
    naive_ts: bool = False,
) -> TelemetryPacket:
    base_time = (
        datetime(2026, 11, 13, 12, 0, 0)
        if naive_ts
        else datetime(2026, 11, 13, 12, 0, 0, tzinfo=timezone.utc)
    )
    return TelemetryPacket(
        id=f"pkt-{idx}",
        user_id="user-1",
        recorded_at=base_time + timedelta(seconds=idx * 2),
        heart_rate_bpm=hr,
        spo2_pct=spo2,
        systolic_bp_mmhg=sys_bp,
        diastolic_bp_mmhg=dia_bp,
        core_temp_c=temp,
        radiation_msv=rad,
        sleep_score=sleep,
        eeg_fatigue_index=fatigue,
    )


def test_single_packet_does_not_fire_alert():
    engine = create_anomaly_engine()
    base = UserBaseline(user_id="user-1")
    pkts = [_make_pkt(1, hr=120, sys_bp=175)]
    status, _, alerts = engine.evaluate_window(pkts, base)
    assert status == "GREEN"
    assert len(alerts) == 0


def test_sans_golden_scenario_fires_exact_4_alerts_and_handles_mixed_timezones():
    engine = create_anomaly_engine()
    base = UserBaseline(user_id="user-1")
    pkts = [
        _make_pkt(
            i,
            sys_bp=142,
            dia_bp=88,
            rad=2.1,
            sleep=58,
            fatigue=0.58,
            naive_ts=(i % 2 == 0),
        )
        for i in range(5)
    ]
    status, regions, alerts = engine.evaluate_window(pkts, base)
    assert status == "YELLOW"
    assert {a.rule_id for a in alerts} == {
        "RULE_BP_HYPERTENSION",
        "RULE_RADIATION_SPIKE",
        "RULE_CIRCADIAN_DRIFT",
        "RULE_SANS_OCULAR_SHIFT",
    }
    assert regions["OCULAR_EYES"] == "YELLOW"


def test_yellow_to_red_escalation_bypasses_cooldown():
    engine = create_anomaly_engine(cooldown_seconds=300)
    base = UserBaseline(user_id="user-1", baseline_hr_bpm=64)

    yellow_pkts = [_make_pkt(i, hr=89, sys_bp=140, dia_bp=90) for i in range(3)]
    status1, _, alerts1 = engine.evaluate_window(yellow_pkts, base)
    assert status1 == "YELLOW"
    assert len(alerts1) == 2

    red_pkts = yellow_pkts[-2:] + [
        _make_pkt(i, hr=109, sys_bp=168, dia_bp=104) for i in range(3, 6)
    ]
    status2, _, alerts2 = engine.evaluate_window(red_pkts, base)
    assert status2 == "RED"
    assert {a.severity for a in alerts2} == {"RED"}
    assert len(alerts2) == 2


@pytest.mark.asyncio
async def test_out_of_domain_query_triggers_deterministic_refusal(tmp_path):
    from scripts.seed_db_and_kb import build_kb_index

    build_kb_index(data_dir=tmp_path, force_offline=True, overwrite_kb=True)
    rag = RAGService(
        kb_index_path=tmp_path / "kb_index.json",
        catalog_path=tmp_path / "countermeasure_catalog.json",
        provider_override=None,
    )
    res = await rag.diagnose(
        body_region="OCULAR_EYES",
        symptom_query="What is the best recipe for baking chocolate chip cookies with butter?",
    )
    assert res.execution_mode == "DETERMINISTIC_REFUSAL"
    assert res.confidence_score == 0.10
    assert res.citations == []
    assert res.generated_tasks == []
