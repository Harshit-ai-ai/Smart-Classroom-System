"""
CSTPE Policy Engine (Feature 6)
Domain-Specific Language (DSL) parser for runtime-configurable attendance policies.
The DSL is a simple key=value format that can be updated without redeploying code.
"""

import os
import re

POLICY_FILE = os.path.join(os.path.dirname(__file__), "policy.dsl")


class PolicyEngine:
    def __init__(self, policy_path=None):
        self.policy_path = policy_path or POLICY_FILE
        self._values = {}
        self.reload()

    def reload(self):
        self._values = {}
        if not os.path.exists(self.policy_path):
            return

        with open(self.policy_path, "r") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$", line)
                if not match:
                    continue

                key = match.group(1)
                raw_value = match.group(2).strip()

                # Parse the value type
                self._values[key] = self._parse_value(raw_value)

    def _parse_value(self, raw):
        # Boolean
        if raw.lower() in ("true", "yes"):
            return True
        if raw.lower() in ("false", "no"):
            return False

        # Float
        if "." in raw:
            try:
                return float(raw)
            except ValueError:
                pass

        # Integer
        try:
            return int(raw)
        except ValueError:
            pass

        # String (strip quotes if present)
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            return raw[1:-1]

        return raw

    def get(self, key, default=None):
        return self._values.get(key, default)

    def get_int(self, key, default=0):
        val = self._values.get(key, default)
        return int(val) if val is not None else default

    def get_float(self, key, default=0.0):
        val = self._values.get(key, default)
        return float(val) if val is not None else default

    def get_all(self):
        return self._values.copy()

    def set_value(self, key, value):
        self._values[key] = value
        self._persist()

    def _persist(self):
        lines = []
        for key, value in sorted(self._values.items()):
            lines.append(f"{key} = {value}")

        with open(self.policy_path, "w") as f:
            f.write("# CSTPE Attendance Policy DSL (auto-generated)\n\n")
            f.write("\n".join(lines))
            f.write("\n")


# Singleton instance
policy = PolicyEngine()
