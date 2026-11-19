import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import bcrypt
import numpy as np
from sqlalchemy import delete, select

from app.config import settings
from app.database import AsyncSessionLocal, Base, engine
from app.models import (
    AnomalyAlert,
    DiagnosticConsultation,
    MissionSyncReport,
    TelemetryReading,
    TraumaProtocol,
    TreatmentTask,
    User,
)
from app.rag_engine import deterministic_local_embedding

ASTRONAUT_WATNEY_ID = "550e8400-e29b-41d4-a716-446655440000"
CMO_LEWIS_ID = "660e8400-e29b-41d4-a716-446655440001"
SURGEON_CRUZ_ID = "770e8400-e29b-41d4-a716-446655440002"

COUNTERMEASURE_CATALOG: Dict[str, Dict[str, Any]] = {
    "CM_LBNP_01": {
        "countermeasure_id": "CM_LBNP_01",
        "task_type": "EXERCISE",
        "title": "Lower Body Negative Pressure (LBNP) Countermeasure Session",
        "instructions": (
            "Perform LBNP session at -20 to -25 mmHg to sequester lower-extremity fluid and "
            "attenuate cephalad venous congestion per NASA HRP SANS protocol."
        ),
        "scheduled_offset_hours": 1,
    },
    "CM_LOW_SODIUM_02": {
        "countermeasure_id": "CM_LOW_SODIUM_02",
        "task_type": "NUTRITION",
        "title": "Low-Sodium Ration & One-Carbon Folate/B-Vitamin Support",
        "instructions": (
            "Select low-sodium ration pack (<2000 mg/day target) and log standard crew "
            "B-complex nutritional supplement."
        ),
        "scheduled_offset_hours": 2,
    },
    "CM_SSLA_BLUE_03": {
        "countermeasure_id": "CM_SSLA_BLUE_03",
        "task_type": "HABITAT_ADJUSTMENT",
        "title": "SSLA 460nm Blue-Enriched Circadian Light Alignment",
        "instructions": (
            "Set habitat Solid-State Lighting Assembly (SSLA) to high-melanopic 460nm spectrum "
            "for 30 minutes during wake phase; switch to warm red-depleted mode 90 minutes pre-sleep."
        ),
        "scheduled_offset_hours": 0,
    },
    "CM_MELATONIN_04": {
        "countermeasure_id": "CM_MELATONIN_04",
        "task_type": "MEDICATION",
        "title": "Pre-Sleep Circadian Phase Alignment Protocol",
        "instructions": (
            "Follow Flight Surgeon pre-approved circadian sleep hygiene protocol 30 minutes "
            "prior to scheduled sleep window; eliminate caffeine 8 hours before sleep."
        ),
        "scheduled_offset_hours": 4,
    },
    "CM_SHIELD_SHELTER_05": {
        "countermeasure_id": "CM_SHIELD_SHELTER_05",
        "task_type": "HABITAT_ADJUSTMENT",
        "title": "Relocate to High-Mass Polyethylene Storm Shelter Zone",
        "instructions": (
            "Remain inside shielded storm shelter station until personal dosimeter readings "
            "return below 0.5 mSv/day."
        ),
        "scheduled_offset_hours": 0,
    },
    "CM_ANTIOXIDANT_06": {
        "countermeasure_id": "CM_ANTIOXIDANT_06",
        "task_type": "NUTRITION",
        "title": "Antioxidant-Rich Hydration & Carotenoid Ration",
        "instructions": (
            "Consume 1500 mL electrolyte hydration solution with antioxidant-fortified "
            "spaceflight ration pack."
        ),
        "scheduled_offset_hours": 1,
    },
    "CM_CARDIO_PACED_BREATH_07": {
        "countermeasure_id": "CM_CARDIO_PACED_BREATH_07",
        "task_type": "EXERCISE",
        "title": "Autonomic Paced-Breathing & Restorative Hydration Protocol",
        "instructions": (
            "Suspend high-load resistive exercise for 4 hours, perform 10 minutes of 6-breaths/min "
            "vagal paced breathing, and consume 500 mL oral electrolyte solution."
        ),
        "scheduled_offset_hours": 0,
    },
}

TRAUMA_PROTOCOLS_SEED: List[Dict[str, Any]] = [
    {
        "id": "e55e8400-e29b-41d4-a716-446655440555",
        "code_name": "ACUTE_HEMORRHAGE_MICROGRAVITY",
        "title": "Acute External Hemorrhage & Microgravity Restraint Stabilization",
        "body_region": "CARDIOVASCULAR",
        "steps": [
            "STEP 1: Secure patient and responder to the habitat restraint grid before intervention to prevent microgravity recoil.",
            "STEP 2: Apply direct, continuous manual pressure over the bleeding site using sterile gauze for a minimum of 3 minutes.",
            "STEP 3: If severe extremity bleeding continues, apply an arterial tourniquet proximal to the wound and record the exact UTC time.",
            "STEP 4: Continuously monitor heart rate, blood pressure, and SpO2 while alerting the Crew Medical Officer.",
        ],
        "nasa_reference": "NASA ISS Integrated Medical Group (IMG) First-Aid Stabilization Checklist (Illustrative Prototype Summary)",
    },
    {
        "id": "e55e8400-e29b-41d4-a716-446655440556",
        "code_name": "ACUTE_HYPOXIA_CABIN_DEPRESSURIZATION",
        "title": "Acute Cabin Depressurization & Supplemental Oxygen Protocol",
        "body_region": "BRAIN_NEURO",
        "steps": [
            "STEP 1: Don emergency portable 100% oxygen mask immediately and verify facepiece seal.",
            "STEP 2: Seal affected module hatch and verify cabin total pressure and oxygen partial pressure gauges.",
            "STEP 3: Exhale normally during any rapid pressure transition; never hold breath during decompression.",
            "STEP 4: Maintain continuous pulse oximetry (SpO2) monitoring and restrict physical exertion.",
        ],
        "nasa_reference": "NASA Spaceflight Medical Operations Emergency Depressurization Procedure (Illustrative Prototype Summary)",
    },
    {
        "id": "e55e8400-e29b-41d4-a716-446655440557",
        "code_name": "OCULAR_CONTAMINANT_IRRIGATION",
        "title": "Acute Ocular Particulate or Chemical Irritation Washout",
        "body_region": "OCULAR_EYES",
        "steps": [
            "STEP 1: Don protective breathing apparatus if airborne habitat contaminant is suspected.",
            "STEP 2: Position zero-gravity sealed ocular irrigation eyewear over the affected eye(s).",
            "STEP 3: Flush continuously with sterile isotonic saline for 15 minutes from nasal to temporal corner.",
            "STEP 4: Avoid rubbing the eye and perform visual acuity and pH verification with the Crew Medical Officer.",
        ],
        "nasa_reference": "NASA Crew Health Care System (CHeCS) Ocular Washout Protocol (Illustrative Prototype Summary)",
    },
]

NASA_KB_DOCUMENTS: Dict[str, str] = {
    "nasa_hrp_sans_stenger_2017.md": """# TITLE: NASA HRP Evidence Report: Risk of Spaceflight Associated Neuro-ocular Syndrome (SANS) (Stenger et al., 2017)
# PROVENANCE: Paraphrased prototype summary based on NASA Human Research Program (HRP) SANS Evidence Report themes. Not verbatim clinical guidance.
# BODY_REGION: OCULAR_EYES

## PAGE: 4
# COUNTERMEASURES: CM_LBNP_01, CM_LOW_SODIUM_02
In- and post-flight changes in visual acuity and structural changes of the eye include unilateral or bilateral optic disc edema, globe flattening, choroidal folds, cotton wool spots, and hyperopic refractive error shift. Astronauts on long-duration microgravity missions frequently report progressive near-vision blurriness when reading instrument panels and mild retro-orbital pressure or headache caused by cephalad fluid shifts toward the head.

## PAGE: 28
# COUNTERMEASURES: CM_LBNP_01, CM_LOW_SODIUM_02
Mechanical and nutritional countermeasures investigated by the NASA Human Research Program to mitigate cephalad venous congestion in SANS include Lower Body Negative Pressure (LBNP) sessions at -20 to -25 mmHg to sequester fluid in the lower extremities, restricting dietary sodium intake below 2000 mg per day, and supporting one-carbon metabolism pathway enzymes with folate and vitamin B12 nutritional supplementation.
""",
    "nasa_hrp_radiation_spe.md": """# TITLE: NASA HRP Evidence Report: Risk of Acute Radiation Syndromes Due to Solar Particle Events (Townsend et al., 2018)
# PROVENANCE: Paraphrased prototype summary based on NASA HRP Acute Radiation Syndromes Evidence Report themes. Not verbatim clinical guidance.
# BODY_REGION: SYSTEMIC

## PAGE: 19
# COUNTERMEASURES: CM_SHIELD_SHELTER_05, CM_ANTIOXIDANT_06
During deep-space lunar and Mars transit outside Earth's magnetosphere, crew radiation dosimeters recording cumulative exposure above 1.5 mSv/day indicate elevated ionizing flux from a Solar Particle Event (SPE) or Galactic Cosmic Rays. Prodromal clinical symptoms include systemic fatigue, mild nausea, anorexia, oxidative stress, and elevated resting heart rate.

## PAGE: 33
# COUNTERMEASURES: CM_SHIELD_SHELTER_05, CM_ANTIOXIDANT_06
Immediate operational countermeasures for elevated radiation dosimetry exceeding 1.5 mSv/day require relocating crew members to the spacecraft's high-mass polyethylene storm shelter zone until dosimeter rates fall below 0.5 mSv/day, accompanied by oral electrolyte hydration (1500 mL/day) and antioxidant-rich carotenoid spaceflight rations.
""",
    "nasa_hrp_sleep_circadian.md": """# TITLE: NASA HRP Evidence Report: Risk of Performance Decrements and Adverse Health Outcomes Resulting from Sleep Loss, Circadian Desynchronization, and Work Overload (Flynn-Evans et al., 2016)
# PROVENANCE: Paraphrased prototype summary based on NASA HRP Sleep Loss and Circadian Desynchronization Evidence Report themes. Not verbatim clinical guidance.
# BODY_REGION: BRAIN_NEURO

## PAGE: 28
# COUNTERMEASURES: CM_SSLA_BLUE_03, CM_MELATONIN_04
Circadian desynchronization and sleep loss during spaceflight reduce total sleep time, degrade Actiwatch sleep quality scores below 60, and elevate prefrontal fNIRS cognitive fatigue indices above 0.65. Crew members experience daytime drowsiness, impaired psychomotor vigilance, mood irritability, and elevated sympathetic resting heart rate.

## PAGE: 51
# COUNTERMEASURES: CM_SSLA_BLUE_03, CM_MELATONIN_04
Countermeasure protocols to entrain circadian phase alignment in spacecraft habitats utilize the Solid-State Lighting Assembly (SSLA) set to 460nm blue-enriched high-melanopic spectrum for 30 minutes during the wake window, shifting to warm red-depleted lighting 90 minutes before sleep, eliminating caffeine 8 hours prior to sleep, and following Flight Surgeon pre-sleep circadian alignment protocols.
""",
    "nasa_hrp_cardiovascular_hypoxia.md": """# TITLE: NASA Spaceflight Medical Operations: Cardiovascular, Hypoxia, and Thermal Stabilization Summary
# PROVENANCE: Paraphrased prototype summary based on NASA HRP Cardiovascular Adaptations and Spaceflight Medical Operations themes. Not verbatim clinical guidance.
# BODY_REGION: CARDIOVASCULAR

## PAGE: 6
# COUNTERMEASURES: CM_CARDIO_PACED_BREATH_07, CM_LOW_SODIUM_02
Persistent resting tachycardia (heart rate elevated 20 to 40 bpm above personal baseline) and elevated arterial blood pressure (systolic >= 135 mmHg or diastolic >= 85 mmHg) during microgravity flight reflect autonomic baroreceptor unloading, vascular stiffness, and cephalad fluid redistribution. Crew members reporting palpitations, chest tightness, or vascular headache should suspend high-load resistive exercise, perform 10 minutes of paced vagal breathing, verify Astroskin ECG lead contact, and restrict dietary sodium below 2000 mg/day.

## PAGE: 14
# COUNTERMEASURES: CM_CARDIO_PACED_BREATH_07
Arterial oxygen desaturation (SpO2 dropping below 95% warning or 90% critical) or core body temperature elevation (>= 37.8 C thermal strain) during EVA or habitat operations requires immediate verification of cabin oxygen partial pressure, supplemental oxygen mask administration if SpO2 is below 92%, workload reduction, liquid cooling garment flow adjustment, and 500 mL chilled oral electrolyte rehydration.
""",
}


def _hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def write_static_kb_and_catalog(data_dir: Path, overwrite_kb: bool = False) -> Path:
    kb_dir = data_dir / "nasa_kb"
    kb_dir.mkdir(parents=True, exist_ok=True)

    catalog_file = data_dir / "countermeasure_catalog.json"
    if overwrite_kb or not catalog_file.exists():
        catalog_file.write_text(
            json.dumps(COUNTERMEASURE_CATALOG, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    for filename, content in NASA_KB_DOCUMENTS.items():
        target_md = kb_dir / filename
        if overwrite_kb or not target_md.exists():
            target_md.write_text(content.strip() + "\n", encoding="utf-8")

    frontend_pub = settings.FRONTEND_PUBLIC_DIR
    frontend_pub.mkdir(parents=True, exist_ok=True)
    (frontend_pub / "trauma_protocols.fallback.json").write_text(
        json.dumps(TRAUMA_PROTOCOLS_SEED, indent=2),
        encoding="utf-8",
    )

    return kb_dir


def build_kb_index(
    data_dir: Path,
    force_offline: bool = False,
    overwrite_kb: bool = False,
) -> int:
    kb_dir = write_static_kb_and_catalog(data_dir, overwrite_kb=overwrite_kb)
    chunks: List[Dict[str, Any]] = []

    for md_path in sorted(kb_dir.glob("*.md")):
        raw = md_path.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s*TITLE:\s*(.+)$", raw, flags=re.MULTILINE)
        region_match = re.search(r"^#\s*BODY_REGION:\s*(.+)$", raw, flags=re.MULTILINE)
        prov_match = re.search(r"^#\s*PROVENANCE:\s*(.+)$", raw, flags=re.MULTILINE)
        doc_title = title_match.group(1).strip() if title_match else md_path.stem
        body_region = region_match.group(1).strip() if region_match else "SYSTEMIC"
        provenance = (
            prov_match.group(1).strip()
            if prov_match
            else "Paraphrased prototype summary based on NASA HRP themes."
        )

        page_parts = re.split(r"^##\s*PAGE:\s*(\d+)\s*$", raw, flags=re.MULTILINE)
        for idx in range(1, len(page_parts), 2):
            page_num = int(page_parts[idx])
            block = page_parts[idx + 1].strip()
            cm_match = re.search(r"^#\s*COUNTERMEASURES:\s*(.+)$", block, flags=re.MULTILINE)
            cm_ids = (
                [c.strip() for c in cm_match.group(1).split(",") if c.strip()]
                if cm_match
                else []
            )
            cleaned_content = re.sub(
                r"^#\s*COUNTERMEASURES:.*$", "", block, flags=re.MULTILINE
            ).strip()

            chunks.append(
                {
                    "chunk_id": f"{md_path.stem}_p{page_num}",
                    "document_title": doc_title,
                    "provenance": provenance,
                    "body_region": body_region,
                    "page_number": page_num,
                    "default_countermeasure_ids": cm_ids,
                    "content": cleaned_content,
                }
            )

    embedding_backend = "local_hash"
    texts_to_embed = [f"{c['document_title']} {c['content']}" for c in chunks]

    if not force_offline and settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            all_vectors: List[List[float]] = []
            for start in range(0, len(texts_to_embed), 100):
                batch = texts_to_embed[start : start + 100]
                resp = client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=settings.EMBEDDING_DIMENSION,
                    ),
                )
                for emb in resp.embeddings:
                    vec = np.array(emb.values, dtype=np.float32)
                    norm = float(np.linalg.norm(vec))
                    if norm > 0.0:
                        vec = vec / norm
                    all_vectors.append(vec.astype(float).tolist())

            for chunk, vec in zip(chunks, all_vectors):
                chunk["embedding"] = vec
            embedding_backend = "gemini"
        except Exception as exc:
            print(f"[WARN] Gemini embedding failed ({exc}); using deterministic local vectors.")

    if embedding_backend == "local_hash":
        for chunk, text in zip(chunks, texts_to_embed):
            chunk["embedding"] = deterministic_local_embedding(
                text, dim=settings.EMBEDDING_DIMENSION
            )

    index_payload = {
        "embedding_backend": embedding_backend,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chunks": chunks,
    }
    (data_dir / "kb_index.json").write_text(
        json.dumps(index_payload, indent=2), encoding="utf-8"
    )
    return len(chunks)


async def seed_database(reset: bool = False) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        existing_user = (
            await session.execute(select(User).where(User.id == ASTRONAUT_WATNEY_ID))
        ).scalar_one_or_none()

        if existing_user is not None and not reset:
            print("[INFO] Database already seeded. Pass --reset to wipe and re-seed.")
            return

        if reset:
            print("[INFO] --reset flag detected: clearing existing SQLite tables...")
            await session.execute(delete(MissionSyncReport))
            await session.execute(delete(TreatmentTask))
            await session.execute(delete(DiagnosticConsultation))
            await session.execute(delete(AnomalyAlert))
            await session.execute(delete(TelemetryReading))
            await session.execute(delete(TraumaProtocol))
            await session.execute(delete(User))

        now = datetime.now(timezone.utc)
        password_hash = _hash_password("MarsMission2026!")

        session.add_all(
            [
                User(
                    id=ASTRONAUT_WATNEY_ID,
                    email="mark.watney@nasa.gov",
                    password_hash=password_hash,
                    full_name="Cmdr. Mark Watney",
                    role="ASTRONAUT",
                    baseline_hr_bpm=64,
                    baseline_spo2_pct=98.5,
                    baseline_sys_bp=118,
                    baseline_dia_bp=75,
                    created_at=now,
                ),
                User(
                    id=CMO_LEWIS_ID,
                    email="cmo.lewis@nasa.gov",
                    password_hash=password_hash,
                    full_name="Dr. Melissa Lewis (CMO)",
                    role="CMO",
                    baseline_hr_bpm=62,
                    baseline_spo2_pct=99.0,
                    baseline_sys_bp=114,
                    baseline_dia_bp=72,
                    created_at=now,
                ),
                User(
                    id=SURGEON_CRUZ_ID,
                    email="surgeon.cruz@nasa.gov",
                    password_hash=password_hash,
                    full_name="Dr. Elena Cruz (Flight Surgeon)",
                    role="FLIGHT_SURGEON",
                    baseline_hr_bpm=68,
                    baseline_spo2_pct=98.0,
                    baseline_sys_bp=120,
                    baseline_dia_bp=78,
                    created_at=now,
                ),
            ]
        )

        for proto in TRAUMA_PROTOCOLS_SEED:
            session.add(
                TraumaProtocol(
                    id=proto["id"],
                    code_name=proto["code_name"],
                    title=proto["title"],
                    body_region=proto["body_region"],
                    steps_json=json.dumps(proto["steps"]),
                    nasa_reference=proto["nasa_reference"],
                )
            )

        # Flush users + trauma protocols first so FK references resolve
        await session.flush()

        for idx in range(5):
            session.add(
                TelemetryReading(
                    id=f"a11e8400-e29b-41d4-a716-44665544010{idx}",
                    user_id=ASTRONAUT_WATNEY_ID,
                    recorded_at=now - timedelta(seconds=(5 - idx) * 2),
                    heart_rate_bpm=65 + (idx % 2),
                    spo2_pct=98.5,
                    systolic_bp_mmhg=118,
                    diastolic_bp_mmhg=75,
                    core_temp_c=36.8,
                    radiation_msv=0.32,
                    sleep_score=84,
                    eeg_fatigue_index=0.20,
                    status_level="GREEN",
                )
            )

        await session.commit()
        print("[OK] SQLite database seeded with synthetic crew profiles and trauma protocols.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AstroHealth AI SQLite DB and KB Index")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--overwrite-kb", action="store_true")
    parser.add_argument("--offline-embeddings", action="store_true")
    args = parser.parse_args()

    chunk_count = build_kb_index(
        data_dir=settings.DATA_DIR,
        force_offline=args.offline_embeddings,
        overwrite_kb=args.overwrite_kb,
    )
    print(f"[OK] Indexed {chunk_count} NASA HRP chunks into {settings.KB_INDEX_PATH}.")
    await seed_database(reset=args.reset)


if __name__ == "__main__":
    asyncio.run(main())
