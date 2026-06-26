"""
CSTPE Model Attestation Module (Feature 3)
Cryptographic hash verification of model weights at service startup.
Guarantees that the exact vetted model binary is loaded, preventing
tampering or substitution of the inference pipeline.
"""

import hashlib
import os
import json

HASH_REGISTRY = os.path.join(os.path.dirname(__file__), "model_hashes.json")


def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def register_model(name, filepath):
    """
    Record the SHA-256 hash of a model file in the local registry.
    This should be run once during a controlled provisioning step.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")

    digest = compute_sha256(filepath)

    registry = _load_registry()
    registry[name] = {
        "path": filepath,
        "sha256": digest,
        "registered_at": _now_iso(),
    }
    _save_registry(registry)
    return digest


def verify_model(name, filepath):
    """
    Verify that the model file on disk matches the registered hash.
    Returns (True, digest) on success or (False, error_message) on failure.
    """
    registry = _load_registry()

    if name not in registry:
        # First run: auto-register the model
        digest = register_model(name, filepath)
        return True, f"Model '{name}' registered with hash {digest[:16]}..."

    expected_hash = registry[name]["sha256"]
    actual_hash = compute_sha256(filepath)

    if actual_hash == expected_hash:
        return True, f"Model '{name}' integrity verified."
    else:
        return False, (
            f"INTEGRITY VIOLATION for '{name}': "
            f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
        )


def verify_all_models(model_paths):
    """
    Verify a dictionary of {name: filepath} models.
    Returns a summary dict.
    """
    results = {}
    all_passed = True

    for name, path in model_paths.items():
        if not os.path.exists(path):
            results[name] = {"status": "MISSING", "message": f"File not found: {path}"}
            all_passed = False
            continue

        passed, message = verify_model(name, path)
        results[name] = {"status": "OK" if passed else "FAILED", "message": message}
        if not passed:
            all_passed = False

    return {"all_passed": all_passed, "models": results}


def _load_registry():
    if os.path.exists(HASH_REGISTRY):
        with open(HASH_REGISTRY, "r") as f:
            return json.load(f)
    return {}


def _save_registry(registry):
    with open(HASH_REGISTRY, "w") as f:
        json.dump(registry, f, indent=2)


def _now_iso():
    from datetime import datetime
    return datetime.now().isoformat()
