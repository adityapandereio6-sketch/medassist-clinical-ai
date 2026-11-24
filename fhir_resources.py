"""Minimal FHIR R4 layer for MedAssist.

Builds and validates the three resources the safety engine needs
(Patient, AllergyIntolerance, MedicationRequest) and wraps them in a
Bundle. Pure standard library, no external packages.

Scope note: this is a *subset* validator. It checks required fields,
allowed codes and reference formats for these resources. It is not a
full FHIR profile validator (use HAPI FHIR / the official validator
for that), and you should say so honestly in interviews.
"""

from __future__ import annotations

import re
import uuid

ALLERGY_CLINICAL_SYSTEM = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
UCUM_SYSTEM = "http://unitsofmeasure.org"

# Small demo map: name -> RxNorm code. Verify codes on RxNav
# (https://mor.nlm.nih.gov/RxNav/) before claiming them as authoritative.
RXNORM_CODES = {
    "warfarin": "11289",
    "aspirin": "1191",
    "ibuprofen": "5640",
    "amoxicillin": "723",
}

MEDREQ_STATUSES = {"active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"}
MEDREQ_INTENTS = {"proposal", "plan", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"}
GENDERS = {"male", "female", "other", "unknown"}
_REF_RE = re.compile(r"^[A-Za-z]+/[A-Za-z0-9\-.]{1,64}$")
_DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


class FhirValidationError(ValueError):
    """Raised when a resource fails the subset validation."""


def _new_id() -> str:
    return str(uuid.uuid4())


def _normalize(name: str) -> str:
    return name.strip().lower()


def _codeable_concept(name: str) -> dict:
    n = _normalize(name)
    concept = {"text": n}
    if n in RXNORM_CODES:
        concept["coding"] = [{"system": RXNORM_SYSTEM, "code": RXNORM_CODES[n], "display": n}]
    return concept


def make_patient(birth_date: str, gender: str = "unknown", patient_id: str | None = None) -> dict:
    return validate({
        "resourceType": "Patient",
        "id": patient_id or _new_id(),
        "gender": gender,
        "birthDate": birth_date,
    })


def make_allergy(patient_id: str, substance: str) -> dict:
    return validate({
        "resourceType": "AllergyIntolerance",
        "id": _new_id(),
        "clinicalStatus": {"coding": [{"system": ALLERGY_CLINICAL_SYSTEM, "code": "active"}]},
        "code": _codeable_concept(substance),
        "patient": {"reference": f"Patient/{patient_id}"},
    })


def make_medication_request(patient_id: str, medication: str, dose_mg: float,
                            status: str = "active", intent: str = "order") -> dict:
    return validate({
        "resourceType": "MedicationRequest",
        "id": _new_id(),
        "status": status,
        "intent": intent,
        "medicationCodeableConcept": _codeable_concept(medication),
        "subject": {"reference": f"Patient/{patient_id}"},
        "dosageInstruction": [{
            "doseAndRate": [{
                "doseQuantity": {"value": dose_mg, "unit": "mg", "system": UCUM_SYSTEM, "code": "mg"}
            }]
        }],
    })


def make_bundle(resources: list[dict]) -> dict:
    for r in resources:
        validate(r)
    return {
        "resourceType": "Bundle",
        "id": _new_id(),
        "type": "collection",
        "entry": [{"resource": r} for r in resources],
    }


# ---------------------------------------------------------------- validation

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise FhirValidationError(msg)


def _check_ref(ref: dict, expected_type: str, where: str) -> None:
    _require(isinstance(ref, dict) and "reference" in ref, f"{where}.reference is required")
    _require(bool(_REF_RE.match(ref["reference"])), f"{where}.reference is malformed: {ref['reference']!r}")
    _require(ref["reference"].startswith(expected_type + "/"), f"{where} must reference {expected_type}")


def validate(resource: dict) -> dict:
    """Validate a resource (subset rules). Returns it unchanged if valid."""
    _require(isinstance(resource, dict), "resource must be a dict")
    rtype = resource.get("resourceType")
    _require(rtype in {"Patient", "AllergyIntolerance", "MedicationRequest", "Bundle"},
             f"unsupported resourceType: {rtype!r}")

    if rtype == "Patient":
        _require(resource.get("gender", "unknown") in GENDERS, "Patient.gender invalid")
        bd = resource.get("birthDate")
        _require(isinstance(bd, str) and bool(_DATE_RE.match(bd)), "Patient.birthDate must be YYYY[-MM[-DD]]")

    elif rtype == "AllergyIntolerance":
        _require(bool(resource.get("code", {}).get("text") or resource.get("code", {}).get("coding")),
                 "AllergyIntolerance.code is required")
        _check_ref(resource.get("patient"), "Patient", "AllergyIntolerance.patient")

    elif rtype == "MedicationRequest":
        _require(resource.get("status") in MEDREQ_STATUSES, "MedicationRequest.status invalid")
        _require(resource.get("intent") in MEDREQ_INTENTS, "MedicationRequest.intent invalid")
        mcc = resource.get("medicationCodeableConcept", {})
        _require(bool(mcc.get("text") or mcc.get("coding")), "MedicationRequest.medicationCodeableConcept required")
        _check_ref(resource.get("subject"), "Patient", "MedicationRequest.subject")
        dose = dose_mg(resource)
        _require(dose is not None and dose > 0, "MedicationRequest needs a positive dose in mg")

    elif rtype == "Bundle":
        _require(resource.get("type") == "collection", "only collection bundles are supported")
        for e in resource.get("entry", []):
            validate(e.get("resource"))

    return resource


# ------------------------------------------------------------------ readers

def medication_name(med_request: dict) -> str:
    return _normalize(med_request["medicationCodeableConcept"].get("text", ""))


def dose_mg(med_request: dict) -> float | None:
    try:
        q = med_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]
    except (KeyError, IndexError, TypeError):
        return None
    if q.get("code") != "mg":
        return None
    return float(q["value"])


def allergies_in(bundle: dict) -> set[str]:
    return {
        _normalize(e["resource"]["code"].get("text", ""))
        for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "AllergyIntolerance"
    }


def active_medications_in(bundle: dict) -> set[str]:
    return {
        medication_name(e["resource"])
        for e in bundle.get("entry", [])
        if e["resource"]["resourceType"] == "MedicationRequest" and e["resource"]["status"] == "active"
    }
