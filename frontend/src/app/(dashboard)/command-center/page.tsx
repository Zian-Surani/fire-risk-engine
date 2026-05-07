"use client";
import React from "react";
import { AlertTriangle, ArrowDown, ArrowUp, Zap, Droplets, Cpu, RadioTower } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { DistrictGlobeLazy } from "@/components/dashboard/DistrictGlobeLazy";
import { api, type Envelope, type CommandCenterData, type Recommendation } from "@/lib/api";

const ACTION_ICONS: Record<string, React.ReactNode> = {
  DEPLOY: <Droplets size={20} />,
  INSPECT: <Cpu size={20} />,
  REROUTE: <RadioTower size={20} />,
};
const ACTION_COLORS: Record<string, string> = {
  DEPLOY: "primary",
  INSPECT: "tertiary",
  REROUTE: "secondary",
};
const CC: Record<string, Record<string, string>> = {
  primary: { bg: "bg-primary/5", text: "text-primary", border: "border-primary/10", hover: "group-hover:bg-primary/20" },
  tertiary: { bg: "bg-tertiary/5", text: "text-tertiary", border: "border-tertiary/10", hover: "group-hover:bg-tertiary/20" },
  secondary: { bg: "bg-secondary/5", text: "text-secondary", border: "border-secondary/10", hover: "group-hover:bg-secondary/20" },
};

function StatusBadge({ status }: { status: string }) {
  const good = status === "live" || status === "NOMINAL";
  return (
    <span className={`text-[10px] font-bold tracking-widest px-3 py-1 rounded-full border ${good ? "text-secondary bg-secondary/10 border-secondary/20" : "text-tertiary bg-tertiary/10 border-tertiary/20"}`}>
      {status === "live" ? "LIVE" : status === "mock" ? "DEMO" : status.toUpperCase()}
    </span>
  );
}

export default function CommandCenter() {
  const { data: envelope, error, refresh } = useDashboard<Envelope<CommandCenterData>>({
    fetcher: api.commandCenter, intervalMs: 5000,
  });
  useLiveSocket((e) => { if (e.type === "snapshot_updated" || e.type === "optimization_completed" || e.type === "simulation_completed") refresh(); });

  const d = envelope?.data;
  const lastOpt = envelope?.last_optimization as { narrative?: string; improvement_metrics?: Record<string, number> } | null | undefined;
  const lastSim = envelope?.last_simulation as { data?: { risk_reduction_pct?: number } } | null | undefined;
  const sourceStatus = envelope?.source_status ?? "initializing";
  const qms = envelope?.query_latency_ms ?? 0;
  const lastUpdate = envelope?.generated_at ? new Date(envelope.generated_at).toLocaleTimeString() : "02m AGO";
  const globalRiskIndex = d ? d.global_risk_index.toFixed(1) : "74.8";
  const highRiskZones = d ? String(d.high_risk_zones) : "12";
  const aiConfidence = d ? d.ai_confidence.toFixed(1) : "68.2";
  const avgResponse = d ? d.avg_response_time_min.toFixed(1) : "\u2014";
  const latencyStatus = d?.response_latency_status ?? "DEGRADED";
  const districts = d?.districts ?? [];
  const recs: Recommendation[] = d?.recommendations ?? [];

  return (
    <div className="flex flex-col gap-8 pb-12 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="h-16 bg-[#0f1419]/80 backdrop-blur-xl flex justify-between items-center px-8 border-b border-outline-variant/10 w-full mb-8">
        <div className="flex items-center gap-6">
          <h1 className="font-headline text-lg font-extrabold tracking-tight text-primary uppercase">Command Center</h1>
          <div className="hidden lg:flex items-center gap-4 text-xs font-label tracking-widest text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full shadow-[0_0_8px_rgba(113,215,205,0.4)] ${sourceStatus === "live" ? "bg-secondary animate-pulse" : "bg-slate-500"}`}></span>
              {sourceStatus === "live" ? "SYSTEMS NOMINAL" : sourceStatus === "mock" ? "DEMO MODE" : "INITIALIZING"}
            </span>
            <span className="text-outline-variant/30">|</span>
            <span>LAST UPDATE: {lastUpdate}</span>
            {qms > 0 && <><span className="text-outline-variant/30">|</span><span>{qms.toFixed(0)}ms</span></>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <StatusBadge status={sourceStatus} />
          <div className="relative hidden md:block">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-500 text-sm">search</span>
            <input className="clay-panel clay-interactive border-none rounded-full pl-10 pr-4 py-1.5 text-sm text-on-surface focus:ring-1 focus:ring-primary/40 w-64 transition-all" placeholder="Scan coordinates..." type="text"/>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-8 px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error flex items-center gap-2">
          <AlertTriangle size={14} /> Backend unavailable &mdash; showing demo data.
        </div>
      )}

      <div className="flex flex-col xl:flex-row gap-8">
        <div className="xl:flex-[1.8] space-y-8">
          <div className="bg-surface-container-low rounded-3xl overflow-hidden relative ambient-glow-primary group shadow-2xl">
            <div className="absolute top-6 left-6 z-10">
              <div className="bg-background/80 backdrop-blur-md px-4 py-2 rounded-full border border-outline-variant/20 inline-flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-tertiary animate-pulse shadow-[0_0_8px_rgba(255,205,201,0.5)]"></div>
                <span className="text-[10px] font-label tracking-widest uppercase font-bold text-tertiary">Active Threat Map</span>
              </div>
            </div>
            <div className="absolute bottom-6 left-6 z-10 bg-[#0a0f14]/90 backdrop-blur-md p-6 rounded-3xl border border-outline-variant/20">
              <div className="flex items-end gap-10">
                <div>
                  <p className="text-[10px] font-label tracking-widest text-slate-500 uppercase mb-2">Global Risk Index</p>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/40"></span>
                    <p className="text-4xl font-headline font-extrabold text-primary">{globalRiskIndex}</p>
                  </div>
                </div>
                <div className="h-10 w-[1px] bg-outline-variant/20"></div>
                <div>
                  <p className="text-[10px] font-label tracking-widest text-slate-500 uppercase mb-2">High Risk Zones</p>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-on-surface/20"></span>
                    <p className="text-4xl font-headline font-extrabold text-on-surface">{highRiskZones}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="h-[520px] w-full relative overflow-hidden">
              <DistrictGlobeLazy markers={d?.markers ?? []} mapHeightClass="h-full min-h-[520px]" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[0, 1, 2].map((i) => {
              const dist = districts[i];
              const band = (dist?.adjusted_risk_band ?? ["MEDIUM","HIGH","LOW"][i]) as "HIGH"|"MEDIUM"|"LOW";
              const score = dist ? dist.adjusted_risk_score : [42, 89, 15][i];
              const label = dist?.display_district ?? ["Northern Ridge","Dry Creek Basin","Coastal Flats"][i];
              const textColor = band === "HIGH" ? "text-tertiary" : band === "MEDIUM" ? "text-primary" : "text-on-surface";
              const hoverBorder = band === "HIGH" ? "hover:border-tertiary/20" : band === "MEDIUM" ? "hover:border-primary/20" : "hover:border-secondary/20";
              return (
                <div key={i} className={`bg-surface-container-high p-8 rounded-3xl relative group ${hoverBorder} transition-all`}>
                  <div className="absolute top-4 right-4 w-1 h-1 rounded-full bg-slate-700"></div>
                  <p className="text-[10px] font-label tracking-widest text-slate-500 uppercase mb-4">{label}</p>
                  <div className="flex justify-between items-end">
                    <div>
                      <span className={`text-4xl font-headline font-bold ${textColor}`}>{typeof score === "number" ? score.toFixed(1) : score}</span>
                      <span className="text-xs text-slate-500 ml-1">{dist ? "adj" : "/100"}</span>
                    </div>
                    <div className={`flex items-center ${textColor} text-sm font-semibold`}>
                      {band === "HIGH" ? <ArrowUp size={14} className="mr-1" /> : band === "LOW" ? <ArrowDown size={14} className="mr-1" /> : null}
                      {dist ? band : ["-12%","+24%","-04%"][i]}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="xl:flex-1 space-y-8">
          <div className="bg-surface-container-high p-8 rounded-3xl ambient-glow-primary">
            <h3 className="font-headline text-lg font-bold text-primary mb-8 flex items-center gap-3">
              <span className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center"><Zap size={20} className="text-primary" /></span>
              STRATEGIC ACTIONS
            </h3>
            <div className="space-y-8">
              {recs.length === 0 ? [
                { icon: <Droplets size={20}/>, title: "Pre-emptive Hydration", desc: "Initiate controlled moisture release in Sector 7G to offset peak thermal window.", color: "primary" },
                { icon: <Cpu size={20}/>, title: "Node Recalibration", desc: "Thermal sensor #242 is reporting variance. Deploy diagnostic drone.", color: "tertiary" },
                { icon: <RadioTower size={20}/>, title: "Public Advisory", desc: "Elevate threat level to Alert for Dry Creek Basin interface zones.", color: "secondary" },
              ].map((item, i) => {
                const c = CC[item.color];
                return (
                  <div key={i} className="flex gap-5 group">
                    <div className={`flex-shrink-0 w-12 h-12 rounded-full ${c.bg} flex items-center justify-center ${c.text} border ${c.border} transition-all ${c.hover} group-hover:scale-105`}>{item.icon}</div>
                    <div><h4 className="text-sm font-bold text-on-surface mb-1">{item.title}</h4><p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p></div>
                  </div>
                );
              }) : recs.map((rec, i) => {
                const actionType = rec.action_type ?? (i === 0 ? "DEPLOY" : i === 1 ? "INSPECT" : "REROUTE");
                const color = ACTION_COLORS[actionType] ?? "secondary";
                const c = CC[color];
                return (
                  <div key={i} className="flex gap-5 group">
                    <div className={`flex-shrink-0 w-12 h-12 rounded-full ${c.bg} flex items-center justify-center ${c.text} border ${c.border} transition-all ${c.hover} group-hover:scale-105`}>
                      {ACTION_ICONS[actionType] ?? <Zap size={20} />}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-on-surface mb-1">{actionType.charAt(0) + actionType.slice(1).toLowerCase()} Action</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">{rec.description}</p>
                      {rec.estimated_impact && <p className="text-[10px] text-slate-500 mt-1">{rec.estimated_impact}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
            <button className="w-full mt-10 py-4 bg-primary text-on-primary-container font-extrabold rounded-full text-xs uppercase tracking-widest transition-all hover:brightness-110 active:scale-[0.98] shadow-lg shadow-primary/20">
              EXECUTE ALL RECS
            </button>
          </div>

          <div className="clay-panel clay-interactive p-8 rounded-3xl ">
            <div className="flex justify-between items-start mb-8">
              <div>
                <h3 className="font-headline text-sm font-bold text-on-surface-variant">RESPONSE LATENCY</h3>
                <p className="text-[10px] font-label text-slate-500 uppercase tracking-widest mt-1">{d ? `Avg: ${avgResponse} min` : "Secondary Units"}</p>
              </div>
              <StatusBadge status={latencyStatus} />
            </div>
            <div className="h-28 relative mt-4">
              <svg viewBox="0 0 100 60" preserveAspectRatio="none" className="w-full h-full overflow-visible">
                <path 
                  d="M 0 50 L 15 45 L 30 55 L 45 20 L 60 30 L 75 10 L 90 25 L 100 20 L 100 60 L 0 60 Z" 
                  fill="url(#gradient-cc-risk)"
                  className="transition-all duration-700 opacity-20"
                />
                <path 
                  d="M 0 50 L 15 45 L 30 55 L 45 20 L 60 30 L 75 10 L 90 25 L 100 20" 
                  fill="none" 
                  stroke={latencyStatus === "DEGRADED" ? "#ffb4ab" : "#71d7cd"} 
                  strokeWidth="2"
                  strokeLinecap="round"
                  className="transition-all duration-700"
                />
                <defs>
                   <linearGradient id="gradient-cc-risk" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={latencyStatus === "DEGRADED" ? "#ffb4ab" : "#71d7cd"} stopOpacity="0.4" />
                      <stop offset="100%" stopColor={latencyStatus === "DEGRADED" ? "#ffb4ab" : "#71d7cd"} stopOpacity="0" />
                   </linearGradient>
                </defs>
              </svg>
              <div className="absolute top-0 left-0 bg-background/40 backdrop-blur-sm px-2 py-1 rounded-md border border-white/5">
                <p className="text-[10px] font-mono text-tertiary">ANOMALY DETECTED</p>
                <p className="text-[8px] text-slate-500 uppercase">Sector 7 & 9 Variance</p>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-outline-variant/10">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center text-tertiary ">
                  <AlertTriangle size={20} className="text-tertiary" />
                </div>
                <p className="text-[11px] text-slate-400 leading-normal">
                  {d?.decision_brief
                    ? d.decision_brief.slice(0, 110) + (d.decision_brief.length > 110 ? "\u2026" : "")
                    : "Response times in Dry Creek exceed safety thresholds by 12.4%."}
                  {lastOpt?.narrative && (
                    <span className="block mt-2 text-secondary/90">{lastOpt.narrative.slice(0, 120)}{lastOpt.narrative.length > 120 ? "\u2026" : ""}</span>
                  )}
                  {lastSim?.data?.risk_reduction_pct != null && (
                    <span className="block mt-1 text-slate-500">Last sim delta: {lastSim.data.risk_reduction_pct.toFixed(1)}%</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="relative overflow-hidden bg-gradient-to-br from-[#1b2025] to-[#0a0f14] p-8 rounded-3xl ">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <div className="w-24 h-24 border-[12px] border-primary rounded-full" style={{clipPath: "polygon(0 0, 100% 0, 100% 50%, 0 50%)", transform: "rotate(45deg)"}}></div>
            </div>
            <div className="flex flex-col items-center">
              <div className="relative w-40 h-20 overflow-hidden">
                <div className="absolute top-0 left-0 w-40 h-40 border-[12px] border-surface-container-highest rounded-full opacity-30"></div>
                <div className="absolute top-0 left-0 w-40 h-40 border-[12px] border-primary rounded-full shadow-[0_0_15px_rgba(255,208,159,0.2)]" style={{clipPath: "polygon(0 0, 100% 0, 100% 50%, 0 50%)", transform: `rotate(${100 + (d ? d.ai_confidence : 68) * 0.8}deg)`}}></div>
              </div>
              <div className="text-center mt-6">
                <p className="text-3xl font-headline font-extrabold text-on-surface">{aiConfidence}<span className="text-sm font-normal text-slate-500 ml-1">%</span></p>
                <p className="text-[10px] font-label tracking-widest text-slate-500 uppercase mt-1">AI System Confidence</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
