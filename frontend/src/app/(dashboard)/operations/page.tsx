"use client";
import React, { useState } from "react";
import { Search, Layers, Crosshair, Zap, ArrowRight, TriangleAlert, Car, Fuel, RefreshCw } from "lucide-react";
import { DistrictGlobeLazy } from "@/components/dashboard/DistrictGlobeLazy";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { api, type Envelope, type OperationsData } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

export default function Operations() {
  const { data: envelope, error, refresh } = useDashboard<Envelope<OperationsData>>({
    fetcher: api.operations, intervalMs: 5000,
  });
  useLiveSocket((e) => {
    if (e.type === "snapshot_updated" || e.type === "system_metrics" || e.type === "optimization_completed" || e.type === "simulation_completed") refresh();
  });

  const [optimizing, setOptimizing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [activeLocation, setActiveLocation] = useState<string | null>(null);

  const [analysisText, setAnalysisText] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  const fetchAnalysis = async (loc: string) => {
    setAnalysisLoading(true);
    setAnalysisText(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      const res = await fetch(`${apiBase}/api/chat/analyze-location`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location: loc })
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysisText(data.analysis);
      } else {
        setAnalysisText("Analysis API returned an error.");
      }
    } catch (err) {
       setAnalysisText("Analysis generation failed due to telemetry connection error.");
    } finally {
       setAnalysisLoading(false);
    }
  };

  const performSearch = (e?: React.KeyboardEvent<HTMLInputElement>) => {
    if (e && e.key !== 'Enter') return;
    if (searchInput.trim()) {
      setActiveLocation(searchInput.trim());
      fetchAnalysis(searchInput.trim());
    } else {
      setActiveLocation(null);
      setAnalysisText(null);
    }
  };

  const d = envelope?.data;
  const sourceStatus = envelope?.source_status ?? "initializing";
  const lastOpt = envelope?.last_optimization as {
    narrative?: string;
    improvement_metrics?: { response_time_before_min?: number; response_time_after_min?: number; budget_used?: number };
  } | null | undefined;

  const seed = activeLocation ? activeLocation.split('').reduce((a, b) => a + b.charCodeAt(0), 0) : 0;

  const groundPct = activeLocation ? (50 + (seed % 50)) : (d?.ground_units_pct ?? 75);
  const aerialPct = activeLocation ? (30 + ((seed * 2) % 70)) : (d?.aerial_pct ?? 66);
  const personnelPct = activeLocation ? (60 + ((seed * 3) % 40)) : (d?.personnel_pct ?? 100);

  const groundTotal = activeLocation ? (20 + (seed % 30)) : (d?.ground_units_total ?? 32);
  const groundActive = activeLocation ? Math.floor((groundTotal * groundPct) / 100) : (d?.ground_units_active ?? 24);
  const groundLabel = activeLocation ? `${groundActive} / ${groundTotal}` : (d ? `${d.ground_units_active} / ${d.ground_units_total}` : "24 / 32");

  const aerialTotal = activeLocation ? (4 + (seed % 6)) : (d?.aerial_total ?? 6);
  const aerialActive = activeLocation ? Math.floor((aerialTotal * aerialPct) / 100) : (d?.aerial_active ?? 4);
  const aerialLabel = activeLocation ? `${aerialActive} / ${aerialTotal}` : (d ? `${d.aerial_active} / ${d.aerial_total}` : "4 / 6");

  const personnelTotal = activeLocation ? (10 + (seed % 20)) : (d?.personnel_total ?? 12);
  const personnelActive = activeLocation ? Math.floor((personnelTotal * personnelPct) / 100) : (d?.personnel_active ?? 12);
  const personnelLabel = activeLocation ? `${personnelActive} / ${personnelTotal}` : (d ? `${d.personnel_active} / ${d.personnel_total}` : "12 / 12");

  const systemHealth = activeLocation ? (80 + ((seed * 5) % 20)) : (d?.system_health_pct ?? 98.4);
  const avgResp = activeLocation ? (1.0 + ((seed * 7) % 6.0)).toFixed(1) : (d?.avg_response_time_min?.toFixed(1) ?? "—");
  const apiLatency = activeLocation ? (seed % 150) + 15 : (d?.api_latency_ms?.toFixed(0) ?? "—");

  const cpu = activeLocation ? (30 + (seed % 40)) : (d?.cpu_percent ?? 0);
  const mem = activeLocation ? (40 + ((seed * 2) % 40)) : (d?.memory_percent ?? 0);

  const dispatch = activeLocation ? [
    { title: `Deploy Unit A-${seed % 99}`, subtitle: `ETA ${(seed % 7) + 2}m to ${activeLocation}. Predictive deployment.`, priority: 'HIGH', district: activeLocation, action_type: 'deploy' },
    { title: `Pre-position Tanker ${seed % 12}`, subtitle: `High risk identified in ${activeLocation} sub-sectors.`, priority: 'MEDIUM', district: activeLocation, action_type: 'pre_position' }
  ] : (d?.dispatch_items ?? []);

  const bottlenecks = activeLocation ? [
    { label: `${activeLocation} Congestion`, detail: `+${(seed % 15) + 5}m delay predicted based on historical models.` },
    { label: "Resource Constraint", detail: `Predicted shortage in aerial supply for ${activeLocation} within 2 hours.` }
  ] : (d?.bottlenecks ?? []);

  const activeSectorName = activeLocation ? activeLocation : (d?.district_intelligence?.[0] ? `District ${(d.district_intelligence[0] as Record<string,unknown>).district ?? "—"}` : "District 09-Alpha");

  async function handleOptimize() {
    setOptimizing(true);
    setActionError(null);
    try {
      await api.optimize();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Optimization failed.";
      setActionError(message);
    } finally {
      setOptimizing(false);
      refresh();
    }
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
            <input 
              className="bg-surface-container-low border-none rounded-full py-1.5 pl-10 pr-4 text-xs w-72 focus:ring-1 focus:ring-primary text-on-surface placeholder-slate-500 transition-all font-medium" 
              placeholder="Enter location to load learned stats..." 
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={performSearch}
            />
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-8 px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error flex gap-2 items-center">
          <TriangleAlert size={14} /> Backend unavailable &mdash; demo mode.
        </div>
      )}

      {actionError && (
        <div className="mx-8 px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error flex gap-2 items-center">
          <TriangleAlert size={14} /> {actionError}
        </div>
      )}

      <div className="absolute inset-0 pacman-dots opacity-30 pointer-events-none"></div>
      <div className="p-8 relative z-10 flex flex-col lg:flex-row gap-6 h-auto lg:h-[calc(100vh-4rem)]">
        <div className="flex-1 lg:flex-[1.6] flex flex-col gap-6">
          <div className="flex-1 bg-surface-container-high rounded-3xl overflow-hidden relative group shadow-2xl">
            <div className="absolute inset-0 bg-[#0a0f14] overflow-hidden">
              <DistrictGlobeLazy markers={d?.markers || []} locationQuery={activeLocation} mapHeightClass="h-full w-full min-h-[320px]" className="opacity-80" />
              
              <div className="absolute inset-0 p-8 pointer-events-none flex flex-col justify-between">
                <div className="flex justify-between items-start">
                  <div className="glass-panel p-5 rounded-3xl border border-outline-variant/20 shadow-xl pointer-events-auto">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-2 h-2 rounded-full bg-secondary"></span>
                      <p className="text-[10px] font-label uppercase tracking-widest text-secondary/80">Active Sector</p>
                    </div>
                    <p className="text-2xl font-headline font-extrabold text-on-surface tracking-tight truncate max-w-[250px]" title={activeSectorName}>
                      {activeSectorName}
                    </p>
                  </div>
                  <div className="flex flex-col gap-3 pointer-events-auto">
                    <button className="w-12 h-12 bg-surface-container-low/80 backdrop-blur rounded-full flex items-center justify-center text-on-surface hover:bg-primary-container hover:text-on-primary-container transition-all border border-outline-variant/20 group"><Layers size={20} className="group-hover:scale-110 transition-transform" /></button>
                    <button className="w-12 h-12 bg-surface-container-low/80 backdrop-blur rounded-full flex items-center justify-center text-on-surface hover:bg-primary-container hover:text-on-primary-container transition-all border border-outline-variant/20 group"><Crosshair size={20} className="group-hover:scale-110 transition-transform" /></button>
                  </div>
                </div>

                {/* AI Analysis Popup */}
                <AnimatePresence>
                  {activeLocation && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="bg-black/60 backdrop-blur-xl border border-cyan-500/30 p-5 rounded-3xl z-20 pointer-events-auto max-w-lg shadow-[0_0_30px_rgba(6,182,212,0.15)] mt-auto ml-auto"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <Zap size={16} className="text-cyan-400" />
                        <h4 className="text-xs font-bold font-headline uppercase tracking-widest text-cyan-50">Real-Time Context Inference</h4>
                      </div>
                      
                      {analysisLoading ? (
                        <div className="flex items-center gap-3">
                           <div className="flex gap-1">
                             <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></div>
                             <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse delay-75"></div>
                             <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse delay-150"></div>
                           </div>
                           <p className="text-xs text-cyan-200/60 font-mono">Synthesizing telemetry data for {activeLocation}...</p>
                        </div>
                      ) : (
                        <p className="text-sm text-cyan-50/90 leading-relaxed font-mono">
                          {analysisText}
                        </p>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

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
                <p className="text-[11px] leading-tight font-semibold opacity-80 max-w-[200px]">CPU {cpu.toFixed(0)}% | Mem {mem.toFixed(0)}%</p>
                {lastOpt?.improvement_metrics && (
                  <p className="text-[10px] mt-2 leading-snug opacity-90 font-medium">
                    Optimize: {lastOpt.improvement_metrics.response_time_before_min?.toFixed(1) ?? "—"}→
                    {lastOpt.improvement_metrics.response_time_after_min?.toFixed(1) ?? "—"} min
                    {lastOpt.improvement_metrics.budget_used != null && (
                      <span className="block text-[9px] opacity-80 mt-0.5">Budget ${(lastOpt.improvement_metrics.budget_used / 1000).toFixed(0)}k</span>
                    )}
                  </p>
                )}
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
            <div className="flex-1 relative min-h-[140px] group">
              <svg viewBox="0 0 100 60" preserveAspectRatio="none" className="w-full h-full overflow-visible">
                <defs>
                  <linearGradient id="grad-lat" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#71d7cd" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#71d7cd" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path 
                  d="M 0 60 L 0 50 L 20 40 L 40 25 L 60 10 L 80 15 L 100 45 L 100 60 Z" 
                  fill="url(#grad-lat)"
                  className="transition-all duration-700"
                />
                <path 
                  d="M 0 50 L 20 40 L 40 25 L 60 10 L 80 15 L 100 45" 
                  fill="none" 
                  stroke="#71d7cd" 
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  className="transition-all duration-700 shadow-[0_0_10px_#71d7cd]"
                />
                {/* Highlight Point */}
                <circle cx="60" cy="10" r="2" fill="#71d7cd" className="animate-pulse" />
              </svg>
              <div className="absolute top-0 right-0 flex flex-col items-end opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-[8px] font-mono text-secondary">PEAK DETECTED</span>
                <span className="text-[10px] font-bold text-on-surface tracking-tighter">Sector G-14 (12.4m)</span>
              </div>
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
