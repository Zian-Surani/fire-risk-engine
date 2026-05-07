"use client";
import React from "react";
import { ShieldCheck, FileCheck, Scale, AlertOctagon, Download } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveSocket } from "@/hooks/useLiveSocket";
import { api, type Envelope, type ComplianceData } from "@/lib/api";

export default function RiskCompliance() {
  const { data, error, refresh } = useDashboard<Envelope<ComplianceData>>({
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
