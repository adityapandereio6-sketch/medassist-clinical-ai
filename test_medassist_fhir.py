import os
import tempfile
import unittest

import fhir_resources as fhir
from medassist import ClinicalSafetyEngine
from medassist_fhir import check_medication_request, patient_from_bundle


class MedAssistFhirTest(unittest.TestCase):
    def setUp(self):
        # Audit log is written to the current folder, so use a throwaway one.
        self._old_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        self.engine = ClinicalSafetyEngine()

    def tearDown(self):
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def bundle(self, allergies=(), active=()):
        resources = [fhir.make_patient("1960-01-01", "male", patient_id="p1")]
        resources += [fhir.make_allergy("p1", a) for a in allergies]
        resources += [fhir.make_medication_request("p1", m, 5) for m in active]
        return fhir.make_bundle(resources)

    def test_patient_built_from_bundle(self):
        p = patient_from_bundle(self.bundle(["penicillin"], ["warfarin"]), "p1")
        self.assertEqual(p.allergies, ["penicillin"])
        self.assertEqual(p.active_medications, ["warfarin"])
        self.assertGreater(p.age, 60)

    def test_missing_patient_rejected(self):
        with self.assertRaises(fhir.FhirValidationError):
            patient_from_bundle(self.bundle(), "nobody")

    def test_interaction_blocked_and_logged(self):
        req = fhir.make_medication_request("p1", "aspirin", 81)
        result = check_medication_request(self.engine, self.bundle(active=["warfarin"]), req)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["alerts"][0]["severity"], "CRITICAL_INTERACTION")
        self.assertTrue(os.path.exists("clinical_audit.log"))

    def test_allergy_blocked(self):
        req = fhir.make_medication_request("p1", "penicillin", 500)
        result = check_medication_request(self.engine, self.bundle(allergies=["penicillin"]), req)
        self.assertEqual(result["alerts"][0]["severity"], "CRITICAL_ALLERGY")

    def test_dosage_anomaly_blocked(self):
        req = fhir.make_medication_request("p1", "ibuprofen", 5000)
        result = check_medication_request(self.engine, self.bundle(), req)
        self.assertEqual(result["alerts"][0]["severity"], "DOSAGE_ANOMALY")

    def test_clear_prescription_not_logged(self):
        req = fhir.make_medication_request("p1", "aspirin", 81)
        result = check_medication_request(self.engine, self.bundle(), req)
        self.assertEqual(result, {"status": "CLEAR", "alerts": []})
        self.assertFalse(os.path.exists("clinical_audit.log"))


if __name__ == "__main__":
    unittest.main()
