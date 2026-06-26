"""
CSTPE Federated Learning Server (Feature 7 - Part 2)
Central aggregation server that merges weight deltas from multiple
edge devices using Federated Averaging (FedAvg).
"""

import numpy as np
import json
import os
import glob
from datetime import datetime

DELTAS_DIR = os.path.join(os.path.dirname(__file__), "fed_deltas")
GLOBAL_MODEL = os.path.join(os.path.dirname(__file__), "fed_global_model.json")


class FederatedServer:
    """
    Central server for federated averaging.
    Collects weight deltas from edge clients and produces an updated
    global model using weighted averaging based on sample counts.
    """

    def __init__(self):
        self._global_weights = self._load_global_model()
        os.makedirs(DELTAS_DIR, exist_ok=True)

    def aggregate(self):
        """
        Perform federated averaging over all pending deltas.
        Returns the updated global weights.
        """
        delta_files = glob.glob(os.path.join(DELTAS_DIR, "delta_*.json"))

        if not delta_files:
            return None, "No deltas available for aggregation"

        deltas = []
        weights = []  # sample-count weights for weighted averaging

        for filepath in delta_files:
            with open(filepath, "r") as f:
                record = json.load(f)
            deltas.append(np.array(record["delta"]))
            weights.append(record.get("sample_count", 1))

        total_samples = sum(weights)
        if total_samples == 0:
            return None, "No samples in deltas"

        # Weighted average of deltas
        avg_delta = np.zeros_like(deltas[0])
        for delta, w in zip(deltas, weights):
            avg_delta += delta * (w / total_samples)

        # Apply aggregated delta to global model
        self._global_weights = self._global_weights + avg_delta

        # Save updated global model
        self._save_global_model()

        # Archive processed deltas
        self._archive_deltas(delta_files)

        return self._global_weights, f"Aggregated {len(deltas)} client updates ({total_samples} total samples)"

    def get_global_model(self):
        """Return the current global model weights."""
        return self._global_weights.copy()

    def get_status(self):
        """Return the current aggregation status."""
        pending = len(glob.glob(os.path.join(DELTAS_DIR, "delta_*.json")))
        return {
            "pending_deltas": pending,
            "model_dim": len(self._global_weights),
            "last_aggregation": self._get_last_aggregation_time(),
        }

    def _load_global_model(self, dim=128):
        if os.path.exists(GLOBAL_MODEL):
            with open(GLOBAL_MODEL, "r") as f:
                data = json.load(f)
            return np.array(data["weights"])
        return np.zeros(dim)

    def _save_global_model(self):
        data = {
            "weights": self._global_weights.tolist(),
            "updated_at": datetime.now().isoformat(),
        }
        with open(GLOBAL_MODEL, "w") as f:
            json.dump(data, f)

    def _archive_deltas(self, filepaths):
        archive_dir = os.path.join(DELTAS_DIR, "archived")
        os.makedirs(archive_dir, exist_ok=True)
        for fp in filepaths:
            basename = os.path.basename(fp)
            os.rename(fp, os.path.join(archive_dir, basename))

    def _get_last_aggregation_time(self):
        if os.path.exists(GLOBAL_MODEL):
            with open(GLOBAL_MODEL, "r") as f:
                data = json.load(f)
            return data.get("updated_at", "never")
        return "never"


# Singleton
fed_server = FederatedServer()
