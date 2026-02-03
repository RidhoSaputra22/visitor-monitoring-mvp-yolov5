"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function CameraConfig() {
  const [err, setErr] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [camera, setCamera] = useState(null);

  const [rtsp, setRtsp] = useState("");
  const [roiText, setRoiText] = useState(`[[100,100],[500,100],[500,400],[100,400]]`);

  async function load() {
    setErr(""); setOkMsg("");
    const token = localStorage.getItem("token");
    if (!token) { setErr("No token. Please login."); return; }
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const res = await fetch(`${API_BASE}/api/cameras/1`, { headers });
      if (!res.ok) throw new Error("Failed to load camera (id=1).");
      const data = await res.json();
      setCamera(data);
      setRtsp(data.rtsp_url || "");
      if (data.roi) setRoiText(JSON.stringify(data.roi));
    } catch (e) {
      setErr(e.message || "Error");
    }
  }

  useEffect(() => { load(); }, []);

  async function save() {
    setErr(""); setOkMsg("");
    const token = localStorage.getItem("token");
    if (!token) { setErr("No token. Please login."); return; }
    const headers = {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    };

    let roi = null;
    try {
      roi = roiText.trim() ? JSON.parse(roiText) : null;
    } catch {
      setErr("ROI JSON invalid. Example: [[100,100],[500,100],[500,400],[100,400]]");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/cameras/1`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ rtsp_url: rtsp || null, roi })
      });
      if (!res.ok) throw new Error("Save failed (need admin role).");
      setOkMsg("Saved. Edge will refresh config automatically.");
      await load();
    } catch (e) {
      setErr(e.message || "Error");
    }
  }

  return (
    <main style={{ padding: 24, maxWidth: 760 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1>Konfigurasi Kamera (ID=1)</h1>
        <Link href="/dashboard">Back</Link>
      </div>

      {err ? <p style={{ color: "crimson" }}>{err}</p> : null}
      {okMsg ? <p style={{ color: "green" }}>{okMsg}</p> : null}

      <section style={{ display: "grid", gap: 12 }}>
        <label>
          RTSP URL
          <input value={rtsp} onChange={(e) => setRtsp(e.target.value)} style={{ width: "100%", padding: 10, marginTop: 6 }} />
        </label>

        <label>
          Area Hitung (ROI Polygon) - JSON array of points [x,y]
          <textarea value={roiText} onChange={(e) => setRoiText(e.target.value)} rows={6}
            style={{ width: "100%", padding: 10, marginTop: 6, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" }} />
        </label>

        <button onClick={save} style={{ padding: 12, cursor: "pointer" }}>Save</button>

        <p style={{ opacity: 0.8 }}>
          ROI menggunakan koordinat pixel gambar dari kamera. Untuk akurat, ambil screenshot frame lalu tentukan titik poligon.
        </p>

        {camera ? (
          <pre style={{ padding: 12, background: "#f6f6f6", borderRadius: 10, overflowX: "auto" }}>
            {JSON.stringify(camera, null, 2)}
          </pre>
        ) : null}
      </section>
    </main>
  );
}
