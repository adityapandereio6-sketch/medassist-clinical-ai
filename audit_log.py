"""Hash-chained audit log for MedAssist.

Each entry stores the SHA-256 hash of the previous entry ("prev_hash"),
so editing, deleting, inserting or reordering an entry in the middle of
the log breaks the chain and verify() reports it.

Log format (same as before, so old entries stay readable):

    EVENT: {json}
    HASH: {sha256 of that json string}
    ---

Limits (be honest about these in interviews): the chain cannot detect
someone deleting entries from the END of the log, or rewriting the whole
file and recomputing every hash. Real systems also anchor the latest hash
somewhere separate (another server, a signed timestamp).
"""

import hashlib
import json
import os
import threading

GENESIS = "GENESIS"
DEFAULT_PATH = "clinical_audit.log"
_lock = threading.Lock()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_entries(path: str = DEFAULT_PATH) -> list[tuple[str, str]]:
    """Return [(json_string, stored_hash), ...] in file order."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    entries = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("EVENT: "):
            if i + 1 >= len(lines) or not lines[i + 1].startswith("HASH: "):
                raise ValueError(f"malformed log: EVENT at line {i + 1} has no HASH line")
            entries.append((lines[i][len("EVENT: "):].strip(), lines[i + 1][len("HASH: "):].strip()))
            i += 2
        else:
            i += 1  # separator or blank line
    return entries


def last_hash(path: str = DEFAULT_PATH) -> str:
    entries = read_entries(path)
    return entries[-1][1] if entries else GENESIS


def append_event(event: dict, path: str = DEFAULT_PATH) -> str:
    """Append an event linked to the previous entry. Returns its hash."""
    with _lock:
        record = dict(event)
        record["prev_hash"] = last_hash(path)
        json_string = json.dumps(record, sort_keys=True)
        event_hash = _sha256(json_string)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"EVENT: {json_string}\nHASH: {event_hash}\n---\n")
        return event_hash


def verify(path: str = DEFAULT_PATH) -> tuple[bool, list[str]]:
    """Check every hash and every chain link. Returns (ok, problems).

    Old entries written before chaining (no prev_hash) only get their own
    hash checked; the first chained entry must link to the last of them.
    """
    problems = []
    previous = None
    for n, (json_string, stored_hash) in enumerate(read_entries(path), start=1):
        if _sha256(json_string) != stored_hash:
            problems.append(f"entry {n}: hash mismatch (content was edited)")
        try:
            event = json.loads(json_string)
        except json.JSONDecodeError:
            problems.append(f"entry {n}: not valid JSON")
            event = {}
        if "prev_hash" in event:
            expected = previous if previous is not None else GENESIS
            if event["prev_hash"] != expected:
                problems.append(f"entry {n}: chain broken (an entry was removed, inserted or reordered)")
        previous = stored_hash
    return (not problems, problems)


if __name__ == "__main__":
    ok, problems = verify()
    print("Audit log OK" if ok else "AUDIT LOG PROBLEMS:")
    for p in problems:
        print(" -", p)
