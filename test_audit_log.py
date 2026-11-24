import hashlib
import json
import os
import tempfile
import unittest

import audit_log


class AuditLogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "audit.log")

    def tearDown(self):
        self._tmp.cleanup()

    def add(self, n):
        for i in range(n):
            audit_log.append_event({"patient_id": f"P{i}", "drug": "aspirin"}, self.path)

    def lines(self):
        with open(self.path, encoding="utf-8") as f:
            return f.read().splitlines()

    def write_lines(self, lines):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def test_empty_or_missing_log_is_ok(self):
        self.assertEqual(audit_log.verify(self.path), (True, []))

    def test_first_entry_links_to_genesis(self):
        self.add(1)
        event = json.loads(audit_log.read_entries(self.path)[0][0])
        self.assertEqual(event["prev_hash"], audit_log.GENESIS)

    def test_entries_are_chained(self):
        self.add(3)
        entries = audit_log.read_entries(self.path)
        self.assertEqual(json.loads(entries[1][0])["prev_hash"], entries[0][1])
        self.assertEqual(json.loads(entries[2][0])["prev_hash"], entries[1][1])
        self.assertEqual(audit_log.verify(self.path), (True, []))

    def test_edited_entry_detected(self):
        self.add(3)
        lines = self.lines()
        lines[3] = lines[3].replace("P1", "P9")  # EVENT line of entry 2
        self.write_lines(lines)
        ok, problems = audit_log.verify(self.path)
        self.assertFalse(ok)
        self.assertTrue(any("entry 2" in p and "edited" in p for p in problems))

    def test_deleted_middle_entry_detected(self):
        self.add(3)
        lines = self.lines()
        del lines[3:6]  # remove entry 2 completely (EVENT, HASH, ---)
        self.write_lines(lines)
        ok, problems = audit_log.verify(self.path)
        self.assertFalse(ok)
        self.assertTrue(any("chain broken" in p for p in problems))

    def test_edit_with_recomputed_own_hash_still_breaks_chain(self):
        self.add(3)
        lines = self.lines()
        event = json.loads(lines[3][len("EVENT: "):])
        event["patient_id"] = "FORGED"
        forged = json.dumps(event, sort_keys=True)
        lines[3] = "EVENT: " + forged
        lines[4] = "HASH: " + hashlib.sha256(forged.encode()).hexdigest()
        self.write_lines(lines)
        ok, problems = audit_log.verify(self.path)
        self.assertFalse(ok)
        self.assertTrue(any("entry 3" in p and "chain broken" in p for p in problems))

    def test_old_unchained_entries_still_verify_and_chain_continues(self):
        old = json.dumps({"patient_id": "OLD", "drug": "x"}, sort_keys=True)
        old_hash = hashlib.sha256(old.encode()).hexdigest()
        self.write_lines([f"EVENT: {old}", f"HASH: {old_hash}", "---"])
        audit_log.append_event({"patient_id": "NEW"}, self.path)
        entries = audit_log.read_entries(self.path)
        self.assertEqual(json.loads(entries[1][0])["prev_hash"], old_hash)
        self.assertEqual(audit_log.verify(self.path), (True, []))


if __name__ == "__main__":
    unittest.main()
