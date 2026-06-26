"""
CSTPE Configuration Module
Central feature-toggle and parameter configuration for all patent modules.
"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "features": {
        "yolo_liveness": True,
        "multi_modal_biometrics": True,
        "adaptive_gap_threshold": True,
        "model_attestation": True,
        "zero_knowledge_proofs": True,
        "edge_inference": False,
        "policy_engine": True,
        "federated_learning": True,
        "blockchain_audit": True,
        "environmental_gating": True,
        "session_recovery": True,
    },
    "thresholds": {
        "attendance_minutes": 40,
        "gap_seconds": 10,
        "face_confidence": 0.55,
        "yolo_confidence": 0.6,
        "aspect_ratio_min": 0.8,
        "session_recovery_similarity": 0.85,
        "entropy_window_seconds": 5,
    },
    "environment": {
        "light_min_lux": 100,
        "light_max_lux": 2000,
        "temp_min_celsius": 15,
        "temp_max_celsius": 40,
    },
    "federated": {
        "aggregation_interval_hours": 24,
        "min_local_samples": 50,
        "learning_rate": 0.001,
    },
    "edge": {
        "use_onnx": False,
        "quantization": "INT8",
        "target_device": "cpu",
    },
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            user_config = json.load(f)
        merged = _deep_merge(DEFAULT_CONFIG, user_config)
        return merged
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def is_feature_enabled(feature_name):
    config = load_config()
    return config.get("features", {}).get(feature_name, False)


def get_threshold(name):
    config = load_config()
    return config.get("thresholds", {}).get(name)


def get_env_bounds():
    config = load_config()
    return config.get("environment", {})


# Initialize config file on first import
if not os.path.exists(CONFIG_FILE):
    save_config(DEFAULT_CONFIG)
