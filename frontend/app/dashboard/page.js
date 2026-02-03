"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function todayISO() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function Dashboard() {
  const [me, setMe] = useState(null);
  const [daily, setDaily] = useState([]);
  const [err, setErr] = useState("");
  const day = useMemo(() => todayISO(), []);

  async function load() {
    setErr("");
    const token = localStorage.getItem("token");
    if (!token) {
      setErr("No token. Please login.");
      return;
    }
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const meRes = await fetch(`${API_BASE}/api/me`, { headers });
      if (!meRes.ok) throw new Error("Auth failed");
      setMe(await meRes.json());

      const dailyRes = await fetch(`${API_BASE}/api/stats/daily?day=${day}`, { headers });
      if (!dailyRes.ok) throw new Error("Failed to load stats");
      setDaily(await dailyRes.json());
    } catch (e) {
      setErr(e.message || "Error");
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [day]);

  const totalIn = daily.reduce((s, r) => s + r.total_in, 0);
  const totalOut = daily.reduce((s, r) => s + r.total_out, 0);
  const unique = daily.reduce((s, r) => s + r.unique_estimate, 0);

  return (
    <main style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1>Dashboard</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "baseline" }}>
          <Link href="/camera">Konfigurasi Kamera</Link>
          <Link href="/login" onClick={() => localStorage.removeItem("token")}>Logout</Link>
        </div>
      </div>

      {me ? <p style={{ opacity: 0.75 }}>Logged in as: <b>{me.username}</b> ({me.role})</p> : null}
      {err ? <p style={{ color: "crimson" }}>{err}</p> : null}

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginTop: 16 }}>
        <Card title="Tanggal (Hari ini)" value={day} />
        <Card title="Total Masuk" value={String(totalIn)} />
        <Card title="Total Keluar" value={String(totalOut)} />
        <Card title="Unik (Estimasi)" value={String(unique)} />
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Camera Preview</h2>
        <CameraView />
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Ringkasan</h2>
        <p>Data diperbarui otomatis setiap 5 detik.</p>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={th}>Camera ID</th>
              <th style={th}>Total In</th>
              <th style={th}>Total Out</th>
              <th style={th}>Unique</th>
            </tr>
          </thead>
          <tbody>
            {daily.map((r) => (
              <tr key={`${r.camera_id}-${r.day}`}>
                <td style={td}>{r.camera_id}</td>
                <td style={td}>{r.total_in}</td>
                <td style={td}>{r.total_out}</td>
                <td style={td}>{r.unique_estimate}</td>
              </tr>
            ))}
            {daily.length === 0 ? (
              <tr>
                <td style={td} colSpan={4}>No data yet. Run edge in FAKE mode or REAL mode.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Export Laporan (CSV)</h2>
        <code style={{ display: "block", padding: 12, background: "#f6f6f6", borderRadius: 10 }}>
          GET {API_BASE}/api/reports/csv?from_day={day}&to_day={day}
        </code>
      </section>
    </main>
  );
}

function Card({ title, value }) {
  return (
    <div style={{ border: "1px solid #e5e5e5", borderRadius: 14, padding: 14 }}>
      <div style={{ opacity: 0.7, fontSize: 13 }}>{title}</div>
      <div style={{ fontSize: 26, fontWeight: 700, marginTop: 6 }}>{value}</div>
    </div>
  );
}

const th = { textAlign: "left", borderBottom: "1px solid #ddd", padding: 10, opacity: 0.8 };
const td = { borderBottom: "1px solid #eee", padding: 10 };

function CameraView() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [streamUrl] = useState("http://localhost:5000/video_feed");
  const imgRef = useRef(null);

  useEffect(() => {
    // Check if stream is accessible
    const checkStream = async () => {
      try {
        const response = await fetch("http://localhost:5000/health");
        if (response.ok) {
          setLoading(false);
          setError("");
        } else {
          throw new Error("Stream server not responding");
        }
      } catch (err) {
        setError("Camera stream not available. Make sure edge container is running.");
        setLoading(false);
      }
    };

    checkStream();
    const interval = setInterval(checkStream, 10000); // Check every 10 seconds
    
    return () => clearInterval(interval);
  }, []);

  const handleImageError = () => {
    setError("Failed to load camera stream. The camera might be busy or disconnected.");
    setLoading(false);
  };

  const handleImageLoad = () => {
    setLoading(false);
    setError("");
  };

  const retryStream = () => {
    setError("");
    setLoading(true);
    if (imgRef.current) {
      imgRef.current.src = streamUrl + "?t=" + Date.now(); // Force reload with timestamp
    }
  };

  return (
    <div style={{ border: "1px solid #e5e5e5", borderRadius: 14, padding: 14 }}>
      <h3 style={{ margin: "0 0 12px 0" }}>Live Camera Feed</h3>
      
      {loading && !error && (
        <div style={{ 
          padding: "40px", 
          textAlign: "center", 
          backgroundColor: "#f8f9fa",
          borderRadius: "8px",
          margin: "12px 0"
        }}>
          <p>🔍 Loading camera stream...</p>
          <p style={{ fontSize: "12px", opacity: 0.7 }}>
            Connecting to edge server...
          </p>
        </div>
      )}
      
      {error && (
        <div style={{ 
          padding: "16px", 
          backgroundColor: "#fff3cd", 
          border: "1px solid #ffeaa7",
          borderRadius: "8px",
          margin: "12px 0"
        }}>
          <p style={{ color: "#856404", margin: "0 0 12px 0", fontWeight: "500" }}>
            📹 Camera Stream Issue
          </p>
          <p style={{ 
            color: "#856404", 
            fontSize: "12px", 
            margin: "0 0 12px 0"
          }}>
            {error}
          </p>
          <button 
            onClick={retryStream}
            style={{
              padding: "8px 16px",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "12px"
            }}
          >
            🔄 Retry Stream
          </button>
        </div>
      )}
      
      <img
        ref={imgRef}
        src={streamUrl}
        alt="Camera Feed"
        onError={handleImageError}
        onLoad={handleImageLoad}
        style={{
          width: "100%",
          maxWidth: "640px",
          height: "auto",
          backgroundColor: "#000",
          borderRadius: "8px",
          display: loading || error ? "none" : "block"
        }}
      />
      
      {!loading && !error && (
        <p style={{ fontSize: "12px", opacity: 0.7, margin: "8px 0 0 0" }}>
          ✅ Live stream from edge server. This is the same camera feed that YOLO detection uses.
        </p>
      )}
    </div>
  );
}
