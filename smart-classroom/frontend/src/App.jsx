import { useEffect, useRef, useState } from "react";
import axios from "axios";

function App() {
  const API_URL = "http://localhost:8000";
  const WS_URL = "ws://localhost:8000/ws/dashboard";

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [dashboardStats, setDashboardStats] = useState([]);
  const [resultImage, setResultImage] = useState("");
  const [isTracking, setIsTracking] = useState(false);
  
  const ws = useRef(null);
  const trackInterval = useRef(null);

  useEffect(() => {
    startCamera();
    connectWebSocket();

    return () => {
      if (ws.current) ws.current.close();
      if (trackInterval.current) clearInterval(trackInterval.current);
    };
  }, []);

  const connectWebSocket = () => {
    ws.current = new WebSocket(WS_URL);
    
    ws.current.onopen = () => console.log("Connected to Teacher Dashboard WS");
    
    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "init" || message.type === "update") {
          setDashboardStats(message.data);
        }
      } catch (e) {
        console.error("WS error", e);
      }
    };
    
    ws.current.onclose = () => {
      console.log("WS closed. Reconnecting...");
      setTimeout(connectWebSocket, 3000);
    };
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = stream;
    } catch (err) {
      alert("Camera access denied");
      console.log(err);
    }
  };

  const captureFrameAndSend = async () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return;

    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const image = canvas.toDataURL("image/jpeg", 0.7);

    try {
      await axios.post(`${API_URL}/attendance`, { image: image });
      setResultImage(`${API_URL}/static/result.jpg?t=` + new Date().getTime());
    } catch (err) {
      console.log("Error processing frame", err);
    }
  };

  const toggleTracking = () => {
    if (isTracking) {
      clearInterval(trackInterval.current);
      setIsTracking(false);
    } else {
      trackInterval.current = setInterval(captureFrameAndSend, 3000); // 3 seconds interval
      setIsTracking(true);
    }
  };

  return (
    <div style={{ fontFamily: "Inter, Arial", background: "#0f172a", minHeight: "100vh", color: "white", padding: "30px" }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto", textAlign: "center" }}>
        
        <h1 style={{ color: "#38bdf8", marginBottom: "5px" }}>Continuous Spatial-Temporal Presence Engine</h1>
        <p style={{ color: "#94a3b8", marginBottom: "30px" }}>Patent-Pending YOLOv8 + Liveness Detection</p>

        <div style={{ display: "flex", gap: "30px", justifyContent: "center", flexWrap: "wrap" }}>
          
          {/* Camera Feed Section */}
          <div style={{ background: "#1e293b", padding: "20px", borderRadius: "15px", flex: "1", minWidth: "400px" }}>
            <h3>Classroom Camera Feed</h3>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{ width: "100%", borderRadius: "10px", border: "2px solid #334155", marginBottom: "15px" }}
            />
            
            <button
              onClick={toggleTracking}
              style={{
                padding: "12px 24px", fontSize: "16px", border: "none", borderRadius: "8px",
                background: isTracking ? "#ef4444" : "#10b981", color: "white", cursor: "pointer", fontWeight: "bold"
              }}
            >
              {isTracking ? "Stop Continuous Tracking" : "Start Continuous Tracking (3s Interval)"}
            </button>

            {resultImage && (
              <div style={{ marginTop: "20px" }}>
                <h4>YOLO Vision Output</h4>
                <img src={resultImage} alt="vision result" style={{ width: "100%", borderRadius: "10px", border: "2px solid #334155" }} />
              </div>
            )}
          </div>

          {/* Teacher Dashboard Section */}
          <div style={{ background: "#1e293b", padding: "20px", borderRadius: "15px", flex: "1", minWidth: "400px" }}>
            <h3>Live Teacher Dashboard</h3>
            <p style={{ color: "#94a3b8", fontSize: "14px" }}>Accumulated Active Presence (AAP) required: 40 mins (2400s)</p>
            
            <div style={{ overflowX: "auto", marginTop: "20px" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", background: "#0f172a", borderRadius: "8px", overflow: "hidden" }}>
                <thead>
                  <tr style={{ background: "#38bdf8", color: "#0f172a" }}>
                    <th style={{ padding: "12px", textAlign: "left" }}>Student</th>
                    <th style={{ padding: "12px", textAlign: "center" }}>Active Time</th>
                    <th style={{ padding: "12px", textAlign: "center" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardStats.length > 0 ? (
                    dashboardStats.map((stat, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #334155" }}>
                        <td style={{ padding: "12px", textAlign: "left" }}>{stat.student || stat.student_name}</td>
                        <td style={{ padding: "12px", textAlign: "center" }}>
                          {Math.floor(stat.accumulated_seconds / 60)}m {stat.accumulated_seconds % 60}s
                        </td>
                        <td style={{ padding: "12px", textAlign: "center" }}>
                          <span style={{
                            padding: "4px 8px", borderRadius: "12px", fontSize: "12px", fontWeight: "bold",
                            background: stat.status === "Present" ? "#10b981" : "#f59e0b",
                            color: stat.status === "Present" ? "white" : "#0f172a"
                          }}>
                            {stat.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="3" style={{ padding: "20px", color: "#94a3b8", textAlign: "center" }}>No students tracked yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <br />
            <a href={`${API_URL}/download`} target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
              <button style={{
                padding: "10px 20px", fontSize: "14px", border: "1px solid #38bdf8", borderRadius: "8px",
                background: "transparent", color: "#38bdf8", cursor: "pointer", fontWeight: "bold", marginTop: "20px"
              }}>
                📥 Export Official Excel Report
              </button>
            </a>
          </div>

        </div>

        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>
    </div>
  );
}

export default App;