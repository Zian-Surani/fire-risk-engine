/**
 * Typed API client for the Fire Risk FastAPI backend.
 * All fetch calls go through this module so we have one place to set
 * the base URL and handle errors.
 */

const BASE = (process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    options?: ErrorOptions
  ) {
    super(message, options);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      cache: "no-store",
      ...init,
    });
  } catch (error) {
    throw new ApiError(
      0,
      `Could not reach the backend at ${BASE}. Start the FastAPI server and try again.`,
      { cause: error }
    );
  }
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

// ---------------------------------------------------------------------------
// Envelope type shared by all dashboard endpoints
// ---------------------------------------------------------------------------

export interface RuntimeSnapshot {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
}

export interface Envelope<T = unknown> {
  generated_at: string;
  stale_after: number;
  query_latency_ms: number;
  ai_latency_ms: number;
  source_status: "live" | "mock" | "error" | "static" | "initializing";
  data: T;
  alerts: string[];
  /** Process + host metrics from the backend refresh loop */
  runtime?: RuntimeSnapshot;
  /** Latest POST /api/optimize payload (full envelope-shaped snapshot extras) */
  last_optimization?: Record<string, unknown> | null;
  /** Latest POST /api/simulations/run snapshot artifact */
  last_simulation?: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// Per-page data shapes (minimal subset consumed by the UI)
// ---------------------------------------------------------------------------

export interface Marker {
  address: string;
  district: string;
  adjusted_risk_score: number;
  adjusted_risk_band: "HIGH" | "MEDIUM" | "LOW";
  adjusted_percentile: number;
  marker_color: string;
  latitude: number;
  longitude: number;
  display_district: string;
  explanation_text: string;
  risk_drivers: { label: string; impact_pct: number }[];
  visual_severity_level: number;
}

export interface DistrictCard {
  district: string;
  display_district: string;
  adjusted_risk_score: number;
  adjusted_risk_band: string;
  marker_color: string;
  latitude: number | null;
  longitude: number | null;
}

export interface Recommendation {
  action_type?: string;
  priority?: string;
  description: string;
  estimated_impact?: string;
  district?: string;
}

export interface ExecMetric {
  metric_name: string;
  current_value: string | number;
  unit?: string;
  status?: string;
}

export interface CommandCenterData {
  global_risk_index: number;
  high_risk_zones: number;
  average_adjusted_risk: number;
  markers: Marker[];
  districts: DistrictCard[];
  recommendations: Recommendation[];
  executive_metrics: ExecMetric[];
  decision_brief: string;
  ai_confidence: number;
  response_latency_status: string;
  avg_response_time_min: number;
}

export interface OperationsData {
  ground_units_active: number;
  ground_units_total: number;
  ground_units_pct: number;
  aerial_active: number;
  aerial_total: number;
  aerial_pct: number;
  personnel_active: number;
  personnel_total: number;
  personnel_pct: number;
  avg_response_time_min: number;
  api_latency_ms: number;
  cpu_percent: number;
  memory_percent: number;
  memory_mb: number;
  system_health_pct: number;
  dispatch_items: { title: string; subtitle: string; priority: string; district: string; action_type: string }[];
  district_intelligence: Record<string, unknown>[];
  bottlenecks: { label: string; detail: string }[];
  refresh_healthy: boolean;
  markers: Marker[];
}

export interface SimulationData {
  scenarios: Record<string, unknown>[];
  best_scenario: Record<string, unknown>;
  risk_reduction_pct: number;
  net_benefit: number;
  spread_bars: { label: string; value: number }[];
  efficiency_pct: number;
  time_risk: Record<string, unknown>[];
  repeat_offenders: Record<string, unknown>[];
  sentinel_brief: string;
  iteration_current: number;
  iteration_total: number;
  markers: Marker[];
}

export interface ComplianceData {
  repeat_offenders: Record<string, unknown>[];
  executive_metrics: ExecMetric[];
  kpis: { label: string; value: string; status: string }[];
  policy_violations_30d: number;
  compliance_rate: number;
  frameworks: { name: string; status: string }[];
}

export interface RoadmapData {
  badges: string[];
  counts: {
    bronze_tables: number;
    silver_tables: number;
    gold_tables: number;
    total_tables: number;
    total_records: number;
    validation_checks: number;
  };
  modules: { id: string; title: string; details: string[] }[];
  pipeline_nodes: string[];
  known_limitations: string[];
}

export interface HealthData {
  status: string;
  generated_at: string;
  databricks_enabled: boolean;
  gemini_enabled: boolean;
  source_status: string;
  last_refresh_completed_at: string | null;
  last_refresh_success: boolean;
  query_latency_ms: number;
  ai_latency_ms: number;
  ws_connections: number;
  cpu_percent: number;
  memory_percent: number;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const api = {
  health: () => get<HealthData>("/api/health"),
  commandCenter: () => get<Envelope<CommandCenterData>>("/api/dashboard/command-center"),
  operations: () => get<Envelope<OperationsData>>("/api/dashboard/operations"),
  simulation: () => get<Envelope<SimulationData>>("/api/dashboard/simulation"),
  compliance: () => get<Envelope<ComplianceData>>("/api/dashboard/compliance"),
  roadmap: () => get<Envelope<RoadmapData>>("/api/dashboard/roadmap"),
  optimize: (params?: { budget_cap?: number; max_districts?: number }) =>
    post<{ success: boolean; result: unknown; generated_at: string }>("/api/optimize", params),
  runSimulation: (params?: unknown) =>
    post<{ success: boolean; result: unknown; generated_at: string }>("/api/simulations/run", params),
  sos: (params?: { user_id?: string }) =>
    post<{ success: boolean; error?: string; message_sid?: string }>("/api/sos", params),
  reportCsv: () => `${BASE}/api/reports/compliance?format=csv`,
  reportPdf: () => `${BASE}/api/reports/compliance?format=pdf`,
};

// ---------------------------------------------------------------------------
// WebSocket helper
// ---------------------------------------------------------------------------

export type WsEventType =
  | "connected"
  | "ping"
  | "snapshot_updated"
  | "system_metrics"
  | "optimization_started"
  | "optimization_completed"
  | "simulation_completed"
  | "report_ready"
  | "pipeline_alert";

export interface WsEvent {
  type: WsEventType;
  [key: string]: unknown;
}

export function createLiveSocket(
  onEvent: (e: WsEvent) => void,
  onClose?: () => void
): WebSocket {
  const wsBase = BASE.replace(/^http/, "ws");
  const ws = new WebSocket(`${wsBase}/ws/live`);
  ws.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data) as WsEvent);
    } catch {
      // ignore malformed frames
    }
  };
  ws.onclose = () => onClose?.();
  return ws;
}
