"""Helper script to write frontend page files with live data bindings."""
import os

BASE = r"C:\Users\zians\Downloads\FIRE\frontend\src\app\(dashboard)"

# ============================================================
# Command Center
# ============================================================
CC = r'''"use client";
import React from "react";
import { AlertTriangle, ArrowDown, ArrowUp, Zap, Droplets, Cpu, RadioTower } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
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
  const { data, loading: _loading, error, refresh } = useDashboard<Envelope<CommandCenterData>>({
    fetcher: api.commandCenter, intervalMs: 5000,
  });
  useLiveSocket((e) => { if (e.type === "snapshot_updated") refresh(); });

  const d = data?.data;
  const sourceStatus = data?.source_status ?? "initializing";
  const qms = data?.query_latency_ms ?? 0;
  const lastUpdate = data?.generated_at ? new Date(data.generated_at).toLocaleTimeString() : "02m AGO";
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
            <div className="h-[520px] w-full bg-surface-container-highest relative">
              <img alt="Topographic risk heatmap" className="w-full h-full object-cover mix-blend-luminosity opacity-40 group-hover:scale-105 transition-transform duration-1000" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAS4PB_7fnF25qg1v5qqNk-o8mtr8iIiALLkczHHtmj28wES5XTDz1DB5CWDE2UKrrwXiOrzYSXp7dpd3PAFsyxWQ04smNBg4Wa-aLyvecTLCZd5pG-olpOI5CYoE8Pcwk0zRA7_JkLKDeGs5n2Q7FZIVvl2pRr5LlJau68td3G4UB9NXk6s_765myMv09Gw2uheZWhaCWOOlBl0X8FE_aD3rD--dRBdEzTw3MbcfZc-trkfepR8oHdEZ1NNM_BDdCQ_ph-mwhfw0Q"/>
              {(d?.markers ?? []).slice(0, 8).map((m, i) => (
                <div key={i} title={`${m.display_district}: ${m.adjusted_risk_band}`} className="absolute rounded-full animate-pulse"
                  style={{ width: m.visual_severity_level * 6 + 6, height: m.visual_severity_level * 6 + 6, backgroundColor: m.marker_color, opacity: 0.75, top: `${20 + (i * 37) % 60}%`, left: `${15 + (i * 41) % 70}%`, boxShadow: `0 0 12px ${m.marker_color}` }} />
              ))}
              <div className="absolute top-1/4 left-1/3 w-32 h-32 bg-primary/10 rounded-full blur-[100px]"></div>
              <div className="absolute bottom-1/3 right-1/4 w-48 h-48 bg-tertiary/10 rounded-full blur-[120px]"></div>
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
            <div className="space-y-6">
              {districts.slice(0,2).length > 0 ? districts.slice(0,2).map((dist, i) => {
                const pct = Math.min(100, Math.round((dist.adjusted_risk_score / 10) * 100));
                return (
                  <div key={i}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-400">{dist.display_district}</span>
                      <span className="text-xs font-semibold text-on-surface">{dist.adjusted_risk_band} risk</span>
                    </div>
                    <div className="w-full bg-background h-1.5 rounded-full overflow-hidden flex items-center p-0.5">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: dist.marker_color, boxShadow: `0 0 8px ${dist.marker_color}60` }} />
                    </div>
                  </div>
                );
              }) : (
                <>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-400">Unit 14-B (Volunteer)</span><span className="text-xs font-semibold text-on-surface">18.4 min</span>
                    </div>
                    <div className="w-full bg-background h-1.5 rounded-full overflow-hidden flex items-center p-0.5">
                      <div className="bg-tertiary h-full w-[85%] rounded-full shadow-[0_0_8px_rgba(255,205,201,0.4)]"></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-400">Unit 09-D (Logistics)</span><span className="text-xs font-semibold text-on-surface">12.1 min</span>
                    </div>
                    <div className="w-full bg-background h-1.5 rounded-full overflow-hidden flex items-center p-0.5">
                      <div className="bg-primary h-full w-[60%] rounded-full shadow-[0_0_8px_rgba(255,208,159,0.4)]"></div>
                    </div>
                  </div>
                </>
              )}
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
'''

# ============================================================
# Operations
# ============================================================
OPS = r'''"use client";
import React, { useState } from "react";
import { Search, Layers, Crosshair, Zap, Navigation, ArrowRight, Activity, TriangleAlert, Car, Fuel, RefreshCw } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { api, type Envelope, type OperationsData } from "@/lib/api";

export default function Operations() {
  const { data, loading: _loading, error, refresh } = useDashboard<Envelope<OperationsData>>({
    fetcher: api.operations, intervalMs: 5000,
  });
  useLiveSocket((e) => { if (e.type === "snapshot_updated" || e.type === "system_metrics") refresh(); });

  const [optimizing, setOptimizing] = useState(false);

  const d = data?.data;
  const sourceStatus = data?.source_status ?? "initializing";

  const groundPct = d?.ground_units_pct ?? 75;
  const aerialPct = d?.aerial_pct ?? 66;
  const personnelPct = d?.personnel_pct ?? 100;
  const groundLabel = d ? `${d.ground_units_active} / ${d.ground_units_total}` : "24 / 32";
  const aerialLabel = d ? `${d.aerial_active} / ${d.aerial_total}` : "4 / 6";
  const personnelLabel = d ? `${d.personnel_active} / ${d.personnel_total}` : "12 / 12";
  const systemHealth = d?.system_health_pct ?? 98.4;
  const dispatch = d?.dispatch_items ?? [];
  const bottlenecks = d?.bottlenecks ?? [];
  const avgResp = d?.avg_response_time_min?.toFixed(1) ?? "—";
  const apiLatency = d?.api_latency_ms?.toFixed(0) ?? "—";
  const cpu = d?.cpu_percent ?? 0;
  const mem = d?.memory_percent ?? 0;

  async function handleOptimize() {
    setOptimizing(true);
    try { await api.optimize(); } finally { setOptimizing(false); refresh(); }
  }

  return (
    <div className="flex flex-col gap-8 pb-12 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="left-20 md:left-64 h-16 bg-background/80 backdrop-blur-xl flex justify-between items-center px-8 border-b border-outline-variant/10 w-full mb-8">
        <div className="flex items-center gap-4">
          <h1 className="font-headline text-xl font-extrabold tracking-tight text-on-surface">Operations Hub</h1>
          <div className="flex items-center gap-2 px-2 py-0.5 rounded-full bg-secondary/10 border border-secondary/20">
            <span className={`w-1.5 h-1.5 rounded-full ${sourceStatus === "live" ? "bg-secondary animate-pulse" : "bg-slate-500"}`}></span>
            <span className="text-secondary text-[10px] font-bold uppercase tracking-tighter">{sourceStatus === "live" ? "Live Sync" : "Demo"}</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative hidden lg:block group">
            <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm group-focus-within:text-primary transition-colors" />
            <input className="bg-surface-container-low border-none rounded-full py-1.5 pl-10 pr-4 text-xs w-64 focus:ring-1 focus:ring-primary text-on-surface placeholder-slate-600" placeholder="Search sectors..." type="text"/>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-8 px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error flex gap-2 items-center">
          <TriangleAlert size={14} /> Backend unavailable &mdash; demo mode.
        </div>
      )}

      <div className="absolute inset-0 pacman-dots opacity-30 pointer-events-none"></div>
      <div className="p-8 relative z-10 flex flex-col lg:flex-row gap-6 h-auto lg:h-[calc(100vh-4rem)]">
        <div className="flex-1 lg:flex-[1.6] flex flex-col gap-6">
          <div className="flex-1 bg-surface-container-high rounded-3xl overflow-hidden relative group shadow-2xl">
            <div className="absolute inset-0 bg-[#0a0f14] overflow-hidden">
              <img className="w-full h-full object-cover opacity-40 grayscale" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCKCs9_VvgqRXCeUdI5iMC7BEh0Bvt5Ic2tVFvSExMciI2dLQUe8V5LyVguerGSwD57bq-2Glir0GOWxwQxRX-UbpzEnWAH2rJrRpL3N4jKa8Afl1l42kg-RIVA63Kpv4OfUf4DTpqyFf3SPxLWRpyGFCs6FKarFI0kd3wAXzzYGEj8dNF2Mb7FHImVUN-hEWSuMFVwgf-kkONyWIxrerjMFAvtehxhw6xLjz6EBmEr1lzCGfN4O2e3gHgQ9Ae7WnJ4COHvr9c1aTQ" alt="map"/>
              <div className="absolute top-1/4 left-1/3 w-3 h-3 bg-primary rounded-full blur-[2px] opacity-80 animate-pulse"></div>
              <div className="absolute top-1/2 left-2/3 w-2 h-2 bg-secondary rounded-full blur-[1px] opacity-60"></div>
              <div className="absolute bottom-1/3 left-1/4 w-4 h-4 bg-primary rounded-full blur-[3px] opacity-40 animate-ping"></div>
              <div className="absolute inset-0 p-8 pointer-events-none">
                <div className="flex justify-between items-start">
                  <div className="glass-panel p-5 rounded-3xl border border-outline-variant/20 shadow-xl pointer-events-auto">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-2 h-2 rounded-full bg-secondary"></span>
                      <p className="text-[10px] font-label uppercase tracking-widest text-secondary/80">Active Sector</p>
                    </div>
                    <p className="text-2xl font-headline font-extrabold text-on-surface tracking-tight">
                      {d?.district_intelligence?.[0] ? `District ${(d.district_intelligence[0] as Record<string,unknown>).district ?? "—"}` : "District 09-Alpha"}
                    </p>
                  </div>
                  <div className="flex flex-col gap-3 pointer-events-auto">
                    <button className="w-12 h-12 bg-surface-container-low/80 backdrop-blur rounded-full flex items-center justify-center text-on-surface hover:bg-primary-container hover:text-on-primary-container transition-all border border-outline-variant/20"><Layers size={20} /></button>
                    <button className="w-12 h-12 bg-surface-container-low/80 backdrop-blur rounded-full flex items-center justify-center text-on-surface hover:bg-primary-container hover:text-on-primary-container transition-all border border-outline-variant/20"><Crosshair size={20} /></button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="h-auto lg:h-64 flex flex-col sm:flex-row gap-6">
            <div className="flex-[1.5] bg-surface-container-high rounded-3xl p-6 relative overflow-hidden group">
              <div className="absolute top-4 right-4 w-2 h-2 bg-primary/20 rounded-full"></div>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="font-headline font-bold text-lg text-on-surface">Dispatch Hub</h3>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-0.5">Automated Intelligence</p>
                </div>
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Zap size={20} className="text-primary" />
                </div>
              </div>
              <div className="space-y-3">
                {dispatch.length > 0 ? dispatch.slice(0,2).map((item, i) => (
                  <div key={i} className="bg-surface-container-low/50 p-4 rounded-3xl flex items-center justify-between group/item hover:bg-surface-container-low transition-all border border-transparent hover:border-primary/20 cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className={`w-2 h-2 rounded-full ${i === 0 ? "bg-primary" : "bg-secondary"}`}></div>
                      <div>
                        <p className="text-xs font-bold text-on-surface">{item.title}</p>
                        <p className="text-[10px] text-slate-400">{item.subtitle}</p>
                      </div>
                    </div>
                    <ArrowRight size={20} className={`text-slate-600 group-hover/item:${i === 0 ? "text-primary" : "text-secondary"} transition-colors`} />
                  </div>
                )) : (
                  <>
                    <div className="bg-surface-container-low/50 p-4 rounded-3xl flex items-center justify-between group/item hover:bg-surface-container-low transition-all border border-transparent hover:border-primary/20 cursor-pointer">
                      <div className="flex items-center gap-4"><div className="w-2 h-2 rounded-full bg-primary"></div><div><p className="text-xs font-bold text-on-surface">Deploy Unit E-42</p><p className="text-[10px] text-slate-400">ETA 4m to Sector G-12. Thermal signature detected.</p></div></div>
                      <ArrowRight size={20} className="text-slate-600 group-hover/item:text-primary transition-colors" />
                    </div>
                    <div className="bg-surface-container-low/50 p-4 rounded-3xl flex items-center justify-between group/item hover:bg-surface-container-low transition-all border border-transparent hover:border-secondary/20 cursor-pointer">
                      <div className="flex items-center gap-4"><div className="w-2 h-2 rounded-full bg-secondary"></div><div><p className="text-xs font-bold text-on-surface">Reroute Tanker 09</p><p className="text-[10px] text-slate-400">Redundancy detected in Sector F-4.</p></div></div>
                      <ArrowRight size={20} className="text-slate-600 group-hover/item:text-secondary transition-colors" />
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="flex-1 bg-primary-container text-on-primary-container rounded-3xl p-6 flex flex-col justify-between relative overflow-hidden">
              <div className="absolute -right-12 -top-12 w-40 h-40 bg-white/10 rounded-full"></div>
              <p className="font-label text-[10px] tracking-widest uppercase font-black opacity-60">System Health</p>
              <div>
                <div className="text-5xl font-headline font-extrabold tracking-tighter mb-1">{systemHealth.toFixed(1)}<span className="text-2xl font-bold opacity-70">%</span></div>
                <p className="text-[11px] leading-tight font-semibold opacity-80 max-w-[120px]">CPU {cpu.toFixed(0)}% | Mem {mem.toFixed(0)}%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-6">
          <div className="bg-surface-container-high rounded-3xl p-8 shadow-xl">
            <div className="flex justify-between items-center mb-8">
              <h3 className="font-headline font-bold text-on-surface">Resource Load</h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-secondary"></span><span className="text-[10px] font-label text-slate-500 uppercase tracking-tighter">Active</span></div>
                <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-surface-container-highest"></span><span className="text-[10px] font-label text-slate-500 uppercase tracking-tighter">Idle</span></div>
              </div>
            </div>
            <div className="space-y-8">
              {[
                { label: "Ground Units", value: groundLabel, pct: groundPct, color: "bg-secondary" },
                { label: "Aerial Support", value: aerialLabel, pct: aerialPct, color: "bg-secondary" },
                { label: "Personnel", value: personnelLabel, pct: personnelPct, color: "bg-primary shadow-[0_0_10px_rgba(255,208,159,0.3)]" },
              ].map((item, i) => (
                <div key={i} className="space-y-3">
                  <div className="flex justify-between items-center px-1">
                    <span className="text-xs font-semibold text-slate-400">{item.label}</span>
                    <span className={`text-xs font-bold ${i < 2 ? "text-secondary" : "text-primary"}`}>{item.value}</span>
                  </div>
                  <div className="h-2 bg-surface-container-low rounded-full overflow-hidden ">
                    <div className={`h-full ${item.color} rounded-full`} style={{width: `${item.pct}%`}}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex-1 bg-surface-container-high rounded-3xl p-8 flex flex-col gap-6 shadow-xl">
            <div>
              <h3 className="font-headline font-bold text-on-surface">Response Latency</h3>
              <div className="pellet-border pb-1 mt-1">
                <p className="text-[10px] text-slate-500 font-label tracking-widest uppercase">Avg: {avgResp} min &nbsp;|&nbsp; API: {apiLatency}ms</p>
              </div>
            </div>
            <div className="flex-1 flex items-end gap-3 px-2 relative min-h-[140px]">
              <div className="absolute inset-0 flex flex-col justify-between opacity-5 pointer-events-none">
                <div className="border-b border-on-surface"></div>
                <div className="border-b border-on-surface"></div>
                <div className="border-b border-on-surface"></div>
              </div>
              {[30, 45, 65, 95, 75, 40].map((h, i) => (
                <div key={i} className={`flex-1 ${i === 3 ? "bg-primary/20 border-x border-t border-primary/30" : "bg-surface-container-low"} rounded-t-full relative group transition-all hover:bg-surface-container-highest`} style={{height: `${h}%`}}>
                  <div className={`absolute -top-1 left-1/2 -translate-x-1/2 ${i === 3 ? "w-2 h-2 bg-primary shadow-[0_0_8px_#ffd09f]" : "w-1.5 h-1.5 bg-slate-600"} rounded-full`}></div>
                </div>
              ))}
            </div>
            <div className="pt-6 border-t border-outline-variant/10">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-full bg-error/10 flex items-center justify-center">
                  <TriangleAlert size={20} className="text-error text-lg" />
                </div>
                <h4 className="text-xs font-bold text-on-surface uppercase tracking-widest">Active Bottlenecks</h4>
              </div>
              <div className="space-y-4">
                {bottlenecks.length > 0 ? bottlenecks.map((b, i) => (
                  <div key={i} className="flex gap-4 group cursor-pointer">
                    <div className="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center shrink-0 group-hover:bg-error/10 group-hover:border-error/20 transition-colors">
                      <Car size={20} className="text-tertiary" />
                    </div>
                    <div className="flex-1">
                      <p className="text-xs font-bold text-on-surface">{b.label}</p>
                      <p className="text-[10px] text-slate-500 leading-relaxed">{b.detail}</p>
                    </div>
                  </div>
                )) : (
                  <>
                    <div className="flex gap-4 group cursor-pointer">
                      <div className="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center shrink-0"><Car size={20} className="text-tertiary" /></div>
                      <div className="flex-1"><p className="text-xs font-bold text-on-surface">Hwy 101 Congestion</p><p className="text-[10px] text-slate-500 leading-relaxed">+12m delay for North Sector units.</p></div>
                    </div>
                    <div className="flex gap-4 group cursor-pointer">
                      <div className="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center shrink-0"><Fuel size={20} className="text-tertiary" /></div>
                      <div className="flex-1"><p className="text-xs font-bold text-on-surface">Refuel Queue - Station 4</p><p className="text-[10px] text-slate-500 leading-relaxed">Recommend rerouting to Station 7.</p></div>
                    </div>
                  </>
                )}
              </div>
            </div>
            <button onClick={handleOptimize} disabled={optimizing} className="mt-auto w-full py-4 bg-primary text-on-primary-container font-black text-[10px] tracking-[0.2em] rounded-full shadow-lg shadow-primary/20 flex items-center justify-center gap-3 group active:scale-95 transition-all disabled:opacity-60">
              {optimizing ? "OPTIMIZING..." : "OPTIMIZE DEPLOYMENT"}
              <RefreshCw size={20} className={`text-lg ${optimizing ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
'''

# ============================================================
# Simulation AI
# ============================================================
SIM = r'''"use client";
import React, { useState } from "react";
import { Sparkles, Target } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { api, type Envelope, type SimulationData } from "@/lib/api";

export default function SimulationAI() {
  const { data, loading: _loading, error, refresh } = useDashboard<Envelope<SimulationData>>({
    fetcher: api.simulation, intervalMs: 5000,
  });
  useLiveSocket((e) => { if (e.type === "snapshot_updated" || e.type === "simulation_completed") refresh(); });

  const [running, setRunning] = useState(false);
  const [gridUnits, setGridUnits] = useState(14);

  const d = data?.data;
  const sourceStatus = data?.source_status ?? "initializing";
  const riskReduction = d ? d.risk_reduction_pct.toFixed(1) : "-18.4";
  const riskReductionLabel = d ? (d.risk_reduction_pct < 0 ? `${d.risk_reduction_pct.toFixed(1)}%` : `+${d.risk_reduction_pct.toFixed(1)}%`) : "-18.4%";
  const netBenefit = d ? `+${(d.net_benefit / 1000).toFixed(0)}k` : "+340k";
  const efficiencyPct = d?.efficiency_pct ?? 72;
  const sentinelBrief = d?.sentinel_brief ?? "Deployment to Northeast corridor reduces critical latency by 4.2m in high-density timber zones.\n\nNotice: 1-95 corridor will experience a 12% coverage deficit. Recommending secondary unit swap.";
  const iterCurrent = d?.iteration_current ?? 1402;
  const iterTotal = d?.iteration_total ?? 5000;
  const spreadBars = d?.spread_bars ?? [
    {label:"00h",value:0.4},{label:"04h",value:0.6},{label:"08h",value:0.3},
    {label:"12h",value:0.8},{label:"16h",value:0.95},{label:"20h",value:0.5}
  ];

  const circumference = 2 * Math.PI * 40;
  const dashOffset = circumference * (1 - efficiencyPct / 100);

  async function handleRun() {
    setRunning(true);
    try { await api.runSimulation({ grid_units: gridUnits }); } finally { setRunning(false); refresh(); }
  }

  return (
    <div className="flex flex-col gap-8 pb-12 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="left-0 h-16 bg-[#0f1419]/80 backdrop-blur-xl flex justify-between items-center px-8 border-b border-white/5 w-full mb-8">
        <div className="flex items-center gap-6">
          <h1 className="text-sm font-bold font-headline tracking-widest uppercase text-primary/80">Alpha-7 Simulation</h1>
          <div className="h-3 w-[1px] bg-white/10"></div>
          <span className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Strategic Layer</span>
          {sourceStatus !== "initializing" && (
            <span className={`text-[10px] font-bold tracking-widest px-2 py-0.5 rounded-full border ${sourceStatus === "live" ? "text-secondary border-secondary/30" : "text-tertiary border-tertiary/30"}`}>{sourceStatus.toUpperCase()}</span>
          )}
        </div>
        <div className="flex items-center gap-8">
          <div className="relative group hidden lg:block">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-500 text-sm">search</span>
            <input className="clay-panel clay-interactive border-none rounded-full py-1.5 pl-10 pr-4 text-[10px] w-56 focus:ring-1 focus:ring-primary/40 transition-all font-bold tracking-wider" placeholder="SCAN DATABASE..." type="text"/>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-10 h-full max-w-[1600px] mx-auto">
        {/* Left: Scenario Controls */}
        <section className="col-span-12 xl:col-span-3 flex flex-col gap-8">
          <div className="clay-panel clay-interactive rounded-3xl p-8 ambient-glow-primary ">
            <div className="flex items-center justify-between mb-8">
              <h2 className="font-headline text-[10px] font-extrabold uppercase tracking-[0.2em] text-primary">Parameters</h2>
              <span className="w-1.5 h-1.5 rounded-full bg-primary/30"></span>
            </div>
            <div className="space-y-10">
              <div className="space-y-5">
                <label className="text-[10px] font-bold tracking-widest text-slate-500 flex items-center justify-between uppercase">
                  Grid Units <span className="text-primary font-mono">{gridUnits} / 20</span>
                </label>
                <div className="flex gap-3">
                  <button onClick={() => setGridUnits(v => Math.min(20, v+1))} className="flex-1 clay-panel clay-interactive hover:bg-[#2a3440] py-4 rounded-2xl flex flex-col items-center gap-2 transition-all ">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center"><span className="material-symbols-outlined">add</span></div>
                    <span className="text-[9px] font-bold tracking-widest uppercase text-slate-400">Deploy</span>
                  </button>
                  <button onClick={() => setGridUnits(v => Math.max(1, v-1))} className="flex-1 clay-panel clay-interactive hover:bg-[#2a3440] py-4 rounded-2xl flex flex-col items-center gap-2 transition-all ">
                    <div className="w-8 h-8 rounded-full bg-slate-500/10 flex items-center justify-center"><span className="material-symbols-outlined">remove</span></div>
                    <span className="text-[9px] font-bold tracking-widest uppercase text-slate-400">Recall</span>
                  </button>
                </div>
              </div>
              <div className="space-y-5">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Sweep Frequency</label>
                  <span className="text-[10px] font-mono font-bold text-secondary uppercase">Bi-Weekly</span>
                </div>
                <div className="relative flex items-center">
                  <input className="w-full h-1.5 clay-panel clay-interactive rounded-full appearance-none cursor-pointer accent-primary" type="range"/>
                </div>
              </div>
              <div className="space-y-5">
                <label className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Aerial Priority</label>
                <div className="flex items-center p-1 bg-[#0f1419] rounded-2xl ">
                  <button className="flex-1 py-2.5 text-[9px] font-bold tracking-widest rounded-lg bg-primary text-on-primary shadow-lg transition-all uppercase">High</button>
                  <button className="flex-1 py-2.5 text-[9px] font-bold tracking-widest text-slate-500 uppercase hover:text-slate-300 transition-colors">Mid</button>
                  <button className="flex-1 py-2.5 text-[9px] font-bold tracking-widest text-slate-500 uppercase hover:text-slate-300 transition-colors">Low</button>
                </div>
              </div>
              <button onClick={handleRun} disabled={running} className="w-full py-5 mt-4 bg-gradient-to-r from-[#ffab40] to-[#ffd09f] text-[#2b1700] font-headline font-extrabold text-[11px] tracking-[0.2em] rounded-2xl shadow-[0_10px_30px_-10px_rgba(255,171,64,0.3)] hover:brightness-105 active:scale-[0.98] transition-all flex items-center justify-center gap-3 uppercase disabled:opacity-60">
                <span className="material-symbols-outlined">bolt</span>
                {running ? "Running..." : "Initiate Sequence"}
              </button>
            </div>
          </div>

          <div className="clay-panel clay-interactive rounded-3xl p-8 ">
            <h3 className="text-[9px] font-extrabold uppercase tracking-[0.2em] text-slate-500 mb-6 flex items-center gap-2">
              <span className="w-1 h-1 rounded-full bg-slate-500"></span> Baselines
            </h3>
            <div className="space-y-4">
              {(d?.scenarios ?? []).slice(0,2).map((s, i) => {
                const sc = s as Record<string,unknown>;
                return (
                  <div key={i} className="flex justify-between items-center py-2.5 border-b border-white/5">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{String(sc.scenario_name ?? `Scenario ${i+1}`)}</span>
                    <span className="text-[10px] font-mono text-primary">{String(sc.risk_reduction_pct ?? "—")}% red.</span>
                  </div>
                );
              }) ?? (
                <>
                  <div className="flex justify-between items-center py-2.5 border-b border-white/5"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">2023 Cycles</span><span className="text-[10px] font-mono text-primary">1.2k pts</span></div>
                  <div className="flex justify-between items-center py-2.5 border-b border-white/5"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resp. Delay</span><span className="text-[10px] font-mono text-primary">14.2m</span></div>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Center: Results Visualization */}
        <section className="col-span-12 xl:col-span-6 flex flex-col gap-10">
          <div className="flex-1 relative clay-panel clay-interactive rounded-3xl overflow-hidden min-h-[500px] shadow-2xl">
            <div className="absolute inset-0 opacity-50">
              <img alt="Fire Risk Visualization Map" className="w-full h-full object-cover grayscale brightness-75 contrast-125" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBodH4re_DIKLBBeEN-wMYbaxzaHd3zdmZfGvt3Vqt3TDkGXBYOHisVd8v5EkuAvIgl7Y-lAcf9zbg_Xju-z33DfH_5pcTkoPP4_gkVWMc9XZOvgertODK6cFe55490vRxifA81C5lMOA_CH_eD94WxcELKA1hCrsPFrEZQug-jaJWc-2-I0pIVZL0p38euqu4Gw5dm00Yz2DhuRWoM-qRCgoJ8ak9QeiPYthpPUDH1DgzfpiRNEgczxLPpVCE1R7jUKCPH_OPVLmo"/>
            </div>
            <div className="absolute top-8 left-8 flex gap-5">
              <div className="glass-panel p-5 rounded-3xl border border-white/10 flex flex-col items-center">
                <div className="text-[9px] font-extrabold text-slate-500 uppercase tracking-[0.2em] mb-2">Delta</div>
                <div className="text-2xl font-headline font-bold text-secondary">{riskReductionLabel}</div>
                <div className="w-1 h-1 rounded-full bg-secondary mt-2"></div>
              </div>
              <div className="glass-panel p-5 rounded-3xl border border-white/10 flex flex-col items-center">
                <div className="text-[9px] font-extrabold text-slate-500 uppercase tracking-[0.2em] mb-2">Net Benefit</div>
                <div className="text-2xl font-headline font-bold text-primary">{netBenefit}</div>
                <div className="w-1 h-1 rounded-full bg-primary mt-2"></div>
              </div>
            </div>
            <div className="absolute bottom-8 right-8 glass-panel py-4 px-6 rounded-3xl border border-white/10">
              <div className="flex items-center gap-4 mb-2">
                <span className="dot-marker animate-pulse"></span>
                <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-on-surface">Sequence {running ? "Running" : "Live"}</span>
              </div>
              <div className="text-[9px] font-bold text-slate-500 tracking-widest uppercase">Iter: {iterCurrent.toLocaleString()} / {iterTotal.toLocaleString()}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            <div className="clay-panel clay-interactive rounded-3xl p-8 relative overflow-hidden">
              <div className="flex justify-between items-center mb-6">
                <h4 className="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">Predictive Spread</h4>
                <Sparkles size={20} className="text-primary text-sm" />
              </div>
              <div className="h-28 flex items-end gap-3">
                {spreadBars.map((bar, i) => {
                  const h = Math.round(bar.value * 100);
                  const isHighest = bar.value >= 0.9;
                  return (
                    <div key={i} title={bar.label}
                      className={`flex-1 rounded-full transition-all ${isHighest ? "bg-primary shadow-[0_0_20px_rgba(255,208,159,0.3)]" : i === spreadBars.length - 2 && bar.value >= 0.75 ? "bg-primary/40 border-t-2 border-primary shadow-[0_0_15px_rgba(255,208,159,0.2)]" : "clay-panel clay-interactive hover:bg-surface-container-highest"}`}
                      style={{height: `${Math.max(h, 10)}%`}}
                    />
                  );
                })}
              </div>
            </div>

            <div className="clay-panel clay-interactive rounded-3xl p-8 ">
              <div className="flex justify-between items-center mb-6">
                <h4 className="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">Efficiency</h4>
                <Target size={20} className="text-secondary text-sm" />
              </div>
              <div className="flex items-center justify-center h-28">
                <div className="relative w-24 h-24">
                  <svg className="w-full h-full -rotate-90">
                    <circle className="text-[#1f2730]" cx="48" cy="48" fill="transparent" r="40" stroke="currentColor" strokeWidth={6}></circle>
                    <circle className="text-secondary" cx="48" cy="48" fill="transparent" r="40" stroke="currentColor" strokeDasharray={circumference} strokeDashoffset={dashOffset} strokeLinecap="round" strokeWidth={6}></circle>
                  </svg>
                  <span className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-sm font-headline font-bold">{efficiencyPct.toFixed(0)}%</span>
                    <span className="w-1 h-1 rounded-full bg-secondary mt-1"></span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Right: Sentinel Core AI Panel */}
        <section className="col-span-12 xl:col-span-3 flex flex-col h-full">
          <div className="flex-1 clay-panel clay-interactive rounded-3xl flex flex-col relative overflow-hidden">
            <div className="absolute inset-x-0 bottom-32 h-[1px] bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
            <div className="p-8 border-b border-white/5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-3xl bg-primary/10 flex items-center justify-center border border-primary/20">
                  <span className="material-symbols-outlined">psychology</span>
                </div>
                <div>
                  <h3 className="text-xs font-headline font-extrabold uppercase tracking-widest">Sentinel Core</h3>
                  <div className="text-[9px] text-secondary flex items-center gap-1.5 uppercase font-extrabold tracking-[0.2em] mt-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-secondary shadow-[0_0_8px_#71d7cd]"></span>
                    Synchronized
                  </div>
                </div>
              </div>
            </div>
            <div className="flex-1 p-8 space-y-8 overflow-y-auto">
              <div className="space-y-3">
                <div className="text-[9px] font-extrabold text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
                  <span className="w-1 h-1 rounded-full bg-slate-500/50"></span> Inquiry Trace
                </div>
                <p className="text-[11px] text-slate-400 font-medium leading-relaxed italic">"Simulate Northeast re-deployment during Grade 3 humidity shifts."</p>
              </div>
              <div className="bg-[#0f1419] p-6 rounded-3xl border-l-4 border-primary space-y-4 relative overflow-hidden">
                <div className="absolute top-4 right-4 w-1.5 h-1.5 rounded-full bg-primary/20"></div>
                <div className="text-[9px] font-extrabold text-primary uppercase tracking-[0.2em]">Neural Output</div>
                <p className="text-[11px] text-slate-300 leading-relaxed">
                  {sentinelBrief.split("\n\n").map((para, i) => (
                    <React.Fragment key={i}>{i > 0 && <><br/><br/></>}{para}</React.Fragment>
                  ))}
                </p>
              </div>
              <div className="space-y-5">
                <div className="text-[9px] font-extrabold text-slate-500 uppercase tracking-[0.2em]">Pattern Scans</div>
                <div className="flex flex-wrap gap-2.5">
                  <button className="text-[9px] font-bold uppercase tracking-widest clay-panel clay-interactive hover:bg-primary/20 hover:text-primary px-4 py-2 rounded-lg transition-all">Bottlenecks</button>
                  <button className="text-[9px] font-bold uppercase tracking-widest clay-panel clay-interactive hover:bg-primary/20 hover:text-primary px-4 py-2 rounded-lg transition-all">Weather Scan</button>
                  <button className="text-[9px] font-bold uppercase tracking-widest clay-panel clay-interactive hover:bg-primary/20 hover:text-primary px-4 py-2 rounded-lg transition-all">Flow Map</button>
                </div>
              </div>
            </div>
            <div className="p-8 mt-auto bg-[#0f1419]/50">
              <div className="relative group">
                <textarea className="w-full clay-panel clay-interactive border-white/5 rounded-3xl p-5 text-[11px] font-medium resize-none focus:ring-1 focus:ring-primary/40 focus:bg-[#252d38] placeholder:text-slate-600 transition-all leading-relaxed" placeholder="ENGAGE SENTINEL CORE..." rows={3}></textarea>
                <button className="absolute bottom-4 right-4 w-10 h-10 bg-primary text-[#2b1700] rounded-2xl hover:scale-105 active:scale-95 transition-all flex items-center justify-center shadow-lg">
                  <span className="material-symbols-outlined">east</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
'''

# ============================================================
# Risk & Compliance
# ============================================================
COMP = r'''"use client";
import React from "react";
import { ShieldCheck, FileCheck, Scale, AlertOctagon, Download } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { api, type Envelope, type ComplianceData } from "@/lib/api";

export default function RiskCompliance() {
  const { data, loading: _loading, error, refresh } = useDashboard<Envelope<ComplianceData>>({
    fetcher: api.compliance, intervalMs: 5000,
  });
  useLiveSocket((e) => { if (e.type === "snapshot_updated" || e.type === "report_ready") refresh(); });

  const d = data?.data;
  const violations = d?.policy_violations_30d ?? 0;
  const compRate = d?.compliance_rate ?? 82.3;
  const offenders = d?.repeat_offenders ?? [];
  const kpis = d?.kpis ?? [];
  const frameworks = d?.frameworks ?? [
    { name: "ISO 31000 Standard", status: "compliant" },
    { name: "OSHA Sect. 5(a)", status: "compliant" },
  ];

  return (
    <div className="flex flex-col gap-8 pb-12 w-full animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight text-white mb-2" style={{ fontFamily: "var(--font-manrope)" }}>Risk &amp; Compliance</h1>
          <p className="text-[#dee3ea]/60 text-sm max-w-xl">Auditing, legal frameworks, and ongoing risk assessment protocols.</p>
        </div>
        <div className="flex items-center gap-3">
          <a href={api.reportCsv()} download className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#534435]/30 text-xs font-bold tracking-widest text-[#d8c3b0] hover:bg-[#534435]/10 hover:text-white transition-all">
            <Download size={14} /> CSV
          </a>
          <a href={api.reportPdf()} download className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#534435]/30 text-xs font-bold tracking-widest text-[#d8c3b0] hover:bg-[#534435]/10 hover:text-white transition-all">
            <Download size={14} /> PDF
          </a>
        </div>
      </header>

      {error && (
        <div className="px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error">Backend unavailable &mdash; demo data.</div>
      )}

      {kpis.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {kpis.map((kpi, i) => (
            <div key={i} className="clay-panel clay-interactive rounded-2xl p-5">
              <p className="text-[10px] font-bold text-[#d8c3b0] tracking-[0.15em] uppercase mb-2">{kpi.label}</p>
              <p className="text-2xl font-semibold text-white">{kpi.value}</p>
              <span className={`text-[10px] font-bold uppercase tracking-wider ${kpi.status === "stable" ? "text-[#71d7cd]" : "text-[#ffb4ab]"}`}>{kpi.status}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6 w-full">
        <div className="col-span-12 lg:col-span-8 clay-panel clay-interactive rounded-3xl min-h-[500px] flex flex-col p-6 relative overflow-hidden group">
          <h3 className="text-[10px] font-bold text-[#d8c3b0] tracking-[0.15em] uppercase mb-6">
            Compliance Matrix Logs {offenders.length > 0 ? `— ${offenders.length} repeat offenders` : ""}
          </h3>
          {offenders.length === 0 ? (
            <div className="w-full flex-1 rounded-[12px] bg-[#0a0f14] p-6 flex flex-col items-center justify-center relative">
              <ShieldCheck size={48} className="text-[#534435]/60 mb-6" strokeWidth={1} />
              <p className="text-[#d8c3b0] text-sm text-center max-w-md">All regional compliances verified. No repeat offenders on record.</p>
              <button className="mt-8 px-6 py-2 rounded-lg border border-[#534435]/30 text-xs font-bold tracking-widest text-[#d8c3b0] flex items-center gap-2 hover:bg-[#534435]/10 hover:text-white transition-all">
                <FileCheck size={16} /> GENERATE REPORT
              </button>
            </div>
          ) : (
            <div className="flex-1 rounded-[12px] bg-[#0a0f14] overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left py-3 px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Address</th>
                    <th className="text-left py-3 px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Violations</th>
                    <th className="text-left py-3 px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Priority</th>
                    <th className="text-left py-3 px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {offenders.map((o, i) => {
                    const off = o as Record<string,unknown>;
                    const pri = Number(off.enforcement_priority ?? 0);
                    return (
                      <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td className="py-3 px-4 text-[#d8c3b0] font-medium">{String(off.address ?? "—")}</td>
                        <td className="py-3 px-4"><span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${pri >= 4 ? "bg-[#ffb4ab]/20 text-[#ffb4ab]" : pri >= 3 ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"}`}>{String(off.violation_count ?? 0)}</span></td>
                        <td className="py-3 px-4 text-slate-400">{pri >= 4 ? "CRITICAL" : pri >= 3 ? "HIGH" : "MEDIUM"}</td>
                        <td className="py-3 px-4 text-slate-400">{String(off.enforcement_action ?? "—")}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
          <div className="clay-panel clay-interactive rounded-3xl p-6 flex flex-col pt-8 border-l-4 border-[#ffb4ab]">
            <h3 className="text-[10px] font-bold text-[#ffb4ab] mb-4 tracking-[0.15em] uppercase">Policy Violations</h3>
            <div className="flex items-center justify-between">
              <AlertOctagon className="text-[#ffb4ab]/80" size={32} strokeWidth={1.5} />
              <div className="text-right">
                <p className="text-[32px] font-semibold text-[#ffb4ab]" style={{ fontFamily: "var(--font-manrope)" }}>{violations}</p>
                <p className="text-[11px] font-bold text-[#ffb4ab]/80 tracking-wider uppercase mt-1">LAST 30 DAYS</p>
              </div>
            </div>
          </div>

          <div className="clay-panel clay-interactive rounded-3xl p-6 flex flex-col flex-1 relative overflow-hidden group hover:border-[#ffd09f]/30 transition-colors">
            <div className="absolute -right-10 -top-10 w-40 h-40 bg-[#ffd09f]/5 rounded-full blur-[40px] pointer-events-none group-hover:bg-[#ffd09f]/10 transition-colors" />
            <h3 className="text-[10px] font-bold text-[#d8c3b0] mb-6 tracking-[0.15em] uppercase">Regulatory Framework</h3>
            <div className="flex flex-col gap-4">
              {frameworks.map((fw, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[#0a0f14] ">
                  <div className="flex items-center gap-3">
                    <Scale size={16} className="text-[#71d7cd]" />
                    <span className="text-sm text-white">{fw.name}</span>
                  </div>
                  <span className={`w-2 h-2 rounded-full ${fw.status === "compliant" ? "bg-[#71d7cd] shadow-[0_0_8px_#71d7cd]" : "bg-[#ffb4ab]"}`}></span>
                </div>
              ))}
            </div>
            <div className="mt-6 pt-6 border-t border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500 uppercase tracking-widest">Compliance Rate</span>
                <span className="text-lg font-bold text-[#71d7cd]">{compRate.toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-surface-container-low rounded-full mt-2 overflow-hidden">
                <div className="h-full bg-[#71d7cd] rounded-full" style={{width: `${compRate}%`}}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
'''

files = {
    os.path.join(BASE, "command-center", "page.tsx"): CC,
    os.path.join(BASE, "operations", "page.tsx"): OPS,
    os.path.join(BASE, "simulation-ai", "page.tsx"): SIM,
    os.path.join(BASE, "risk-compliance", "page.tsx"): COMP,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path}")

print("All done!")
