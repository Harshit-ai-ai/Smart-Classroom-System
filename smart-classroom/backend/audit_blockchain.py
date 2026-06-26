"""
CSTPE Blockchain Audit Log (Feature 8)
Implements an append-only, tamper-evident hash-chain for attendance events.
Each block contains the event data, a timestamp, and the hash of the previous block,
forming a local blockchain. Any modification to a past record would break the chain.
"""

import hashlib
import json
import os
from datetime import datetime

CHAIN_FILE = os.path.join(os.path.dirname(__file__), "audit_chain.jsonl")


class AuditBlockchain:
    """
    A local, permissioned blockchain for immutable attendance logging.
    Each block is linked to the previous block via SHA-256 hashing,
    creating a tamper-evident audit trail.
    """

    def __init__(self):
        self._last_hash = self._get_last_hash()

    def append_event(self, event_type, student_name, data):
        """
        Append a new event to the audit chain.
        event_type: 'attendance_update', 'session_start', 'session_end', etc.
        """
        block = {
            "index": self._get_chain_length(),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "student": student_name,
            "data": data,
            "prev_hash": self._last_hash,
        }

        # Compute this block's hash
        block_bytes = json.dumps(block, sort_keys=True).encode()
        block["hash"] = hashlib.sha256(block_bytes).hexdigest()

        # Append to the chain file
        with open(CHAIN_FILE, "a") as f:
            f.write(json.dumps(block) + "\n")

        self._last_hash = block["hash"]
        return block

    def verify_chain(self):
        """
        Verify the integrity of the entire audit chain.
        Returns (is_valid, error_message_or_none, block_count).
        """
        if not os.path.exists(CHAIN_FILE):
            return True, None, 0

        prev_hash = "genesis"
        count = 0

        with open(CHAIN_FILE, "r") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                block = json.loads(line)
                count += 1

                # Check previous hash linkage
                if block.get("prev_hash") != prev_hash:
                    return False, f"Chain broken at block {line_no}: prev_hash mismatch", count

                # Recompute the hash (excluding the stored hash field)
                stored_hash = block.pop("hash")
                recomputed = hashlib.sha256(
                    json.dumps(block, sort_keys=True).encode()
                ).hexdigest()

                if recomputed != stored_hash:
                    return False, f"Chain tampered at block {line_no}: hash mismatch", count

                prev_hash = stored_hash
                block["hash"] = stored_hash

        return True, None, count

    def get_recent_events(self, limit=50):
        """Retrieve the most recent audit events."""
        if not os.path.exists(CHAIN_FILE):
            return []

        events = []
        with open(CHAIN_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))

        return events[-limit:]

    def get_student_history(self, student_name, limit=20):
        """Retrieve audit events for a specific student."""
        events = self.get_recent_events(limit=1000)
        return [e for e in events if e.get("student") == student_name][-limit:]

    def _get_last_hash(self):
        if not os.path.exists(CHAIN_FILE):
            return "genesis"

        last_line = None
        with open(CHAIN_FILE, "r") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()

        if last_line:
            block = json.loads(last_line)
            return block.get("hash", "genesis")

        return "genesis"

    def _get_chain_length(self):
        if not os.path.exists(CHAIN_FILE):
            return 0
        with open(CHAIN_FILE, "r") as f:
            return sum(1 for line in f if line.strip())


# Singleton
audit_chain = AuditBlockchain()
