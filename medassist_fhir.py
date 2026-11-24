"""FHIR adapter for MedAssist.

Reads a FHIR Bundle (Patient + AllergyIntolerance + active MedicationRequest
resources) plus a proposed MedicationRequest, and runs the existing
ClinicalSafetyEngine checks on them. medassist.py is not modified.
"""

from datetime import date

import fhir_resources as fhir
from medassist import ClinicalSafetyEngine, Patient


def _age_from_birth_date(birth_date: str) -> int:
    year = int(birth_date[:4])
    month = int(birth_date[5:7]) if len(birth_date) >= 7 else 1
    day = int(birth_date[8:10]) if len(birth_date) >= 10 else 1
    today = date.today()
    return today.year - year - ((today.month, today.day) < (month, day))


def patient_from_bundle(bundle: dict, patient_id: str) -> Patient:
    """Build the engine's Patient object from FHIR resources in a bundle."""
    fhir.validate(bundle)
    fhir_patient = next(
        (e["resource"] for e in bundle["entry"]
         if e["resource"]["resourceType"] == "Patient" and e["resource"]["id"] == patient_id),
        None,
    )
    if fhir_patient is None:
        raise fhir.FhirValidationError(f"Patient/{patient_id} not found in bundle")

    # Weight is a FHIR Observation, which we don't model yet; the engine
    # does not use it for any check, so it stays None.
    return Patient(
        patient_id=patient_id,
        age=_age_from_birth_date(fhir_patient["birthDate"]),
        weight_kg=None,
        allergies=sorted(fhir.allergies_in(bundle)),
        active_medications=sorted(fhir.active_medications_in(bundle)),
    )


def check_medication_request(engine: ClinicalSafetyEngine, bundle: dict, med_request: dict) -> dict:
    """Run all safety checks for a proposed MedicationRequest.

    Returns {"status": "CLEAR" | "BLOCKED", "alerts": [...]}.
    Blocked requests are written to the SHA-256 audit log, like prescribe().
    """
    fhir.validate(med_request)
    patient_id = med_request["subject"]["reference"].split("/", 1)[1]
    patient = patient_from_bundle(bundle, patient_id)
    drug = fhir.medication_name(med_request)
    dose = fhir.dose_mg(med_request)

    alerts = (
        engine.check_allergy(patient, drug)
        + engine.check_interaction(patient, drug)
        + engine.check_dosage_anomaly(drug, dose)
    )
    if alerts:
        engine.generate_audit_log(patient, drug, dose, alerts)
        return {"status": "BLOCKED", "alerts": alerts}
    return {"status": "CLEAR", "alerts": []}
