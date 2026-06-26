"""
CSTPE Comprehensive Test Suite
Tests all 10 novel patent features end-to-end.
"""

import os
import sys
import time
import numpy as np
import json

# Ensure we are in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} -- {detail}")


print("=" * 60)
print("CSTPE COMPREHENSIVE TEST SUITE")
print("=" * 60)

# -------------------------------------------------------
print("\n[1] Policy Engine (Feature 6)")
# -------------------------------------------------------
from policy_engine import PolicyEngine

pe = PolicyEngine()
pe.reload()
test("Policy loads threshold_minutes", pe.get("threshold_minutes") == 40)
test("Policy loads gap_seconds", pe.get("gap_seconds") == 10)
test("Policy loads face_confidence as float", isinstance(pe.get("face_confidence"), float))
test("Policy get_all returns dict", isinstance(pe.get_all(), dict))
test("Policy has fusion weights", pe.get("weight_face") is not None)

# -------------------------------------------------------
print("\n[2] Config Module")
# -------------------------------------------------------
from config import load_config, is_feature_enabled, get_threshold

cfg = load_config()
test("Config has features key", "features" in cfg)
test("Config has thresholds key", "thresholds" in cfg)
test("YOLO liveness enabled", is_feature_enabled("yolo_liveness"))
test("Blockchain audit enabled", is_feature_enabled("blockchain_audit"))
test("Face confidence threshold", get_threshold("face_confidence") == 0.55)

# -------------------------------------------------------
print("\n[3] Model Attestation (Feature 3)")
# -------------------------------------------------------
from model_attestation import compute_sha256, register_model, verify_model, verify_all_models

# Create a temp file to test
test_file = "__test_model.bin"
with open(test_file, "wb") as f:
    f.write(b"test model data for attestation")

digest = compute_sha256(test_file)
test("SHA256 produces 64-char hex", len(digest) == 64)

ok, msg = verify_model("test_model", test_file)
test("First verify auto-registers", ok)

ok2, msg2 = verify_model("test_model", test_file)
test("Second verify matches", ok2)

# Tamper the file
with open(test_file, "wb") as f:
    f.write(b"tampered data")
ok3, msg3 = verify_model("test_model", test_file)
test("Tampered file detected", not ok3)

os.remove(test_file)
# Clean up registry
if os.path.exists("model_hashes.json"):
    os.remove("model_hashes.json")

# -------------------------------------------------------
print("\n[4] Entropy Engine (Feature 2)")
# -------------------------------------------------------
from entropy_engine import EntropyEngine

ee = EntropyEngine()

# Feed identical keypoints -> low entropy -> tight gap
for _ in range(10):
    kp = np.ones((33, 3)) * 0.5
    kp[:, 2] = 0.9
    gap = ee.update("TestStudent", kp)

test("Low entropy gives tight gap", gap <= 10, f"gap={gap}")

# Feed random keypoints -> high entropy -> relaxed gap
ee2 = EntropyEngine()
for _ in range(10):
    kp = np.random.uniform(0, 1, (33, 3))
    gap2 = ee2.update("ActiveStudent", kp)

test("High entropy gives wider gap", gap2 >= 5, f"gap={gap2}")

# -------------------------------------------------------
print("\n[5] Pose Engine (Feature 2)")
# -------------------------------------------------------
from pose_engine import PoseEngine

pe2 = PoseEngine()
kp = pe2.extract_keypoints(np.zeros((480, 640, 3), dtype=np.uint8))
test("Pose engine returns keypoints", kp is not None)
test("Keypoints shape is (33, 3)", kp.shape == (33, 3))

# -------------------------------------------------------
print("\n[6] Iris Engine (Feature 1)")
# -------------------------------------------------------
from iris_engine import IrisEngine

ie = IrisEngine()
code = ie.enroll("Alice")
test("Iris code is 256 bits", len(code) == 256)

score, match = ie.match("Alice")
test("Iris self-match succeeds", match and score > 0.7, f"score={score}")

# -------------------------------------------------------
print("\n[7] Voice Engine (Feature 1)")
# -------------------------------------------------------
from voice_engine import VoiceEngine

ve = VoiceEngine()
ve.enroll("Alice")
sim, match = ve.verify_speaker("Alice")
test("Voice self-match succeeds", match and sim > 0.7, f"sim={sim}")

active, conf = ve.detect_activity("Alice")
test("Voice activity returns confidence", conf > 0, f"conf={conf}")

# -------------------------------------------------------
print("\n[8] Biometric Fusion (Feature 1)")
# -------------------------------------------------------
from fusion import BiometricFusion

bf = BiometricFusion()
score, accepted, details = bf.fuse("Alice", 0.9, 0.85, 0.8)
test("Fusion returns valid score", 0 <= score <= 1, f"score={score}")
test("High scores accepted", accepted)

score2, accepted2, _ = bf.fuse("Bob", 0.1, 0.1, 0.1)
test("Low scores eventually rejected", score2 < 0.7 or not accepted2, f"score={score2}")

# -------------------------------------------------------
print("\n[9] Session Recovery (Feature 10)")
# -------------------------------------------------------
from embedding_store import store_embedding, get_recent_embeddings, init_embedding_table
from session_recovery import SessionRecovery

# Reset for clean test
import sqlite3
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM embedding_store")
conn.commit()
conn.close()

emb = np.random.randn(128).astype(np.float32)
store_embedding("Alice", emb, "2026-01-01 00:00:00")

stored = get_recent_embeddings("Alice")
test("Embedding stored and retrieved", len(stored) == 1)
test("Embedding shape preserved", stored[0].shape == (128,))

sr = SessionRecovery()
match_name, sim = sr.attempt_recovery(emb)
test("Session recovery finds match", match_name == "Alice", f"match={match_name}")

# -------------------------------------------------------
print("\n[10] ZK Prover (Feature 4)")
# -------------------------------------------------------
from zk_prover import ZKPresenceProver

# Clean up any existing proof log
if os.path.exists("zk_proofs.jsonl"):
    os.remove("zk_proofs.jsonl")

zk = ZKPresenceProver()
proof = zk.generate_proof("Alice", "2026-01-01 00:00:00", "2026-01-01 00:00:05", True)
test("ZK proof has commitment", len(proof["commitment"]) == 64)
test("ZK proof has protocol", proof["protocol"] == "pedersen_commitment_v1")

ok, msg = zk.verify_proof(proof, "Alice", True)
test("ZK proof verification passes", ok, msg)

ok2, msg2 = zk.verify_proof(proof, "Bob", True)
test("ZK proof rejects wrong student", not ok2)

test("ZK proof count is 1", zk.get_proof_count() == 1)

# -------------------------------------------------------
print("\n[11] Blockchain Audit (Feature 8)")
# -------------------------------------------------------
from audit_blockchain import AuditBlockchain

# Clean up
if os.path.exists("audit_chain.jsonl"):
    os.remove("audit_chain.jsonl")

bc = AuditBlockchain()
block = bc.append_event("test_event", "Alice", {"score": 0.95})
test("Block has hash", len(block["hash"]) == 64)
test("Block has prev_hash genesis", block["prev_hash"] == "genesis")

block2 = bc.append_event("test_event_2", "Bob", {"score": 0.80})
test("Block2 chains to block1", block2["prev_hash"] == block["hash"])

valid, error, count = bc.verify_chain()
test("Chain integrity verified", valid, error)
test("Chain has 2 blocks", count == 2)

# -------------------------------------------------------
print("\n[12] Environmental Sensors (Feature 9)")
# -------------------------------------------------------
from env_sensors import EnvironmentalSensors

es = EnvironmentalSensors()
is_valid, readings, violations = es.check_environment()
test("Environment check returns valid", is_valid)
test("Readings have light_lux", "light_lux" in readings)
test("Readings have temperature", "temperature_celsius" in readings)
test("Light in reasonable range", 100 < readings["light_lux"] < 600)

# -------------------------------------------------------
print("\n[13] Federated Learning (Feature 7)")
# -------------------------------------------------------
from fed_client import FederatedClient
from fed_server import FederatedServer

# Clean up
import glob
for f in glob.glob("fed_deltas/delta_*.json"):
    os.remove(f)

fc = FederatedClient(device_id="test_device")
for i in range(15):
    fc.collect_sample(np.random.randn(128), is_genuine=i % 3 != 0)

test("Client collected 15 samples", fc.get_sample_count() == 15)

delta_path = fc.export_delta()
test("Delta exported", delta_path is not None and os.path.exists(delta_path))

fs = FederatedServer()
result, message = fs.aggregate()
test("Server aggregation succeeded", result is not None, message)

status = fs.get_status()
test("Server reports 0 pending", status["pending_deltas"] == 0)

# -------------------------------------------------------
print("\n[14] Attendance DB Integration")
# -------------------------------------------------------
from attendance_db import init_db, update_attendance, get_all_stats, reset_db

# Reset for clean test
if os.path.exists("attendance.db"):
    os.remove("attendance.db")
init_db()

stats = update_attendance(["Alice", "Bob"], metadata={
    "Alice": {"adaptive_gap": 8, "env_valid": True, "biometric_score": 0.92},
    "Bob": {"adaptive_gap": 12, "env_valid": True, "biometric_score": 0.88},
})
test("Two students inserted", len(stats) == 2)
test("Alice has 0 accumulated", stats[0]["accumulated_seconds"] == 0)

time.sleep(2)
stats2 = update_attendance(["Alice"], metadata={
    "Alice": {"adaptive_gap": 8, "env_valid": True, "biometric_score": 0.92},
})
test("Alice accumulates time", stats2[0]["accumulated_seconds"] >= 2)

# Gap test
time.sleep(11)
stats3 = update_attendance(["Alice"], metadata={
    "Alice": {"adaptive_gap": 8, "env_valid": True, "biometric_score": 0.92},
})
test("Gap blocks accumulation", stats3[0]["accumulated_seconds"] < 10)

all_stats = get_all_stats()
test("get_all_stats returns list", isinstance(all_stats, list))

# -------------------------------------------------------
print("\n[15] Edge Export Module (Feature 5)")
# -------------------------------------------------------
from scripts.export_onnx import generate_edge_report, get_model_size_mb

report = generate_edge_report()
test("Edge report returns list", isinstance(report, list))

size = get_model_size_mb("yolov8n.pt")
test("YOLO model size is reasonable", size > 5, f"size={size}MB")

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
print("=" * 60)

if failed > 0:
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
