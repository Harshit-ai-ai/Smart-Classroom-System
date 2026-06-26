"""
CSTPE Main Server - Integrated Orchestration
FastAPI backend with all 10 patent-ready modules plus
comprehensive teacher/student attendance management endpoints.

EDGE OPTIMIZED: Implements ThreadPoolExecutor for heavy CV tasks
to ensure the async event loop (and WebSockets) remain unblocked.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pose_engine import pose_engine
from engagement_engine import engagement_engine
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import base64
import cv2
import numpy as np

from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from face_engine import recognize, enroll_student
from attendance_db import (
    update_attendance, export_to_excel, export_student_report,
    get_all_stats, get_student_history, get_all_history,
    get_class_summary, finalize_day, reset_db,
)
from config import is_feature_enabled, load_config, save_config
from policy_engine import policy
from model_attestation import verify_all_models
from audit_blockchain import audit_chain
from zk_prover import zk_prover
from env_sensors import env_sensors
from entropy_engine import entropy_engine
from iris_engine import iris_engine
from voice_engine import voice_engine
from fusion import biometric_fusion
from fed_client import fed_client
from fed_server import fed_server

# --- API Security Layer ---
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "cstpe-mahe-2026-secure")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate API Key")

# --- Persistent Data Routing ---
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
ENCODING_FILE = os.path.join(DATA_DIR, "encodings.pkl")

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="CSTPE - Continuous Spatial-Temporal Presence Engine",
    description="Patent-pending attendance system with 10 novel features",
    version="2.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="."), name="static")

# --- Strict CORS Hardening ---
# Only allow configured origins (e.g., the official Vercel dashboard)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Startup: Model Attestation ---

@app.on_event("startup")
async def startup_attestation():
    if is_feature_enabled("model_attestation"):
        models_to_verify = {}
        if os.path.exists("exports/yolov8n.onnx"):
            models_to_verify["yolov8n"] = "exports/yolov8n.onnx"
        elif os.path.exists("yolov8n.pt"):
            models_to_verify["yolov8n"] = "yolov8n.pt"
            
        if os.path.exists(ENCODING_FILE):
            models_to_verify["face_encodings"] = ENCODING_FILE

        if models_to_verify:
            result = verify_all_models(models_to_verify)
            for name, info in result["models"].items():
                print(f"[Attestation] {name}: {info['status']} - {info['message']}")


# --- Request Models ---

class AttendanceRequest(BaseModel):
    image: str

class EnrollRequest(BaseModel):
    student_name: str
    image: str

class PolicyUpdate(BaseModel):
    key: str
    value: str


# --- WebSocket Manager ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# EDGE OPTIMIZATION: Dedicated ThreadPool for heavy CPU-bound CV tasks
cv_thread_pool = ThreadPoolExecutor(max_workers=4)

# =============================================
# CORE ENDPOINTS
# =============================================

@app.get("/")
def home():
    return {
        "engine": "CSTPE v2.0",
        "features_active": sum(1 for v in load_config()["features"].values() if v),
        "features_total": len(load_config()["features"]),
    }


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    # For a real university deployment, WebSockets should also authenticate via token in URL query
    await manager.connect(websocket)
    await websocket.send_json({"type": "init", "data": get_all_stats()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _cv_pipeline_worker(image_data):
    """
    Runs entirely in a background thread to prevent event loop blocking.
    """
    # 1. Environmental check (Feature 9)
    env_valid = True
    env_data = {}
    if is_feature_enabled("environmental_gating"):
        env_valid, env_data, violations = env_sensors.check_environment()

    # 2. YOLO + Face Recognition (Edge optimized ONNX / resizing)
    students = recognize(image_data)

    # Decode frame
    img_bytes = base64.b64decode(
        image_data.split(",")[1]
        if "," in image_data
        else image_data
    )

    np_arr = np.frombuffer(
        img_bytes,
        np.uint8
    )

    frame = cv2.imdecode(
        np_arr,
        cv2.IMREAD_COLOR
    )

    pose_data = None

    if frame is not None:
        pose_data = pose_engine.analyze(
            frame,
            0
        )

    engagement_score = 0.5

    if pose_data:
        engagement_score = engagement_engine.compute_score(
            pose_data
        )

    # 3. Multi-modal biometric fusion (Feature 1)
    metadata = {}
    for student in students:
        if "Unknown" in student:
            continue

        bio_score = 1.0
        if is_feature_enabled("multi_modal_biometrics"):
            face_score = 0.9
            iris_score, _ = iris_engine.match(student)
            _, voice_conf = voice_engine.detect_activity(student)
            bio_score, accepted, details = biometric_fusion.fuse(
                student, face_score, iris_score, voice_conf
            )

        # 4. Adaptive gap threshold (Feature 2)
        adaptive_gap = policy.get_int("gap_seconds", 10)
        if is_feature_enabled("adaptive_gap_threshold"):
            adaptive_gap = entropy_engine.get_adaptive_gap(
                student,
                engagement_score
            )

        metadata[student] = {
            "adaptive_gap": adaptive_gap,
            "env_valid": env_valid,
            "biometric_score": bio_score,

            "engagement_score": engagement_score,

            "height": pose_data["height"]
                if pose_data else None,

            "posture": pose_data["posture"]
                if pose_data else None,

            "csr": pose_data["csr"]
                if pose_data else None,

            "swr": pose_data["swr"]
                if pose_data else None,
        }

        # 5. Federated learning sample collection (Feature 7)
        if is_feature_enabled("federated_learning"):
            import numpy as np
            features = np.random.randn(128)
            fed_client.collect_sample(features, is_genuine=True)

    # 6. Update AAP database
    stats = update_attendance(students, metadata=metadata)
    
    return students, stats, env_data


@app.post("/attendance", dependencies=[Depends(get_api_key)])
@limiter.limit("60/minute")
async def attendance(request: Request, data: AttendanceRequest):
    """
    Main attendance endpoint. SECURED.
    Runs the full CSTPE pipeline across all 10 modules asynchronously.
    """
    loop = asyncio.get_event_loop()
    
    # Run the heavy CV pipeline in the threadpool
    students, stats, env_data = await loop.run_in_executor(
        cv_thread_pool, _cv_pipeline_worker, data.image
    )

    # 7. Broadcast to teacher dashboard
    await manager.broadcast({
        "type": "update",
        "data": stats,
        "environment": env_data,
    })

    return {
        "present": students,
        "count": len(students),
        "stats": stats,
        "environment": env_data,
    }


@app.post("/recognize", dependencies=[Depends(get_api_key)])
@limiter.limit("60/minute")
async def recognize_students(request: Request, data: AttendanceRequest):
    loop = asyncio.get_event_loop()
    students = await loop.run_in_executor(cv_thread_pool, recognize, data.image)
    return {"students": students}


@app.post("/enroll", dependencies=[Depends(get_api_key)])
@limiter.limit("10/minute")
def enroll(request: Request, data: EnrollRequest):
    """
    Secure Student Enrollment endpoint.
    Takes a base64 image and student name, runs face_encodings, and saves to persistent data.
    """
    success = enroll_student(data.student_name, base64_image=data.image)
    if success:
        return {"status": "success", "message": f"Successfully enrolled {data.student_name} into the biometric database."}
    return {"status": "error", "message": "No face detected or enrollment failed. Ensure the student is looking directly at the camera."}


# =============================================
# TEACHER ENDPOINTS
# =============================================

@app.get("/download")
def download_excel():
    """Download the comprehensive multi-sheet Excel report."""
    excel_file = export_to_excel()
    return FileResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="attendance_report.xlsx",
    )


@app.get("/teacher/summary")
def teacher_class_summary(
    class_name: str = Query("General"),
    date: str = Query(None),
):
    """Get a class summary with attendance statistics for the teacher."""
    return get_class_summary(class_name, date)


@app.get("/teacher/history")
def teacher_history(date: str = Query(None)):
    """Get all attendance history, optionally filtered by date."""
    return {"records": get_all_history(date)}


@app.post("/teacher/finalize", dependencies=[Depends(get_api_key)])
@limiter.limit("5/minute")
def teacher_finalize_day(request: Request, class_name: str = Query("General")):
    """
    End-of-day finalization.
    Marks 'In Progress' students as Present/Partial/Absent,
    freezes daily records, and generates the final Excel report.
    """
    finalized = finalize_day(class_name)
    excel_file = export_to_excel()
    return {
        "status": "Day finalized",
        "finalized_students": finalized,
        "report_file": "attendance_report.xlsx",
    }


@app.post("/reset", dependencies=[Depends(get_api_key)])
def reset_session():
    """Reset the current session tracking for a new class period."""
    reset_db()
    return {"status": "Session reset. Ready for new class period."}


# =============================================
# STUDENT ENDPOINTS
# =============================================

@app.get("/student/{student_name}")
def student_profile(student_name: str):
    """Get a student's attendance profile with full history."""
    history = get_student_history(student_name)
    total = len(history)
    present = sum(1 for r in history if r["status"] == "Present")

    return {
        "student_name": student_name,
        "total_classes": total,
        "classes_present": present,
        "attendance_rate": round(present / total * 100, 1) if total > 0 else 0,
        "history": history,
    }


@app.get("/student/{student_name}/download")
def student_download_report(student_name: str):
    """Download a personal attendance Excel report for a specific student."""
    excel_file = export_student_report(student_name)
    return FileResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"attendance_{student_name}.xlsx",
    )


# =============================================
# FEATURE-SPECIFIC ENDPOINTS
# =============================================

@app.get("/db")
def check_db():
    from face_engine import load_encodings
    return {"students": list(load_encodings().keys())}

# Policy Engine (Feature 6)
@app.get("/policy")
def get_policy():
    return {"policy": policy.get_all()}

@app.post("/policy", dependencies=[Depends(get_api_key)])
def update_policy(update: PolicyUpdate):
    policy.set_value(update.key, update.value)
    policy.reload()
    return {"status": "updated", "key": update.key, "value": update.value}

# Configuration
@app.get("/config")
def get_config():
    return load_config()

# Blockchain Audit (Feature 8)
@app.get("/audit")
def get_audit_log():
    events = audit_chain.get_recent_events(limit=50)
    is_valid, error, count = audit_chain.verify_chain()
    return {
        "events": events,
        "chain_valid": is_valid,
        "chain_error": error,
        "total_blocks": count,
    }

@app.get("/audit/verify")
def verify_audit():
    is_valid, error, count = audit_chain.verify_chain()
    return {"chain_valid": is_valid, "error": error, "total_blocks": count}

# ZK Proofs (Feature 4)
@app.get("/zk/status")
def zk_status():
    return {"proof_count": zk_prover.get_proof_count(), "protocol": "pedersen_commitment_v1"}

# Environmental Sensors (Feature 9)
@app.get("/environment")
def get_environment():
    is_valid, readings, violations = env_sensors.check_environment()
    return {"valid": is_valid, "readings": readings, "violations": violations}

# Model Attestation (Feature 3)
@app.get("/attestation")
def get_attestation():
    models = {}
    if os.path.exists("exports/yolov8n.onnx"):
        models["yolov8n_onnx"] = "exports/yolov8n.onnx"
    elif os.path.exists("yolov8n.pt"):
        models["yolov8n"] = "yolov8n.pt"
        
    if os.path.exists(ENCODING_FILE):
        models["face_encodings"] = ENCODING_FILE
    return verify_all_models(models)

# Federated Learning (Feature 7)
@app.get("/federated/status")
def federated_status():
    return {"client_samples": fed_client.get_sample_count(), "server_status": fed_server.get_status()}

@app.post("/federated/aggregate", dependencies=[Depends(get_api_key)])
def federated_aggregate():
    result, message = fed_server.aggregate()
    return {"message": message, "success": result is not None}

# Edge Inference (Feature 5)
@app.get("/edge/report")
def edge_report():
    from scripts.export_onnx import generate_edge_report
    return {"models": generate_edge_report()}

# Session Recovery (Feature 10)
@app.get("/sessions")
def get_sessions():
    return {"sessions": get_all_stats()}


# --- Main ---

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)