"""NASA Spaceflight Emergency Medical Scenarios Catalog
Grounded in NASA Human Research Program (HRP) Evidence Reports,
Integrated Medical Group (IMG) First-Aid Stabilization Procedures,
and Crew Health Care System (CHeCS) Protocols.
"""

from typing import Any, Dict, List

EMERGENCY_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "CHEST_PAIN": {
        "scenario_id": "CHEST_PAIN",
        "title": "Acute Chest Pain & Cardiovascular Decompensation",
        "body_region": "CARDIOVASCULAR",
        "severity": "CRITICAL",
        "default_symptoms": (
            "Substernal chest tightness radiating to left shoulder and jaw, persistent palpitations, "
            "shortness of breath at rest, diaphoresis, and sudden systolic blood pressure elevation."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 132,
            "spo2_pct": 92.5,
            "systolic_bp_mmhg": 174,
            "diastolic_bp_mmhg": 108,
            "core_temp_c": 37.3,
            "radiation_msv": 0.42,
            "sleep_score": 52,
            "eeg_fatigue_index": 0.62,
        },
        "possible_concerns": [
            "Acute coronary syndrome / myocardial ischemia aggravated by cephalad fluid shifts",
            "Malignant cardiac arrhythmia secondary to autonomic baroreceptor unloading",
            "Hypertensive crisis in microgravity",
        ],
        "immediate_actions": [
            "STEP 1: Halt all physical activity and secure astronaut to habitat medical restraint grid.",
            "STEP 2: Administer high-flow supplemental oxygen via non-rebreather mask at 10-15 L/min; verify SpO2 >= 95%.",
            "STEP 3: Attach Astroskin 12-lead ECG telemetry harness and transmit real-time telemetry to Flight Surgeon Cruz.",
            "STEP 4: Verify emergency medication locker contents for sublingual nitroglycerin and chewable aspirin (325 mg) per CMO authorization.",
            "STEP 5: Initiate continuous non-invasive blood pressure cycling every 3 minutes.",
        ],
        "monitoring_instructions": [
            "Continuous 12-lead ECG rhythm monitoring for ST-segment elevation, depression, or ventricular ectopy.",
            "Serial blood pressure measurement every 3 to 5 minutes until stabilized below 140/90 mmHg.",
            "Continuous pulse oximetry (SpO2) and respiratory rate telemetry.",
        ],
        "ground_medical_support": (
            "Priority Flash Uplink to NASA Johnson Space Center (JSC) Flight Surgeon console. "
            "Request immediate real-time telemedicine teleconference via high-gain S-band antenna."
        ),
        "warnings": [
            "WARNING: Do not administer nitrates if systolic blood pressure is below 100 mmHg or if PDE-5 inhibitors were taken in the last 24h.",
            "WARNING: Ensure responder and patient are anchored to restraint rails to prevent CPR recoil forces in microgravity.",
        ],
        "follow_up_questions": [
            "Does the chest discomfort change with deep inspiration, body position, or palpation?",
            "Is the patient experiencing any nausea, dizziness, cold diaphoresis, or visual darkening?",
            "What is the exact onset time and duration of the current pain episode?",
        ],
        "nasa_reference": "NASA Spaceflight Medical Operations: Cardiovascular, Hypoxia, and Thermal Stabilization Protocol (Page 6)",
        "countermeasure_ids": ["CM_CARDIO_PACED_BREATH_07", "CM_LOW_SODIUM_02"],
    },
    "DIFFICULTY_BREATHING": {
        "scenario_id": "DIFFICULTY_BREATHING",
        "title": "Acute Respiratory Distress & Airway Impairment",
        "body_region": "CARDIOVASCULAR",
        "severity": "CRITICAL",
        "default_symptoms": (
            "Severe dyspnea, rapid shallow tachypnea (respiratory rate > 28/min), accessory muscle use, "
            "audible expiratory wheezing, and arterial oxygen desaturation below 90%."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 126,
            "spo2_pct": 88.5,
            "systolic_bp_mmhg": 156,
            "diastolic_bp_mmhg": 96,
            "core_temp_c": 37.1,
            "radiation_msv": 0.38,
            "sleep_score": 45,
            "eeg_fatigue_index": 0.55,
        },
        "possible_concerns": [
            "Acute habitat atmospheric contaminant inhalation or toxic gas leak (e.g., ammonia/freon/combustion)",
            "Acute pulmonary edema secondary to microgravity cephalad fluid redistribution",
            "Spontaneous pneumothorax or severe reactive bronchospasm",
        ],
        "immediate_actions": [
            "STEP 1: Don emergency quick-don breathing mask immediately and verify habitat life support atmospheric composition (ppO2, ppCO2).",
            "STEP 2: Connect crew member to portable oxygen assembly (100% O2) with tight facial seal.",
            "STEP 3: Position astronaut in semi-upright restrained position against habitat bulkhead to optimize diaphragmatic excursion.",
            "STEP 4: Auscultate bilateral lung fields using digital electronic stethoscope; transmit audio stream to Mission Control.",
            "STEP 5: Prepare emergency nebulized bronchodilator (albuterol) from the onboard Medical Kit.",
        ],
        "monitoring_instructions": [
            "Continuous pulse oximetry with alert threshold set at < 92%.",
            "Cabin air quality monitor: verify carbon dioxide partial pressure (ppCO2 < 3.0 mmHg) and ammonia sensors.",
            "Respiratory rate and waveform capnography if available.",
        ],
        "ground_medical_support": (
            "Alert Flight Surgeon Cruz and habitat ECLSS (Environmental Control and Life Support System) lead. "
            "Coordinate emergency cabin atmospheric scrubbing or module isolation."
        ),
        "warnings": [
            "WARNING: If atmospheric contaminant is suspected, all crew members must immediately don breathing apparatus before assisting patient.",
            "WARNING: Never administer 100% hyperbaric oxygen in vicinity of open electrical equipment or ignition sources.",
        ],
        "follow_up_questions": [
            "Was there any sudden odor, chemical release, particulate haze, or EVA suit repressurization event prior to onset?",
            "Are there crackles, wheezes, or asymmetric breath sounds on auscultation?",
            "Is there any hemoptysis, pink frothy sputum, or retrosternal burning?",
        ],
        "nasa_reference": "NASA Spaceflight Medical Operations Emergency Depressurization and Inhalation Checklist (Page 14)",
        "countermeasure_ids": ["CM_CARDIO_PACED_BREATH_07"],
    },
    "HYPOXIA": {
        "scenario_id": "HYPOXIA",
        "title": "Acute Hypoxia & Cabin Oxygen Depletion",
        "body_region": "BRAIN_NEURO",
        "severity": "CRITICAL",
        "default_symptoms": (
            "Progressive cognitive slowing, confusion, cyanosis of lips and nail beds, visual tunnel vision, "
            "headache, loss of psychomotor coordination, and arterial SpO2 dropping to 84%."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 118,
            "spo2_pct": 84.0,
            "systolic_bp_mmhg": 148,
            "diastolic_bp_mmhg": 90,
            "core_temp_c": 36.6,
            "radiation_msv": 0.35,
            "sleep_score": 60,
            "eeg_fatigue_index": 0.82,
        },
        "possible_concerns": [
            "ECLSS oxygen generator assembly (OGA) failure or cabin depressurization",
            "Localized stagnant cabin airflow pocket causing carbon dioxide pooling or oxygen deprivation",
            "Severe arterial hypoxemia causing irreversible neuronal ischemia within 3-4 minutes",
        ],
        "immediate_actions": [
            "STEP 1: Don emergency portable 100% oxygen mask immediately and confirm positive seal pressure.",
            "STEP 2: Check cabin total pressure gauge and verify module oxygen partial pressure (ppO2 target 150-160 mmHg).",
            "STEP 3: Inspect habitat ventilation inter-module air diffusers to eliminate dead-air pockets.",
            "STEP 4: Restrict all physical exertion; astronaut must remain stationary under supplemental O2.",
            "STEP 5: Administer emergency verbal psychomotor assessment (Time of Useful Consciousness check).",
        ],
        "monitoring_instructions": [
            "SpO2 sensor must remain clamped on index finger with continuous audio telemetry alarm active.",
            "Verify cabin pressure trend every 60 seconds for signs of micro-puncture depressurization.",
            "Serial cognitive acuity and orientation tests (Name, Date, Mission Elapsed Time, Task assignment).",
        ],
        "ground_medical_support": (
            "Declare Station/Spacecraft Medical Condition Tier 1 to Mission Control Houston. "
            "Request urgent telemetry review from Flight Director and Surgeon Cruz."
        ),
        "warnings": [
            "CRITICAL: Time of Useful Consciousness (TUC) at rapid depressurization altitudes can be under 60 seconds.",
            "WARNING: Do not remove oxygen mask until cabin ppO2 is independently confirmed > 19.5% by two independent sensors.",
        ],
        "follow_up_questions": [
            "What is the exact cabin pressure reading on the primary mechanical gauge?",
            "Are other crew members in the same module reporting lightheadedness or headache?",
            "Did SpO2 begin rebounding within 90 seconds of supplemental oxygen delivery?",
        ],
        "nasa_reference": "NASA Spaceflight Medical Operations: Hypoxia and Depressurization Protocol (Page 14)",
        "countermeasure_ids": ["CM_CARDIO_PACED_BREATH_07"],
    },
    "DECOMPRESSION_SICKNESS": {
        "scenario_id": "DECOMPRESSION_SICKNESS",
        "title": "Acute Decompression Sickness (DCS / Bends)",
        "body_region": "SYSTEMIC",
        "severity": "CRITICAL",
        "default_symptoms": (
            "Excruciating peri-articular joint pain ('the bends') in shoulders and knees following EVA egress, "
            "substernal burning on inspiration ('the chokes'), cutis marmorata mottling rash, and paresthesias."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 114,
            "spo2_pct": 91.0,
            "systolic_bp_mmhg": 150,
            "diastolic_bp_mmhg": 92,
            "core_temp_c": 36.9,
            "radiation_msv": 0.40,
            "sleep_score": 55,
            "eeg_fatigue_index": 0.68,
        },
        "possible_concerns": [
            "Type II Neurological/Cardiopulmonary Decompression Sickness with intravascular nitrogen bubble emboli",
            "Venous gas emboli causing right ventricular strain or pulmonary vascular occlusion",
            "Spinal cord ischemia from epidural venous nitrogen bubbling",
        ],
        "immediate_actions": [
            "STEP 1: Initiate 100% normobaric oxygen washout immediately via tight-fitting aviator mask to accelerate nitrogen elimination.",
            "STEP 2: Increase habitat module ambient pressure to maximum allowable operational envelope (recompression protocol).",
            "STEP 3: Immobilize the patient completely in neutral posture; avoid all joint movement.",
            "STEP 4: Provide oral hydration with isotonic electrolyte solution (1000 mL/hour) if patient is conscious and alert.",
            "STEP 5: Prepare EMU (Extravehicular Mobility Unit) hyperbaric treatment protocol if cabin recompression is insufficient.",
        ],
        "monitoring_instructions": [
            "Continuous neurological exam (cranial nerves, motor strength, sensory level, tendon reflexes) every 15 minutes.",
            "Precordial Doppler audio monitoring for venous gas bubble signals if equipment available.",
            "SpO2 and continuous ECG telemetry.",
        ],
        "ground_medical_support": (
            "Contact NASA Flight Surgeon Cruz and Johnson Space Center Neutral Buoyancy Lab hyperbaric medical specialists. "
            "Coordinate recompression schedule (US Navy Treatment Table 5/6 adaptation for spaceflight)."
        ),
        "warnings": [
            "WARNING: Never allow astronaut to perform EVA or pressure-reduction activities for minimum 72 hours post DCS resolution.",
            "WARNING: Do not permit breath-holding maneuvers; patient must breathe smoothly to prevent air trapping.",
        ],
        "follow_up_questions": [
            "What was the pre-breathe protocol duration and final suit pressure during the EVA?",
            "Are neurological deficits present: numbness, weakness, visual loss, gait ataxia, or urinary retention?",
            "Is the joint pain constant, throbbing, or aggravated by passive motion?",
        ],
        "nasa_reference": "NASA Spaceflight Medical Operations: Decompression Protocols and Microgravity Gas Embolism Mitigation",
        "countermeasure_ids": ["CM_CARDIO_PACED_BREATH_07", "CM_ANTIOXIDANT_06"],
    },
    "RADIATION_EXPOSURE": {
        "scenario_id": "RADIATION_EXPOSURE",
        "title": "Solar Particle Event (SPE) Acute Radiation Overexposure",
        "body_region": "SYSTEMIC",
        "severity": "HIGH",
        "default_symptoms": (
            "Cumulative dosimeter rate exceeding 2.5 mSv/day, prodromal nausea, anorexia, intense fatigue, "
            "diffuse headache, and mild thermal sensation on exposed skin."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 86,
            "spo2_pct": 98.0,
            "systolic_bp_mmhg": 128,
            "diastolic_bp_mmhg": 82,
            "core_temp_c": 37.4,
            "radiation_msv": 3.85,
            "sleep_score": 42,
            "eeg_fatigue_index": 0.74,
        },
        "possible_concerns": [
            "Acute Radiation Syndrome (ARS) prodromal phase secondary to solar proton coronal mass ejection",
            "Hematopoietic suppression (lymphocyte and granulocyte nadir within 48-72h)",
            "Degradation of cognitive executive function under acute ionizing flux",
        ],
        "immediate_actions": [
            "STEP 1: Sound spacecraft Radiation Storm Alarm; all crew members immediately relocate to the central Polyethylene Storm Shelter.",
            "STEP 2: Deploy water bladder radiation shielding walls around the sleeping and command quarters.",
            "STEP 3: Read and log all passive TLD and active silicon personal dosimeter levels for every crew member.",
            "STEP 4: Initiate antioxidant-rich spaceflight hydration protocol (1500 mL/day oral electrolyte solution with carotenoids).",
            "STEP 5: Administer ondansetron 4-8 mg from Medical Kit if nausea/vomiting impairs hydration.",
        ],
        "monitoring_instructions": [
            "Personal electronic dosimeter readings logged every 30 minutes until storm rate drops below 0.5 mSv/day.",
            "Daily complete blood count / lymphocyte monitoring if onboard CBC analyzer is functional.",
            "Core body temperature and hydration fluid balance monitoring.",
        ],
        "ground_medical_support": (
            "Uplink with Space Radiation Analysis Group (SRAG) at Johnson Space Center. "
            "Coordinate SPE proton flux trajectory forecasts and storm shelter duration estimate."
        ),
        "warnings": [
            "WARNING: Do not leave the storm shelter module for any non-essential maintenance during peak proton flux.",
            "WARNING: Restrict physical exertion to minimize oxidative metabolic load during ionizing flux peaks.",
        ],
        "follow_up_questions": [
            "What is the current flux reading on the external spacecraft dosimeter versus personal dosimeters?",
            "Has the astronaut vomited, and if so, how many minutes elapsed after dosimeter alarm triggered?",
            "Are there any erythematous skin changes or ocular phosphenes (light flashes)?",
        ],
        "nasa_reference": "NASA HRP Evidence Report: Risk of Acute Radiation Syndromes Due to Solar Particle Events (Townsend et al., 2018)",
        "countermeasure_ids": ["CM_SHIELD_SHELTER_05", "CM_ANTIOXIDANT_06"],
    },
    "LOSS_OF_CONSCIOUSNESS": {
        "scenario_id": "LOSS_OF_CONSCIOUSNESS",
        "title": "Acute Syncope / Sudden Loss of Consciousness",
        "body_region": "BRAIN_NEURO",
        "severity": "CRITICAL",
        "default_symptoms": (
            "Unresponsive astronaut found drifting in module, unreactive to verbal commands, "
            "profound bradycardia (HR 42 bpm), hypotension (BP 82/48 mmHg), and shallow respiration."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 44,
            "spo2_pct": 90.0,
            "systolic_bp_mmhg": 84,
            "diastolic_bp_mmhg": 50,
            "core_temp_c": 36.3,
            "radiation_msv": 0.35,
            "sleep_score": 50,
            "eeg_fatigue_index": 0.90,
        },
        "possible_concerns": [
            "Profound neurocardiogenic / vasovagal syncope exacerbated by cephalad fluid shifts",
            "Acute intracranial hemorrhage, subarachnoid hemorrhage, or seizure",
            "Severe carbon dioxide narcosis (hypercapnia pocket) or toxic habitat gas exposure",
        ],
        "immediate_actions": [
            "STEP 1: Grasp astronaut and secure immediately to the habitat emergency restraint grid; maintain cervical spine stabilization.",
            "STEP 2: Assess Airway, Breathing, and Circulation (ABCs); tilt head to open airway if no trauma suspected.",
            "STEP 3: Don emergency 100% O2 mask and confirm chest expansion and carotid pulse.",
            "STEP 4: Check pupil equality, light reactivity, and capillary refill time; log Glasgow Coma Scale (GCS).",
            "STEP 5: Check fingerstick blood glucose using onboard glucometer (rule out acute hypoglycemia).",
        ],
        "monitoring_instructions": [
            "Continuous pulse oximetry, 12-lead ECG telemetry, and automated blood pressure every 2 minutes.",
            "Frequent pupil checks and neurological reflex evaluation.",
            "Verify module atmosphere for carbon dioxide pooling (ppCO2).",
        ],
        "ground_medical_support": (
            "Emergency High-Priority Audio-Visual Uplink to Flight Surgeon Elena Cruz. "
            "Prepare Advanced Life Support (ALS) medical packs and resuscitation defibrillator."
        ),
        "warnings": [
            "CRITICAL: Always secure patient before performing chest compressions or defibrillation to prevent microgravity recoil injury.",
            "WARNING: Do not administer IV fluids rapidly without monitoring for fluid overload in microgravity.",
        ],
        "follow_up_questions": [
            "Did anyone witness the collapse: was there tonic-clonic jerking, trauma, or head impact?",
            "What is the current pupil diameter and pupillary light reflex response?",
            "What is the fingerstick blood glucose level?",
        ],
        "nasa_reference": "NASA ISS Integrated Medical Group First-Aid Stabilization Checklist (Illustrative Prototype)",
        "countermeasure_ids": ["CM_CARDIO_PACED_BREATH_07"],
    },
    "DIZZINESS_DISORIENTATION": {
        "scenario_id": "DIZZINESS_DISORIENTATION",
        "title": "Severe Neuro-Vestibular Disorientation & Space Motion Sickness",
        "body_region": "BRAIN_NEURO",
        "severity": "MODERATE",
        "default_symptoms": (
            "Debilitating rotational vertigo aggravated by head motion, illusory sensation of inversion, "
            "cold sweating, persistent nausea, and severe spatial disorientation."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 88,
            "spo2_pct": 98.0,
            "systolic_bp_mmhg": 128,
            "diastolic_bp_mmhg": 80,
            "core_temp_c": 36.8,
            "radiation_msv": 0.32,
            "sleep_score": 62,
            "eeg_fatigue_index": 0.70,
        },
        "possible_concerns": [
            "Acute Space Adaptation Syndrome (SAS) / Space Motion Sickness (SMS) neurovestibular mismatch",
            "Benign paroxysmal positional vertigo or otolith organ asymmetric unloading",
            "Early Spaceflight Associated Neuro-ocular Syndrome (SANS) with retro-orbital intracranial pressure",
        ],
        "immediate_actions": [
            "STEP 1: Direct astronaut to minimize all head and neck movement; secure in restraint sleep station with eye mask.",
            "STEP 2: Align body with habitat visual horizontal cues ('Earth-down' cabin orientation references).",
            "STEP 3: Administer intramuscular promethazine 25-50 mg from Medical Kit if nausea is incapacitating.",
            "STEP 4: Maintain oral sip hydration with chilled electrolyte solution to prevent dehydration from emesis.",
            "STEP 5: Postpone scheduled high-acceleration or EVA tasks until neurovestibular adaptation stabilizes.",
        ],
        "monitoring_instructions": [
            "Monitor hydration status and urine output frequency.",
            "Check for spontaneous nystagmus or focal neurological signs.",
            "Track symptoms using standardized Space Motion Sickness symptom score sheet.",
        ],
        "ground_medical_support": (
            "Routine medical conference with Flight Surgeon Cruz. "
            "Update mission timeline to defer demanding piloting or robotic arm manipulation."
        ),
        "warnings": [
            "WARNING: Promethazine causes marked sedation; patient must not operate spacecraft controls or life-support valves.",
            "WARNING: Vomiting in a spacesuit during EVA is fatal; never permit EVA with active SMS symptoms.",
        ],
        "follow_up_questions": [
            "Does the vertigo worsen specifically with pitch, roll, or yaw head movements?",
            "Are there visual symptoms: blurred vision, double vision, or visual field deficits?",
            "Has the astronaut been able to retain oral fluids over the past 6 hours?",
        ],
        "nasa_reference": "NASA HRP Evidence Report: Risk of Spaceflight-Associated Neurovestibular Alterations and Space Motion Sickness",
        "countermeasure_ids": ["CM_SSLA_BLUE_03", "CM_LOW_SODIUM_02"],
    },
    "SEVERE_DEHYDRATION": {
        "scenario_id": "SEVERE_DEHYDRATION",
        "title": "Acute Hypovolemia & Severe Dehydration",
        "body_region": "SYSTEMIC",
        "severity": "HIGH",
        "default_symptoms": (
            "Marked postural tachycardia (HR jumps +35 bpm on upright movement), dry mucous membranes, "
            "dark oliguric urine, extreme thirst, muscle cramps, and cognitive lethargy."
        ),
        "telemetry_metrics": {
            "heart_rate_bpm": 108,
            "spo2_pct": 97.0,
            "systolic_bp_mmhg": 98,
            "diastolic_bp_mmhg": 62,
            "core_temp_c": 37.6,
            "radiation_msv": 0.35,
            "sleep_score": 58,
            "eeg_fatigue_index": 0.72,
        },
        "possible_concerns": [
            "Microgravity hypovolemia combined with inadequate water ration intake",
            "Electrolyte derangement (hypokalemia / hyponatremia) predisposing to cardiac dysrhythmias",
            "Prerenal acute kidney injury and renal stone crystallization (calcium oxalate)",
        ],
        "immediate_actions": [
            "STEP 1: Suspend resistive workout or high-metabolic-output duties immediately.",
            "STEP 2: Initiate oral rehydration therapy with balanced sodium-glucose electrolyte packs (1500-2000 mL over 3 hours).",
            "STEP 3: If patient is vomiting or unable to tolerate oral intake, prepare peripheral intravenous line with 0.9% normal saline (1000 mL infusion).",
            "STEP 4: Test urine specific gravity using onboard refractometer strips; target specific gravity < 1.015.",
            "STEP 5: Record strict fluid intake and output (I/O) flow sheet in the AstroHealth log.",
        ],
        "monitoring_instructions": [
            "Heart rate and blood pressure checks every 30 minutes until resting HR is below 85 bpm.",
            "Urine volume, color, and specific gravity monitoring on each void.",
            "Electrolyte panel check if i-STAT blood analyzer is available onboard.",
        ],
        "ground_medical_support": (
            "Notify CMO Lewis and Flight Surgeon Cruz. "
            "Review habitat potable water dispenser quality telemetry and crew water rationing logs."
        ),
        "warnings": [
            "WARNING: Do not infuse plain sterile water IV; use only isotonic normal saline or lactated Ringer's solution.",
            "WARNING: Severe dehydration in microgravity significantly accelerates nephrolithiasis (kidney stone) formation.",
        ],
        "follow_up_questions": [
            "How much fluid has the astronaut consumed in the last 24 hours?",
            "What was the volume and appearance of the last urine void?",
            "Is the patient experiencing any flank pain, hematuria, or abdominal cramping?",
        ],
        "nasa_reference": "NASA Spaceflight Medical Operations: Hydration Protocols and Microgravity Fluid Electrolyte Balance",
        "countermeasure_ids": ["CM_LOW_SODIUM_02", "CM_ANTIOXIDANT_06"],
    },
}
