"""
CSTPE Edge Inference Export (Feature 5)
Script to export YOLOv8 and face-recognition models to ONNX format
with optional INT8 quantization for deployment on edge hardware
(e.g., Jetson Nano, Raspberry Pi + Coral TPU).
"""

import os
import sys


def export_yolo_to_onnx(model_path="yolov8n.pt", output_dir="exports"):
    """
    Export the YOLOv8 model to ONNX format.
    """
    os.makedirs(output_dir, exist_ok=True)

    try:
        import torch
        # Patch torch.load for compatibility
        _original = torch.load
        def _patched(*a, **kw):
            kw['weights_only'] = False
            return _original(*a, **kw)
        torch.load = _patched

        from ultralytics import YOLO

        model = YOLO(model_path)
        onnx_path = model.export(format="onnx", imgsz=640, simplify=True)
        print(f"YOLO model exported to ONNX: {onnx_path}")
        return onnx_path

    except Exception as e:
        print(f"ONNX export failed: {e}")
        return None


def quantize_onnx_model(onnx_path, output_path=None):
    """
    Apply INT8 dynamic quantization to an ONNX model.
    """
    try:
        from onnxruntime.quantization import quantize_dynamic, QuantType

        if output_path is None:
            base, ext = os.path.splitext(onnx_path)
            output_path = f"{base}_int8{ext}"

        quantize_dynamic(
            model_input=onnx_path,
            model_output=output_path,
            weight_type=QuantType.QInt8,
        )
        print(f"Quantized model saved to: {output_path}")
        return output_path

    except ImportError:
        print("onnxruntime not installed. Install with: pip install onnxruntime")
        return None
    except Exception as e:
        print(f"Quantization failed: {e}")
        return None


def get_model_size_mb(filepath):
    """Report model file size in MB."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath) / (1024 * 1024)
        return round(size, 2)
    return 0


def generate_edge_report():
    """
    Generate a summary of available model formats and their sizes.
    """
    models = {
        "yolov8n.pt": "yolov8n.pt",
        "yolov8n.onnx": "exports/yolov8n.onnx",
        "yolov8n_int8.onnx": "exports/yolov8n_int8.onnx",
    }

    report = []
    for name, path in models.items():
        size = get_model_size_mb(path)
        status = "Available" if os.path.exists(path) else "Not exported"
        report.append({"model": name, "size_mb": size, "status": status})

    return report


if __name__ == "__main__":
    print("CSTPE Edge Inference Export Tool")
    print("=" * 40)

    # Export YOLO to ONNX
    onnx_path = export_yolo_to_onnx()

    if onnx_path:
        # Quantize to INT8
        quantize_onnx_model(onnx_path)

    # Report
    print("\nModel Report:")
    for item in generate_edge_report():
        print(f"  {item['model']}: {item['size_mb']} MB ({item['status']})")
