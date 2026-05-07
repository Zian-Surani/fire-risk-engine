"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDashboard } from "@/hooks/useDashboard";
import { api, type Envelope, type RoadmapData } from "@/lib/api";

const STATIC_MODULES = [
  {
    id: "ingestion",
    title: "Data Ingestion",
    icon: "api",
    color: "from-blue-500 to-cyan-400",
    shadow: "shadow-blue-500/20",
    staticDetails: [
      "Bronze ingestion notebooks persist raw city datasets",
      "Delta tables preserve historical traceability",
      "Validation checks guard schema drift",
      "5 Bronze tables from Socrata/city APIs",
    ],
  },
  {
    id: "engineering",
    title: "Data Engineering",
    icon: "schema",
    color: "from-purple-500 to-indigo-400",
    shadow: "shadow-purple-500/20",
    staticDetails: [
      "Silver unifies 23,634 addresses into a risk base",
      "34 engineered features: response, compliance, recency",
      "Gold serves 13 decision-ready output tables",
      "641,337 total records across 19 tables",
    ],
  },
  {
    id: "intelligence",
    title: "Intelligence Layer",
    icon: "psychology",
    color: "from-fuchsia-500 to-pink-400",
    shadow: "shadow-fuchsia-500/20",
    staticDetails: [
      "Adjusted risk amplification for visual contrast",
      "Multi-objective deployment optimization",
      "Scenario simulation and AI reasoning",
      "Deterministic fallback when OpenAI is unavailable",
    ],
  },
  {
    id: "decision",
    title: "Decision Layer",
    icon: "account_tree",
    color: "from-orange-500 to-red-400",
    shadow: "shadow-orange-500/20",
    staticDetails: [
      "Risk scoring with recency, violation, and response weights",
      "Constraint-based budget optimization",
      "District centroid mapping for globe rendering",
      "Action playbook generation",
    ],
  },
  {
    id: "governance",
    title: "Governance & Feedback",
    icon: "gavel",
    color: "from-emerald-500 to-teal-400",
    shadow: "shadow-emerald-500/20",
    staticDetails: [
      "11 validation checks on Bronze and Silver layers",
      "Explainability per address with top-3 risk drivers",
      "PDF and CSV compliance report exports",
      "WebSocket live push for real-time operator feedback",
    ],
  },
  {
    id: "visuals",
    title: "Visualization & Action",
    icon: "monitoring",
    color: "from-sky-500 to-cyan-400",
    shadow: "shadow-sky-500/20",
    staticDetails: [
      "5-second polling with in-memory snapshot caching",
      "5-page live dashboard (no rebuild required)",
      "Globe markers with adjusted risk banding",
      "Reports download, optimize, and simulate APIs",
    ],
  },
];

export default function RoadmapPage() {
  const { data } = useDashboard<Envelope<RoadmapData>>({
    fetcher: api.roadmap, intervalMs: 30000,
  });

  const [activeModule, setActiveModule] = useState<string | null>(null);
  const rd = data?.data;
  const counts = rd?.counts ?? {
    bronze_tables: 5, silver_tables: 1, gold_tables: 13,
    total_tables: 19, total_records: 641337, validation_checks: 11,
  };
  const badges = rd?.badges ?? ["Real-time Databricks Reads", "Constraint-Based Optimization", "Explainable AI Layer"];
  const pipelineNodes = rd?.pipeline_nodes ?? ["Data Sources","Ingestion","Processing","ML Models","Decision Engine","Output"];
  const limitations = rd?.known_limitations ?? [];

  const modules = STATIC_MODULES.map((m) => {
    const live = rd?.modules?.find((lm) => lm.id === m.id);
    return { ...m, details: live?.details ?? m.staticDetails };
  });

  const selectedModule = modules.find((m) => m.id === activeModule);

  return (
    <div className="w-full min-h-screen pb-20 relative">
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/3 left-10 w-80 h-80 bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col gap-4 mb-12">
        <h1 className="text-4xl font-bold text-white tracking-tight">Implementation Roadmap</h1>
        <p className="text-slate-400 max-w-2xl">
          Interactive system pipeline for fire risk prediction, decision optimization, and live Databricks consumption.
        </p>
        <div className="flex flex-wrap items-center gap-3 mt-2">
          {badges.map((label) => (
            <div key={label} className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-slate-300 shadow-sm backdrop-blur-sm">
              {label}
            </div>
          ))}
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-12">
        {[
          { label: "Bronze Tables", value: counts.bronze_tables },
          { label: "Silver Tables", value: counts.silver_tables },
          { label: "Gold Tables", value: counts.gold_tables },
          { label: "Total Tables", value: counts.total_tables },
          { label: "Total Records", value: counts.total_records.toLocaleString() },
          { label: "Validation Checks", value: counts.validation_checks },
        ].map((stat) => (
          <div key={stat.label} className="bg-white/5 border border-white/10 rounded-2xl p-4 text-center">
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Modules grid */}
      <div className="mb-20">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
          <span className="material-symbols-outlined text-cyan-400">view_comfy_alt</span> System Modules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative z-10">
          {modules.map((mod, idx) => (
            <motion.div
              key={mod.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1, duration: 0.5 }}
              onClick={() => setActiveModule(activeModule === mod.id ? null : mod.id)}
              className={`cursor-pointer group relative overflow-hidden rounded-2xl border transition-all duration-300 ${
                activeModule === mod.id
                  ? "border-white/40 bg-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)] scale-[1.02]"
                  : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20"
              }`}
            >
              <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${mod.color} opacity-80`} />
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br ${mod.color} ${mod.shadow} text-white shadow-lg`}>
                    <span className="material-symbols-outlined">{mod.icon}</span>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:bg-white/10 transition-colors">
                    <span className="material-symbols-outlined text-sm text-slate-300 transition-transform duration-300 group-hover:translate-x-0.5">
                      {activeModule === mod.id ? "keyboard_arrow_up" : "keyboard_arrow_right"}
                    </span>
                  </div>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{mod.title}</h3>
                <p className="text-sm text-slate-400">Click to expand processing steps</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Expanded View Modal */}
      <AnimatePresence>
        {selectedModule && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setActiveModule(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-full max-w-2xl bg-surface-container-highest border border-white/10 rounded-3xl overflow-hidden shadow-2xl relative"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="absolute top-4 right-4 z-10 w-10 h-10 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 border border-white/10 cursor-pointer transition-colors" onClick={() => setActiveModule(null)}>
                <span className="material-symbols-outlined text-slate-300">close</span>
              </div>
              <div className={`h-32 bg-gradient-to-br ${selectedModule.color} relative overflow-hidden`}>
                <div className="absolute inset-0 bg-black/20" />
                <div className="absolute -bottom-10 -right-10 text-9xl text-white/10 font-bold material-symbols-outlined select-none" style={{ fontSize: "160px" }}>
                  {selectedModule.icon}
                </div>
                <div className="absolute bottom-6 left-8 flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30 text-white shadow-xl">
                    <span className="material-symbols-outlined text-2xl">{selectedModule.icon}</span>
                  </div>
                  <h2 className="text-3xl font-bold text-white drop-shadow-md">{selectedModule.title}</h2>
                </div>
              </div>
              <div className="p-8">
                <p className="text-slate-400 mb-6 font-medium tracking-wide text-sm uppercase">Implementation Details</p>
                <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[1.125rem] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
                  {selectedModule.details.map((detail, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 + idx * 0.1 }}
                      className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active"
                    >
                      <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-surface-container-highest shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 bg-gradient-to-br ${selectedModule.color} shadow-lg z-10`}>
                        <span className="text-xs font-bold text-white">{idx + 1}</span>
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 transition-colors shadow-sm">
                        <span className="text-slate-200 font-semibold">{detail}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Known Limitations */}
      {limitations.length > 0 && (
        <div className="mt-10 mb-16 p-6 rounded-2xl bg-white/5 border border-white/10">
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-yellow-400 text-base">warning</span> Known Limitations
          </h3>
          <ul className="space-y-2">
            {limitations.map((lim, i) => (
              <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                <span className="text-yellow-400 mt-0.5">&#x2022;</span> {lim}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Connected Pipeline Flow */}
      <div className="mt-16 pt-16 border-t border-white/5 relative z-0">
        <h2 className="text-xl font-semibold text-white mb-10 flex items-center gap-2">
          <span className="material-symbols-outlined text-purple-400">route</span> Connected Pipeline Flow
        </h2>
        <div className="relative w-full max-w-[1000px] mx-auto py-10 px-4">
          <div className="flex items-center justify-between relative z-10 w-full">
            {pipelineNodes.map((node, idx) => (
              <React.Fragment key={node}>
                <div className={`relative flex items-center justify-center p-4 rounded-xl border ${node === "Decision Engine" ? "border-[#ff7a00]/50 bg-[#ff7a00]/10 shadow-[0_0_20px_rgba(255,122,0,0.2)]" : "border-outline-variant/30 bg-surface-container-high"} z-20 w-[140px] h-[64px] text-center shadow-lg transition-transform hover:scale-105 duration-300 shrink-0`}>
                  <span className={`text-[13px] font-bold tracking-wide ${node === "Decision Engine" ? "text-[#ff7a00]" : "text-slate-200"}`}>{node}</span>
                </div>
                {idx < pipelineNodes.length - 1 && (
                  <div className="flex-1 flex items-center justify-center min-w-[20px] max-w-[80px] h-full relative z-10 mx-2">
                    <div className="h-[2px] w-full bg-slate-700/80 rounded-full mx-1 overflow-hidden relative">
                      <motion.div
                        initial={{ left: "-100%" }}
                        animate={{ left: "100%" }}
                        transition={{ repeat: Infinity, duration: 1.5, ease: "linear", delay: idx * 0.2 }}
                        className="absolute top-0 bottom-0 w-[40px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
                      />
                    </div>
                    <div className="w-0 h-0 border-y-[4px] border-y-transparent border-l-[6px] border-l-slate-400 absolute right-0" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
          <div className="absolute h-[80px] top-[50%] -z-10 pointer-events-none" style={{ left: "calc(60% - 14px)", right: "70px" }}>
            <div className="absolute inset-0 border-b-2 border-l-2 border-r-2 border-emerald-500/80 rounded-b-3xl">
              <div className="absolute inset-x-0 bottom-[-2px] h-[2px] overflow-hidden rounded-b-3xl">
                <motion.div
                  initial={{ left: "100%" }}
                  animate={{ left: "-10%" }}
                  transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                  className="absolute top-0 bottom-0 w-32 bg-gradient-to-r from-transparent via-emerald-400 to-transparent"
                />
              </div>
            </div>
            <span className="absolute top-[44px] right-[-6px] text-emerald-500 material-symbols-outlined text-[12px] rotate-90">arrow_forward_ios</span>
            <div className="absolute top-[30px] left-[-5px] w-0 h-0 border-x-[5px] border-x-transparent border-b-[6px] border-b-emerald-500" />
            <div className="absolute left-1/2 bottom-[-14px] -translate-x-1/2 px-3 py-[2px] bg-surface-container-lowest border border-emerald-500/40 rounded-full flex items-center gap-1.5 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
              <motion.span animate={{ rotate: -360 }} transition={{ repeat: Infinity, duration: 3, ease: "linear" }} className="material-symbols-outlined text-[14px] text-emerald-400">sync</motion.span>
              <span className="uppercase text-[10px] font-bold tracking-widest text-emerald-300">Continuous Learning Loop</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
