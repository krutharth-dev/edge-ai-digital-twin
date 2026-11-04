import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowUpRight, BarChart3, Bell, CheckCircle2,
  CircleHelp, Cpu, Gauge, LayoutDashboard, Radio, RefreshCw, Thermometer,
  Waves, Zap,
} from "lucide-react";

type Health = "HEALTHY" | "WARNING" | "FAULT" | "UNKNOWN";
type Sensor = "temperature" | "current" | "rpm" | "vibration";
type Snapshot = {
  asset_id: string; health_state: Health; is_fresh: boolean;
  health_score: number | null; metrics: Partial<Record<"temperature_c" | "current_a" | "rpm" | "vibration_rms_g", number>>;
  source: string | null; message: string; last_updated_ms: number | null;
  predicted_state?: string | null; confidence?: number | null;
  model_version?: string | null; model_data_type?: string | null;
};
type Reading = { time_ms: number; sensor: Sensor; value: number; source: string };
type Alert = { timestamp_ms: number; previous_state: string; new_state: string; message: string; source: string | null };
type Dashboard = { server_time_ms: number; asset_id: string; snapshot: Snapshot; history: Reading[]; alerts: Alert[] };
type View = "overview" | "telemetry" | "alerts";

const EMPTY: Dashboard = {
  server_time_ms: 0, asset_id: "MOTOR_01",
  snapshot: { asset_id: "MOTOR_01", health_state: "UNKNOWN", is_fresh: false,
    health_score: null, metrics: {}, source: "UNKNOWN", message: "Waiting for telemetry", last_updated_ms: null },
  history: [], alerts: [],
};
const METRICS = [
  { sensor: "temperature" as const, key: "temperature_c" as const, title: "Temperature", unit: "°C", icon: Thermometer, color: "#fbad69", max: 90 },
  { sensor: "current" as const, key: "current_a" as const, title: "Motor current", unit: "A", icon: Zap, color: "#c39fff", max: 2.5 },
  { sensor: "rpm" as const, key: "rpm" as const, title: "Rotational speed", unit: "RPM", icon: Gauge, color: "#6ebdff", max: 2500 },
  { sensor: "vibration" as const, key: "vibration_rms_g" as const, title: "Vibration RMS", unit: "g", icon: Waves, color: "#5be0c6", max: .65 },
];
const STATE_COLOR: Record<Health, string> = {
  HEALTHY: "#58e5b7", WARNING: "#ffc17f", FAULT: "#ff7d90", UNKNOWN: "#95a3bb",
};

function Sparkline({ values, color, height = 58 }: { values: number[]; color: string; height?: number }) {
  if (!values.length) return <div className="no-chart">Awaiting sensor readings</div>;
  const width = 320;
  const low = Math.min(...values), high = Math.max(...values);
  const range = high - low || 1;
  const points = values.map((v, i) => {
    const x = 6 + (i / Math.max(1, values.length - 1)) * (width - 12);
    const y = height - 7 - ((v - low) / range) * (height - 16);
    return x.toFixed(1) + "," + y.toFixed(1);
  }).join(" ");
  return <svg viewBox={"0 0 " + width + " " + height} preserveAspectRatio="none" className="sparkline" aria-label="Recent measurement trend" role="img">
    <line x1="0" y1={height - 2} x2={width} y2={height - 2} stroke="#29364b" strokeWidth="1" />
    <polyline fill="none" stroke={color} strokeWidth="2.8" strokeLinejoin="round" strokeLinecap="round" points={points} vectorEffect="non-scaling-stroke" />
  </svg>;
}
function formatValue(value: number | undefined, sensor: Sensor) {
  if (value === undefined || value === null) return "—";
  return sensor === "rpm" ? value.toFixed(0) : sensor === "current" || sensor === "vibration" ? value.toFixed(3) : value.toFixed(1);
}
function timeLabel(ms: number | null) {
  if (!ms) return "No telemetry yet";
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
function useDashboard() {
  const [data, setData] = useState<Dashboard>(EMPTY);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/dashboard", { cache: "no-store" });
      if (!response.ok) throw new Error("Dashboard API returned " + response.status);
      const json: Dashboard = await response.json();
      setData(json);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "API unavailable");
    }
  }, []);
  useEffect(() => {
    let socket: WebSocket | undefined;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;
    const connect = () => {
      const scheme = location.protocol === "https:" ? "wss:" : "ws:";
      socket = new WebSocket(scheme + "//" + location.host + "/ws");
      socket.onopen = () => { if (!stopped) { setConnected(true); setError(null); } };
      socket.onmessage = (event: MessageEvent<string>) => {
        try { setData(JSON.parse(event.data) as Dashboard); setError(null); } catch { /* ignore malformed frames */ }
      };
      socket.onerror = () => { if (!stopped) setConnected(false); };
      socket.onclose = () => {
        if (stopped) return;
        setConnected(false);
        retry = setTimeout(connect, 3000);
      };
    };
    void refresh();
    connect();
    const fallback = setInterval(() => { if (!socket || socket.readyState !== WebSocket.OPEN) void refresh(); }, 5000);
    return () => {
      stopped = true;
      clearInterval(fallback);
      if (retry) clearTimeout(retry);
      socket?.close();
    };
  }, [refresh]);
  // Backend time is authoritative for freshness; force UI stale if stream stops.
  const [clock, setClock] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const last = data.snapshot.last_updated_ms;
  const fresh = data.snapshot.is_fresh && typeof last === "number" && clock - last <= 12_000 && clock >= last;
  const snapshot = fresh ? data.snapshot : { ...data.snapshot, health_state: "UNKNOWN" as Health, metrics: {}, health_score: null, predicted_state: null, confidence: null };
  return { data, snapshot, connected, error, refresh };
}
export default function App() {
  const { data, snapshot, connected, error, refresh } = useDashboard();
  const [view, setView] = useState<View>("overview");
  const recent = useMemo(() => Object.fromEntries(METRICS.map(m => [
    m.sensor, data.history.filter(item => item.sensor === m.sensor).slice(-65),
  ])) as Record<Sensor, Reading[]>, [data.history]);
  const state = snapshot.health_state;
  const statusColor = STATE_COLOR[state];
  return <div className="app">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><Activity size={24} /></div><div><strong>AXIOM</strong><span>EDGE INTELLIGENCE</span></div></div>
      <p className="sidebar-label">WORKSPACE</p>
      <nav aria-label="Dashboard views">
        <button className={"nav-item " + (view === "overview" ? "active" : "")} onClick={() => setView("overview")}><LayoutDashboard size={18} /> Overview</button>
        <button className={"nav-item " + (view === "telemetry" ? "active" : "")} onClick={() => setView("telemetry")}><BarChart3 size={18} /> Telemetry</button>
        <button className={"nav-item " + (view === "alerts" ? "active" : "")} onClick={() => setView("alerts")}><Bell size={18} /> Alerts <span className="nav-count">{data.alerts.length}</span></button>
      </nav>
      <div className="sidebar-bottom"><div className="asset-mini"><span className="asset-dot" /> MOTOR_01 <span>ACTIVE ASSET</span></div><p>Local simulation environment<br/>Academic prototype · v0.1</p></div>
    </aside>
    <main className="main">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> Motor monitoring <span>/</span> <b>{view === "overview" ? "Overview" : view === "telemetry" ? "Telemetry" : "Alerts"}</b></div>
        <div className="top-actions"><span className={"connection " + (connected ? "connected" : "")}><Radio size={15} /> {connected ? "Live connection" : "Reconnecting"}</span><button className="icon-button" onClick={() => void refresh()} title="Refresh dashboard" aria-label="Refresh dashboard"><RefreshCw size={17} /></button></div>
      </header>
      <div className="page">
        <div className="heading"><div><p className="eyebrow">MACHINE INTELLIGENCE / LIVE OVERVIEW</p><h1>{view === "overview" ? "Digital Twin Command Center" : view === "telemetry" ? "Sensor Telemetry" : "Maintenance Alerts"}</h1><p className="subheading">Motor 01 <span>·</span> Condition monitoring and predictive-maintenance research</p></div><div className="live-pill"><span className="pulse-dot"/> LOCAL ENVIRONMENT</div></div>
        <div className="notice"><CircleHelp size={18}/><span><strong>SIMULATION / ACADEMIC USE.</strong> Thresholds and model predictions are illustrative, not validated equipment protection or real-world fault accuracy.</span></div>
        {error && <div className="api-error"><AlertTriangle size={17}/>{error}. Start the FastAPI service on port 8000.</div>}
        {view === "overview" && <>
          <div className="hero-grid">
            <section className="panel machine-panel">
              <div className="panel-title"><span><Cpu size={17}/> DIGITAL TWIN / MOTOR_01</span><span className="panel-tag">LIVE MODEL</span></div>
              <div className="machine-stage">
                <div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit orbit-three"/>
                <div className="machine-body"><div className="fan-visual"><div className="fan-blade b1"/><div className="fan-blade b2"/><div className="fan-blade b3"/><div className="fan-blade b4"/><div className="fan-center"/></div></div>
                <div className="stage-label top-left">ASSET 01 <span>DC MOTOR / FAN</span></div>
                <div className="stage-label bottom-right">EDGE HOST <span>MAC · LOCAL</span></div>
              </div>
              <div className="machine-footer"><div><span className="label">OPERATIONAL STATE</span><div className="state-row"><span className="state-dot" style={{background:statusColor}}/><strong style={{color:statusColor}}>{state}</strong></div></div><div className="state-message">{state === "UNKNOWN" && !snapshot.is_fresh ? "Waiting for fresh readings" : snapshot.message}</div></div>
            </section>
            <section className="panel status-panel">
              <div className="panel-title"><span><Activity size={17}/> SYSTEM HEALTH</span><span className="panel-tag">CURRENT</span></div>
              <div className="health-content"><div className="score-ring" style={{"--ring-color": statusColor, "--ring-angle": ((snapshot.health_score ?? 0) * 3.6) + "deg"} as React.CSSProperties}><div><strong>{snapshot.health_score === null ? "—" : snapshot.health_score}</strong><small>HEALTH SCORE</small></div></div>
              <h2 style={{color:statusColor}}>{state === "UNKNOWN" ? "Telemetry unavailable" : state === "HEALTHY" ? "Operating normally" : state === "WARNING" ? "Attention required" : "Fault detected"}</h2><p>{snapshot.message}</p></div>
              <div className="status-stats"><div><span>DATA SOURCE</span><strong>{snapshot.source || "UNKNOWN"}</strong></div><div><span>LAST SEEN</span><strong>{timeLabel(snapshot.last_updated_ms)}</strong></div></div>
            </section>
          </div>
          <div className="section-header"><h2>Live Sensor Readings</h2><span>Four monitored parameters <ArrowUpRight size={15}/></span></div>
          <div className="metrics-grid">{METRICS.map(m => {const Icon=m.icon;const readings=recent[m.sensor];return <article className="panel metric-card" key={m.sensor}><div className="metric-top"><div className="metric-icon" style={{color:m.color,background:m.color+"18"}}><Icon size={20}/></div><span className="metric-tag">SENSOR / {m.sensor.toUpperCase()}</span></div><div className="metric-name">{m.title}</div><div className="metric-value">{formatValue(snapshot.metrics[m.key],m.sensor)} <span>{m.unit}</span></div><Sparkline values={readings.map(r=>r.value)} color={m.color}/><div className="metric-bottom"><span>{readings.length} recent samples</span><span>HISTORY <ArrowUpRight size={13}/></span></div></article>;})}</div>
          <div className="bottom-grid"><section className="panel detail-panel"><div className="panel-title"><span><Cpu size={17}/> AI INFERENCE</span><span className="panel-tag">OPTIONAL MODEL</span></div><div className="ai-inference">{snapshot.predicted_state ? <><div className="ai-value">{snapshot.predicted_state}</div><p>Classifier probability: {snapshot.confidence == null ? "Not available" : (snapshot.confidence*100).toFixed(1)+"%"} · Not calibrated</p><small>{snapshot.model_version ?? "Unversioned"} · {snapshot.model_data_type ?? "Unverified data"}</small></> : <><div className="ai-placeholder"><Cpu size={30}/></div><h3>Rule-based monitoring active</h3><p>No optional ML inference loaded. Run the trusted local demo model to see predictions.</p></>}</div></section><section className="panel detail-panel"><div className="panel-title"><span><Bell size={17}/> RECENT EVENTS</span><button className="text-action" onClick={()=>setView("alerts")}>View all <ArrowUpRight size={14}/></button></div><div className="events-list">{data.alerts.length===0?<p className="empty-state">No state-transition alerts recorded yet.</p>:data.alerts.slice(0,3).map((a,i)=><div className="event-row" key={String(a.timestamp_ms)+i}><span className="event-icon"><AlertTriangle size={17}/></span><div><strong>{a.previous_state} → {a.new_state}</strong><p>{a.message}</p></div><time>{timeLabel(a.timestamp_ms)}</time></div>)}</div></section></div>
        </>}
        {view === "telemetry" && <div className="telemetry-grid">{METRICS.map(m=>{const Icon=m.icon;const readings=recent[m.sensor];return <article className="panel telemetry-panel" key={m.sensor}><div className="panel-title"><span><Icon size={17}/>{m.title}</span><span className="panel-tag">{m.unit}</span></div><div className="telemetry-number">{formatValue(snapshot.metrics[m.key],m.sensor)} <span>{m.unit}</span></div><Sparkline height={175} values={readings.map(r=>r.value)} color={m.color}/><p>Historical readings · {readings.length} recent samples · {readings[readings.length-1]?.source ?? "—"}</p></article>;})}</div>}
        {view === "alerts" && <section className="panel alerts-panel"><div className="panel-title"><span><Bell size={17}/> STATE TRANSITION HISTORY</span><span className="panel-tag">{data.alerts.length} EVENTS</span></div>{data.alerts.length ? <div className="alerts-table"><div className="alerts-header"><span>TRANSITION</span><span>DETAIL</span><span>SOURCE</span><span>TIME</span></div>{data.alerts.map((a,i)=><div className="alerts-line" key={String(a.timestamp_ms)+i}><span><AlertTriangle size={16}/> {a.previous_state} → {a.new_state}</span><span>{a.message}</span><span>{a.source || "UNKNOWN"}</span><time>{new Date(a.timestamp_ms).toLocaleString()}</time></div>)}</div>:<div className="empty-large"><CheckCircle2 size={34}/><h3>No transitions recorded</h3><p>Start the simulated MQTT scenarios to generate alert history.</p></div>}</section>}
        <footer className="footer">EDGE AI DIGITAL TWIN <span>·</span> MOTOR_01 <span>·</span> LOCAL READ-ONLY DASHBOARD <span>·</span> SYNTHETIC DATA NOT VALIDATED</footer>
      </div>
    </main>
  </div>;
}
