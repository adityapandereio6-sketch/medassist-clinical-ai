import unittest

import fhir_resources as fhir


class FhirResourcesTest(unittest.TestCase):
    def setUp(self):
        self.patient = fhir.make_patient("1990-05-14", "male", patient_id="p1")

    def test_patient_valid(self):
        self.assertEqual(self.patient["resourceType"], "Patient")
        self.assertEqual(self.patient["id"], "p1")

    def test_patient_bad_birthdate(self):
        with self.assertRaises(fhir.FhirValidationError):
            fhir.make_patient("14/05/1990")

    def test_patient_bad_gender(self):
        with self.assertRaises(fhir.FhirValidationError):
            fhir.make_patient("1990-05-14", "robot")

    def test_allergy_references_patient(self):
        a = fhir.make_allergy("p1", "Penicillin")
        self.assertEqual(a["patient"]["reference"], "Patient/p1")
        self.assertEqual(a["code"]["text"], "penicillin")

    def test_medication_request_has_rxnorm_and_ucum_dose(self):
        m = fhir.make_medication_request("p1", "Warfarin", 5)
        coding = m["medicationCodeableConcept"]["coding"][0]
        self.assertEqual(coding["system"], fhir.RXNORM_SYSTEM)
        self.assertEqual(fhir.dose_mg(m), 5.0)

    def test_unknown_drug_still_valid_without_coding(self):
        m = fhir.make_medication_request("p1", "mysterydrug", 10)
        self.assertNotIn("coding", m["medicationCodeableConcept"])

    def test_negative_dose_rejected(self):
        with self.assertRaises(fhir.FhirValidationError):
            fhir.make_medication_request("p1", "aspirin", -1)

    def test_bad_status_rejected(self):
        with self.assertRaises(fhir.FhirValidationError):
            fhir.make_medication_request("p1", "aspirin", 81, status="maybe")

    def test_malformed_reference_rejected(self):
        bad = fhir.make_medication_request("p1", "aspirin", 81)
        bad["subject"]["reference"] = "not a reference"
        with self.assertRaises(fhir.FhirValidationError):
            fhir.validate(bad)

    def test_wrong_reference_type_rejected(self):
        bad = fhir.make_allergy("p1", "penicillin")
        bad["patient"]["reference"] = "Practitioner/p1"
        with self.assertRaises(fhir.FhirValidationError):
            fhir.validate(bad)

    def test_unsupported_resource_type(self):
        with self.assertRaises(fhir.FhirValidationError):
            fhir.validate({"resourceType": "Observation"})

    def test_bundle_readers(self):
        bundle = fhir.make_bundle([
            self.patient,
            fhir.make_allergy("p1", "penicillin"),
            fhir.make_medication_request("p1", "warfarin", 5),
            fhir.make_medication_request("p1", "ibuprofen", 200, status="stopped"),
        ])
        self.assertEqual(fhir.allergies_in(bundle), {"penicillin"})
        self.assertEqual(fhir.active_medications_in(bundle), {"warfarin"})

    def test_bundle_rejects_invalid_member(self):
        bad = fhir.make_allergy("p1", "penicillin")
        bad["patient"] = {}
        with self.assertRaises(fhir.FhirValidationError):
            fhir.make_bundle([bad])


if __name__ == "__main__":
    unittest.main()
