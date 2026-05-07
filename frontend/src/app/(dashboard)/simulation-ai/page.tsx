"use client";
import React, { useState } from "react";
import { Sparkles, Target } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { api, type Envelope, type SimulationData } from "@/lib/api";
import { DistrictGlobeLazy } from "@/components/dashboard/DistrictGlobeLazy";

export default function SimulationAI() {
  const { data: envelope, error, refresh } = useDashboard<Envelope<SimulationData>>({
    fetcher: api.simulation, intervalMs: 5000,
  });
  useLiveSocket((e) => { if (e.type === "snapshot_updated" || e.type === "simulation_completed") refresh(); });

  const [running, setRunning] = useState(false);
  const [gridUnits, setGridUnits] = useState(14);
  const [actionError, setActionError] = useState<string | null>(null);

  const [inquiryText, setInquiryText] = useState("Simulate Northeast re-deployment during Grade 3 humidity shifts.");
  const [neuralOutput, setNeuralOutput] = useState<string | null>(null);
  const [sentinelInput, setSentinelInput] = useState("");
  const [isSentinelThinking, setIsSentinelThinking] = useState(false);

  const d = envelope?.data;
  const sourceStatus = envelope?.source_status ?? "initializing";
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
    setActionError(null);
    try {
      await api.runSimulation({ grid_units: gridUnits });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Simulation run failed.";
      setActionError(message);
    } finally {
      setRunning(false);
      refresh();
    }
  }

  const displayOutput = neuralOutput || sentinelBrief;

  const handleSentinelSubmit = async (overrideQuery?: string | any) => {
    // Ensure we don't accidentally treat a React event as a query string
    const queryStr = (typeof overrideQuery === "string") ? overrideQuery : sentinelInput.trim();
    
    if (!queryStr || isSentinelThinking) return;
    if (typeof overrideQuery !== "string") setSentinelInput("");
    
    setInquiryText(queryStr);
    setIsSentinelThinking(true);
    setNeuralOutput(null); 
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      const response = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{role: "user", content: `As the Sentinel Core AI, analyze this simulation parameter shift and provide tactical insight based on current telemetry: ${queryStr}`}],
          page_context: "/simulation-ai"
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setNeuralOutput(data.reply);
      } else {
         setNeuralOutput("ERROR: Connection to Sentinel Core failed.");
      }
    } catch (e) {
      setNeuralOutput("ERROR: Inquiry failed (telemetry offline).");
    } finally {
      setIsSentinelThinking(false);
    }
  };

  const triggerAnalysis = async (type: "Bottlenecks" | "Weather Scan" | "Flow Map") => {
    if (isSentinelThinking) return;
    
    let query = "";
    switch (type) {
      case "Bottlenecks": 
        query = "Identify critical resource bottlenecks in the Northeast corridor given current unit deployment.";
        break;
      case "Weather Scan":
        query = "Analyze simulated impact of humidity drops below 20% on containment success rates.";
        break;
      case "Flow Map":
        query = "Generate tactical movement optimizations for Alpha-7 units to minimize response delay.";
        break;
    }

    setSentinelInput(query);
    // Use a small timeout to let the state update reflect in UI before submitting
    setTimeout(() => handleSentinelSubmit(query), 100);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSentinelSubmit();
    }
  };

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

      {error !== null && (
        <div className="mx-8 px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error">
          Simulation feed unavailable — retrying.
        </div>
      )}

      {actionError && (
        <div className="mx-8 px-6 py-3 bg-error/10 border border-error/20 rounded-2xl text-xs text-error">
          {actionError}
        </div>
      )}

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
              {(d?.scenarios ?? []).slice(0, 2).length > 0 ? (
                (d?.scenarios ?? []).slice(0, 2).map((s, i) => {
                  const sc = s as Record<string, unknown>;
                  return (
                    <div key={i} className="flex justify-between items-center py-2.5 border-b border-white/5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{String(sc.scenario_name ?? `Scenario ${i + 1}`)}</span>
                      <span className="text-[10px] font-mono text-primary">{String(sc.risk_reduction_pct ?? "—")}% red.</span>
                    </div>
                  );
                })
              ) : (
                <>
                  <div className="flex justify-between items-center py-2.5 border-b border-white/5"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">2023 Cycles</span><span className="text-[10px] font-mono text-primary">1.2k pts</span></div>
                  <div className="flex justify-between items-center py-2.5 border-b border-white/5"><span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resp. Delay</span><span className="text-[10px] font-mono text-primary">14.2m</span></div>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Center: map, charts, Sentinel Core (below spread + efficiency) */}
        <section className="col-span-12 xl:col-span-9 flex flex-col gap-10">
          <div className="flex-1 relative clay-panel clay-interactive rounded-3xl overflow-hidden min-h-[500px] shadow-2xl">
            <div className="absolute inset-0 opacity-80">
              <DistrictGlobeLazy markers={(d as any)?.markers ?? []} mapHeightClass="h-full w-full" />
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
            <div className="clay-panel clay-interactive rounded-3xl p-8 relative overflow-hidden group">
              <div className="flex justify-between items-center mb-6">
                <h4 className="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">Predictive Spread</h4>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-mono text-primary animate-pulse">TREND ANALYZE</span>
                  <Sparkles size={16} className="text-primary" />
                </div>
              </div>
              
              <div className="h-32 relative">
                {/* SVG Graph for Inference */}
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full overflow-visible">
                  <defs>
                    <linearGradient id="gradient-risk" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ffab40" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#ffab40" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  
                  {/* Area */}
                  <path 
                    d={`M 0 100 ${spreadBars.map((bar, i) => `L ${i * (100 / (spreadBars.length - 1))} ${100 - (bar.value * 80)}`).join(" ")} L 100 100 Z`}
                    fill="url(#gradient-risk)"
                    className="transition-all duration-700"
                  />
                  
                  {/* Line */}
                  <path 
                    d={spreadBars.map((bar, i) => `${i === 0 ? "M" : "L"} ${i * (100 / (spreadBars.length - 1))} ${100 - (bar.value * 80)}`).join(" ")}
                    fill="none"
                    stroke="#ffab40"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="transition-all duration-700 shadow-[0_0_15px_rgba(255,171,64,0.5)]"
                  />

                  {/* Nodes */}
                  {spreadBars.map((bar, i) => (
                    <circle 
                      key={i}
                      cx={i * (100 / (spreadBars.length - 1))}
                      cy={100 - (bar.value * 80)}
                      r="1.5"
                      fill="#ffab40"
                      className="transition-all duration-300 hover:r-[3] cursor-pointer"
                    >
                      <title>{`${bar.label}: ${Math.round(bar.value * 100)}%`}</title>
                    </circle>
                  ))}
                </svg>

                {/* X-Axis Labels */}
                <div className="absolute -bottom-6 left-0 right-0 flex justify-between px-1">
                  {spreadBars.map((bar, i) => (
                    <span key={i} className="text-[8px] font-mono text-slate-500 uppercase">{bar.label}</span>
                  ))}
                </div>
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

          <div className={`clay-panel clay-interactive rounded-3xl flex flex-col relative overflow-hidden transition-all duration-700 ${isSentinelThinking ? 'ring-2 ring-primary/40 shadow-[0_0_50px_rgba(255,171,64,0.15)]' : ''}`}>
            <div className="absolute inset-x-0 bottom-32 h-[1px] bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
            <div className="p-8 border-b border-white/5">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-3xl flex items-center justify-center border transition-all duration-500 ${isSentinelThinking ? 'bg-primary/20 border-primary animate-pulse' : 'bg-primary/10 border-primary/20'}`}>
                  <span className={`material-symbols-outlined ${isSentinelThinking ? 'text-primary' : ''}`}>psychology</span>
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
                <p className="text-[11px] text-slate-400 font-medium leading-relaxed italic">
                  &ldquo;{inquiryText}&rdquo;
                </p>
              </div>
              <div className="bg-[#0f1419] p-6 rounded-3xl border-l-4 border-primary space-y-4 relative overflow-hidden">
                <div className="absolute top-4 right-4 w-1.5 h-1.5 rounded-full bg-primary/20"></div>
                <div className="text-[9px] font-extrabold text-primary uppercase tracking-[0.2em]">Neural Output</div>
                <p className="text-[11px] text-slate-300 leading-relaxed font-mono">
                  {isSentinelThinking && !neuralOutput ? (
                     <span className="flex items-center gap-2 text-primary/60">
                       <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></span>
                       <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse delay-75"></span>
                       <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse delay-150"></span>
                       Processing neural architecture...
                     </span>
                  ) : (
                    displayOutput.split("\n\n").map((para, i) => (
                      <React.Fragment key={i}>{i > 0 && <><br/><br/></>}{para}</React.Fragment>
                    ))
                  )}
                </p>
              </div>

              {/* Inference HUD */}
              <div className="grid grid-cols-3 gap-4">
                <div className="clay-panel p-4 rounded-2xl flex flex-col items-center">
                  <div className="text-[8px] text-slate-500 uppercase tracking-widest mb-1">Confidence</div>
                  <div className="text-sm font-mono text-secondary">94.2%</div>
                </div>
                <div className="clay-panel p-4 rounded-2xl flex flex-col items-center">
                  <div className="text-[8px] text-slate-500 uppercase tracking-widest mb-1">Urgency</div>
                  <div className="text-sm font-mono text-primary">CRITICAL</div>
                </div>
                <div className="clay-panel p-4 rounded-2xl flex flex-col items-center text-center">
                  <div className="text-[8px] text-slate-500 uppercase tracking-widest mb-1">Vector</div>
                  <div className="text-[10px] font-mono text-slate-300 uppercase">Wind Velocity</div>
                </div>
              </div>
              <div className="space-y-5">
                <div className="text-[9px] font-extrabold text-slate-500 uppercase tracking-[0.2em]">Pattern Scans</div>
                <div className="flex flex-wrap gap-2.5">
                  <button 
                    type="button" 
                    onClick={() => triggerAnalysis("Bottlenecks")}
                    className="text-[9px] font-bold uppercase tracking-widest clay-panel clay-interactive hover:bg-primary/20 hover:text-primary px-4 py-2 rounded-lg transition-all"
                  >
                    Bottlenecks
                  </button>
                  <button 
                    type="button" 
                    onClick={() => triggerAnalysis("Weather Scan")}
                    className="text-[9px] font-bold uppercase tracking-widest clay-panel clay-interactive hover:bg-primary/20 hover:text-primary px-4 py-2 rounded-lg transition-all"
                  >
                    Weather Scan
                  </button>
                  <button 
                    type="button" 
                    onClick={() => triggerAnalysis("Flow Map")}
                    className="text-[9px] font-bold uppercase tracking-widest clay-panel clay-interactive hover:bg-primary/20 hover:text-primary px-4 py-2 rounded-lg transition-all"
                  >
                    Flow Map
                  </button>
                </div>
              </div>
            </div>
            <div className="p-8 mt-auto bg-[#0f1419]/50">
              <div className="relative group">
                <textarea 
                  value={sentinelInput}
                  onChange={(e) => setSentinelInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="w-full clay-panel clay-interactive border-white/5 rounded-3xl p-5 text-[11px] font-medium resize-none focus:ring-1 focus:ring-primary/40 focus:bg-[#252d38] placeholder:text-slate-600 transition-all leading-relaxed font-mono" 
                  placeholder="ENGAGE SENTINEL CORE..." 
                  rows={3}
                  disabled={isSentinelThinking}
                ></textarea>
                <button 
                  type="button" 
                  onClick={() => handleSentinelSubmit()}
                  disabled={!sentinelInput.trim() || isSentinelThinking}
                  className="absolute bottom-4 right-4 w-10 h-10 bg-primary text-[#2b1700] rounded-2xl hover:scale-105 active:scale-95 transition-all flex items-center justify-center shadow-lg disabled:opacity-50 disabled:hover:scale-100"
                >
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
