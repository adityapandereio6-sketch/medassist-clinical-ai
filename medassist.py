import json
import hashlib
from datetime import datetime, timezone

class Patient:
    def __init__(self, patient_id: str, age: int, weight_kg: float, allergies: list = None, active_medications: list = None):
        self.patient_id = patient_id
        self.age = age
        self.weight_kg = weight_kg
        self.allergies = [a.strip().lower() for a in (allergies or [])]
        self.active_medications = [m.strip().lower() for m in (active_medications or [])]

class ClinicalSafetyEngine:
    def __init__(self):
        # Database of severe Drug-Drug Interactions (DDIs)
        raw_interactions = {
            "aspirin": ["warfarin", "heparin"],
            "warfarin": ["aspirin", "ibuprofen"],
            "sildenafil": ["nitroglycerin"]
        }
        
        # Normalize the database upon initialization
        self.dangerous_interactions = {
            k.strip().lower(): [v.strip().lower() for v in values]
            for k, values in raw_interactions.items()
        }

        # Simulated historical dosage database (in mg)
        raw_dosages = {
            "aspirin": [81.0, 81.0, 100.0, 325.0, 325.0, 325.0, 500.0, 500.0, 650.0],
            "warfarin": [2.0, 2.5, 3.0, 4.0, 5.0, 5.0, 7.5, 10.0],
            "ibuprofen": [200.0, 200.0, 400.0, 400.0, 400.0, 600.0, 600.0, 800.0, 800.0],
            "sildenafil": [25.0, 50.0, 50.0, 50.0, 100.0],
            "penicillin": [250.0, 250.0, 500.0, 500.0, 500.0, 500.0]
        }

        self.dosage_history = {
            k.strip().lower(): [float(v) for v in values]
            for k, values in raw_dosages.items()
        }

    def check_allergy(self, patient: Patient, new_drug: str) -> list[dict]:
        new_drug_normalized = new_drug.strip().lower()
        if new_drug_normalized in patient.allergies:
            return [{
                "severity": "CRITICAL_ALLERGY",
                "patient": patient.patient_id,
                "drug": new_drug.strip(),
                "rationale": f"Patient has a documented anaphylactic allergy to {new_drug.strip()}."
            }]
        return []

    def check_interaction(self, patient: Patient, new_drug: str) -> list[dict]:
        new_drug_normalized = new_drug.strip().lower()
        alerts = []

        for active_med in patient.active_medications:
            # Path A & Path B (Bidirectional Check)
            contra_new = self.dangerous_interactions.get(new_drug_normalized, [])
            contra_active = self.dangerous_interactions.get(active_med, [])

            if (active_med in contra_new) or (new_drug_normalized in contra_active):
                alerts.append({
                    "severity": "CRITICAL_INTERACTION",
                    "patient": patient.patient_id,
                    "new_drug": new_drug.strip(),
                    "conflicting_drug": active_med,
                    "rationale": f"Co-administration of '{new_drug.strip()}' and '{active_med}' is contraindicated."
                })

        return alerts

    def check_dosage_anomaly(self, new_drug: str, dosage_mg: float) -> list[dict]:
        new_drug_normalized = new_drug.strip().lower()
        history = self.dosage_history.get(new_drug_normalized, [])

        if len(history) < 2:
            return []

        # Calculate Mean
        mean = sum(history) / len(history)

        # Calculate Standard Deviation (Population)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std_dev = variance ** 0.5

        if std_dev == 0:
            z_score = 0.0 if dosage_mg == mean else 999.0
        else:
            z_score = (dosage_mg - mean) / std_dev

        if z_score > 2.5:
            return [{
                "severity": "DOSAGE_ANOMALY",
                "drug": new_drug.strip(),
                "dosage_mg": dosage_mg,
                "mean_mg": round(mean, 2),
                "std_dev_mg": round(std_dev, 2),
                "z_score": round(z_score, 2),
                "rationale": f"Prescribed dosage {dosage_mg}mg for {new_drug.strip()} is statistically anomalous (Z-score: {round(z_score, 2)} > 2.5). Historical mean is {round(mean, 2)}mg (SD: {round(std_dev, 2)}mg)."
            }]

        return []

    def generate_audit_log(self, patient: Patient, drug: str, dosage: float, alerts: list[dict]):
        # Format the blocked event into a deterministic dictionary
        blocked_event = {
            "patient_id": patient.patient_id,
            "drug": drug.strip(),
            "dosage_mg": dosage,
            "alerts": alerts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Serialize to JSON with sorted keys for tamper-evident cryptographic consistency
        json_string = json.dumps(blocked_event, sort_keys=True)

        # Compute SHA-256 hash of the JSON string
        event_hash = hashlib.sha256(json_string.encode("utf-8")).hexdigest()

        # Write/append both the JSON string and the hash to the local log file
        log_file_path = "clinical_audit.log"
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"EVENT: {json_string}\nHASH: {event_hash}\n---\n")

        print(f"[AUDIT] SECURE RECORD GENERATED: SHA-256 hash {event_hash[:8]}... written to clinical_audit.log.")

    def prescribe(self, patient: Patient, new_drug: str, dosage_mg: float):
        print(f"\n[ORDER] Order received: {dosage_mg}mg of {new_drug.strip()} to Patient {patient.patient_id}...")
        
        # Aggregate all alerts
        alerts = (
            self.check_allergy(patient, new_drug) + 
            self.check_interaction(patient, new_drug) + 
            self.check_dosage_anomaly(new_drug, dosage_mg)
        )

        if alerts:
            print(f"[BLOCKED] PRESCRIPTION BLOCKED. Triggered {len(alerts)} Safety Alerts:")
            for alert in alerts:
                print(f"   -> [{alert['severity']}] {alert['rationale']}")
            
            # Fire audit trail generation
            self.generate_audit_log(patient, new_drug, dosage_mg, alerts)
        else:
            patient.active_medications.append(new_drug.strip().lower())
            print(f"[CLEAR] CLEAR: {new_drug.strip()} verified and added to active medications.")

# --- Test Scenario ---
if __name__ == "__main__":
    engine = ClinicalSafetyEngine()
    
    # Test Case 1: Active medication is "warfarin", new prescription is "  AsPiRiN " (with spaces & mixed case)
    print("=== TEST CASE 1: Warfarin patient prescribed AsPiRiN ===")
    patient_one = Patient(
        patient_id="PT-9942", 
        age=65, 
        weight_kg=82.5, 
        allergies=["penicillin"], 
        active_medications=["warfarin"]
    )
    engine.prescribe(patient_one, "  AsPiRiN ", 81)

    # Test Case 2: Active medication is "aspirin", new prescription is "  waRFarin " (with spaces & mixed case)
    print("\n=== TEST CASE 2: Aspirin patient prescribed waRFarin ===")
    patient_two = Patient(
        patient_id="PT-7721",
        age=45,
        weight_kg=70.0,
        allergies=[],
        active_medications=["aspirin"]
    )
    engine.prescribe(patient_two, "  waRFarin ", 5.0)

    # Test Case 3: Anaphylactic allergy check (prescribing penicillin to a penicillin-allergic patient)
    print("\n=== TEST CASE 3: Allergy detection ===")
    patient_three = Patient(
        patient_id="PT-1082",
        age=30,
        weight_kg=62.0,
        allergies=["penicillin"],
        active_medications=[]
    )
    engine.prescribe(patient_three, "Penicillin", 500)

    # Test Case 4: Dosage Anomaly Detection (prescribing 5000mg of Ibuprofen)
    print("\n=== TEST CASE 4: Dosage Anomaly Detection ===")
    patient_four = Patient(
        patient_id="PT-5561",
        age=35,
        weight_kg=75.0,
        allergies=[],
        active_medications=[]
    )
    engine.prescribe(patient_four, "Ibuprofen", 5000)

    # ==========================================
    # --- ADVANCED CLINICAL TEST SCENARIOS ---
    # ==========================================

    # Create new patients for clean testing environments
    patient_five = Patient(
        patient_id="PT-1001",
        age=45,
        weight_kg=90.0,
        allergies=["sulfa"],
        active_medications=["sildenafil"]
    )

    patient_six = Patient(
        patient_id="PT-2002",
        age=28,
        weight_kg=65.0,
        allergies=["latex"],
        active_medications=[] # Completely clean slate
    )

    print("\n=== TEST CASE 5: The Sneaky Bidirectional Catch ===")
    # The database maps "sildenafil" -> ["nitroglycerin"]. 
    # Here, the patient is ON sildenafil, and the doctor prescribes Nitroglycerin.
    # This proves the engine successfully checks Path B (Active Med -> New Med).
    engine.prescribe(patient_five, "Nitroglycerin", 2.5)

    print("\n=== TEST CASE 6: The Boundary Dosage ===")
    # The historical mean for Ibuprofen is ~488mg with an SD of ~213mg.
    # 800mg is a strong dose, but the Z-score is roughly 1.46. 
    # Since 1.46 is LESS than our 2.5 threshold, the AI should recognize it as safe and clear it.
    engine.prescribe(patient_six, "Ibuprofen", 800)

    print("\n=== TEST CASE 7: The Perfect 'Happy Path' ===")
    # The patient has no conflicting medications and no relevant allergies.
    # A standard 81mg dose of Aspirin should pass all deterministic and probabilistic nets.
    engine.prescribe(patient_six, "Aspirin", 81)
