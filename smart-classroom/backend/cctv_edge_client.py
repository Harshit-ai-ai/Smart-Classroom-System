import cv2
import time
import base64
import requests
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="CSTPE Edge Gateway - CCTV RTSP Ingestion")
    parser.add_argument("--rtsp", type=str, required=True, help="RTSP URL of the CCTV camera (e.g., rtsp://192.168.1.100:554/stream)")
    parser.add_argument("--api", type=str, required=True, help="URL of the Render API backend (e.g., https://smart-classroom-system-3.onrender.com)")
    parser.add_argument("--key", type=str, default="cstpe-mahe-2026-secure", help="API Key for the backend (default: cstpe-mahe-2026-secure)")
    parser.add_argument("--interval", type=int, default=3, help="Interval between frames in seconds (default: 3)")
    
    args = parser.parse_args()

    print(f"[*] Initializing Edge Gateway...")
    print(f"[-] Target CCTV Stream: {args.rtsp}")
    print(f"[-] Target Cloud API:   {args.api}")
    print(f"[-] Polling Interval:   {args.interval} seconds")
    
    cap = cv2.VideoCapture(args.rtsp)
    
    if not cap.isOpened():
        print("[!] ERROR: Cannot open CCTV stream. Check the RTSP URL and network connection.")
        sys.exit(1)
        
    print("[+] Successfully connected to CCTV stream. Starting ingestion pipeline...")

    try:
        while True:
            # Clear buffer to ensure we get the latest frame
            # (RTSP feeds can buffer causing massive delays if not grabbed continuously)
            cap.grab()
            
            ret, frame = cap.retrieve()
            if not ret:
                print("[!] Failed to retrieve frame from CCTV. Reconnecting...")
                cap.release()
                time.sleep(2)
                cap = cv2.VideoCapture(args.rtsp)
                continue

            # Encode as highly compressed JPEG to save bandwidth
            # Quality=80 is an excellent balance between preserving facial details and minimizing payload size
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            # Convert to base64 exactly as the frontend does
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            payload = f"data:image/jpeg;base64,{jpg_as_text}"

            print(f"[*] Sending frame to Cloud Engine... ({len(payload) // 1024} KB)")

            try:
                # HTTP POST to the backend with Security Key
                headers = {"X-API-Key": args.key}
                res = requests.post(f"{args.api}/attendance", json={"image": payload}, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    print(f"  [+] Success: Detected {data.get('count', 0)} students.")
                else:
                    print(f"  [-] API Error: HTTP {res.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"  [!] Network Exception: {e}")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[*] Gracefully shutting down Edge Gateway...")
    finally:
        cap.release()

if __name__ == "__main__":
    main()
