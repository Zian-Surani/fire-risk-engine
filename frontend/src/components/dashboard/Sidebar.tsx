"use client";
import Link from "next/link";
import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { motion as Motion } from "framer-motion";

export default function Sidebar({ isExpanded = false, onLinkClick }: { isExpanded?: boolean; onLinkClick?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside 
      style={{ width: isExpanded ? 288 : 80 }}
      className={`fixed left-0 top-0 h-full z-[110] flex flex-col pt-8 pb-6 hidden xl:flex transition-[width,shadow] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] clay-panel !rounded-l-none !rounded-r-3xl`}
    >
      {/* Header */}
      <div className="mb-8 px-4 flex flex-col items-center gap-6">
        <div className="flex items-center justify-center overflow-hidden transition-all duration-500 w-full">
            {isExpanded ? (
               <div className="flex items-center gap-2">
                 <img src="/logo-fire.png" alt="FIRE.OS Logo" className="h-10 w-auto object-contain" />
               </div>
            ) : (
                <img src="/logo-fire.png" alt="FIRE.OS" className="h-10 w-auto object-contain" />
            )}
        </div>

      </div>

      <nav className="flex-1 space-y-2 px-3 flex flex-col items-center overflow-hidden pointer-events-auto mt-4">
        {[
            { href: "/command-center", icon: "grid_view", label: "Command Center" },
            { href: "/operations", icon: "monitoring", label: "Operations" },
            { href: "/simulation-ai", icon: "psychology", label: "Simulation + AI" },
            { href: "/risk-compliance", icon: "shield", label: "Risk & Compliance" },
            { href: "/roadmap", icon: "timeline", label: "Roadmap" },
        ].map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
              key={item.label}
              href={item.href || '#'}
              onClick={onLinkClick}
              className={`flex items-center transition-all duration-300 relative group min-h-[52px] rounded-2xl justify-center ${
                  isActive 
                  ? 'text-pac-yellow' 
                  : 'text-slate-400 hover:text-white'
              }`}
              style={{ width: isExpanded ? '100%' : '52px' }}
              >
              {/* Active Background Glow Pill */}
              {isActive && (
                <Motion.div 
                  layoutId="sidebar-active-glow"
                  className="absolute inset-0 bg-[#ffd09f]/10 rounded-2xl border border-[#ffd09f]/20 shadow-[0_4px_24px_rgba(255,208,159,0.1)]"
                />
              )}
              {/* Hover Background */}
              {!isActive && <div className="absolute inset-0 bg-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>}
              
              <div className={`flex items-center gap-3 transition-all duration-500 ${isExpanded ? 'px-5 w-full' : 'w-12 h-12 justify-center'}`}>
                <div className="w-10 h-10 flex items-center justify-center shrink-0 relative z-10 transition-transform duration-300 group-hover:scale-110">
                    <span className="material-symbols-outlined text-xl" >{item.icon}</span> 
                </div>
                {isExpanded && (
                    <span className="font-bold text-[13px] tracking-wide relative z-10 whitespace-nowrap" style={{ fontFamily: 'var(--font-inter)' }}>{item.label}</span>
                )}
              </div>
              </Link>
            )
        })}
      </nav>

      <div className="mt-auto px-3 space-y-3 py-6 border-t border-white/[0.05]">
          <SOSButton isExpanded={isExpanded} />
          
          <button
            onClick={() => {
              if (onLinkClick) onLinkClick();
              router.push('/');
            }}
            className={`flex items-center transition-all duration-300 rounded-2xl relative group min-h-[52px] justify-center text-slate-500 hover:text-white`}
            style={{ width: isExpanded ? '100%' : '52px' }}
          >
            <div className="absolute inset-0 bg-white/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className={`flex items-center transition-all duration-500 ${isExpanded ? 'px-5 w-full gap-3' : 'w-12 h-12 justify-center'}`}>
                <div className="w-10 h-10 flex items-center justify-center shrink-0 relative z-10 p-2 group-hover:scale-110 duration-300">
                    <span className="material-symbols-outlined text-xl">logout</span>
                </div>
                {isExpanded && (
                    <span className="font-bold text-[13px] tracking-wide relative z-10 whitespace-nowrap" style={{ fontFamily: 'var(--font-inter)' }}>Exit Platform</span>
                )}
            </div>
          </button>
      </div>
    </aside>
  );
}

function SOSButton({ isExpanded }: { isExpanded: boolean }) {
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);

  const handleSos = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (loading || success) return;

    // ── DEBUG STEP 1: Button fired ────────────────────────────────────────
    console.log("[SOS] 🚨 Button clicked — initiating emergency dispatch");

    setLoading(true);
    try {
      const { api } = await import("@/lib/api");

      // ── DEBUG STEP 2: About to call API ──────────────────────────────────
      console.log("[SOS] 📡 Calling POST /api/sos …");

      const res = await api.sos({ user_id: "Admin Console" });

      // ── DEBUG STEP 3: API response received ──────────────────────────────
      console.log("[SOS] ✅ API responded:", res);

      if (res.success) {
        console.log("[SOS] 📲 SMS dispatched — message_sid:", res.message_sid, "recipient:", (res as any).recipient);
        setSuccess(true);
        setTimeout(() => {
          setSuccess(false);
        }, 3000);
      } else {
        console.error("[SOS] ❌ Backend returned error:", res.error);
        alert(res.error || "Failed to dispatch SOS signal.");
      }
    } catch (err: any) {
      // ── DEBUG STEP 4: Network / fetch failure ─────────────────────────────
      console.error("[SOS] 🔥 Network / fetch failed:", err?.message ?? err);
      alert("SOS link failed. Telemetry down?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleSos}
      disabled={loading || success}
      className={`flex items-center transition-all duration-500 rounded-2xl relative group min-h-[52px] justify-center 
        ${success ? 'bg-secondary text-on-secondary shadow-[0_0_20px_#71d7cd]' : 
          'bg-tertiary/10 text-tertiary border border-tertiary/20'}`}
      style={{ width: isExpanded ? '100%' : '52px' }}
    >
      <div className={`absolute inset-0 bg-tertiary rounded-2xl transition-opacity duration-300 ${loading ? 'opacity-20 animate-pulse' : 'opacity-0'}`}></div>
      <div className={`flex items-center transition-all duration-500 ${isExpanded ? 'px-5 w-full gap-3' : 'w-12 h-12 justify-center'}`}>
          <div className="w-10 h-10 flex items-center justify-center shrink-0 relative z-10 p-2 group-hover:scale-110 duration-300">
              <span className={`material-symbols-outlined text-2xl ${loading ? 'animate-bounce' : ''}`}>
                {success ? 'check_circle' : loading ? 'hourglass_top' : 'emergency'}
              </span>
          </div>
          {isExpanded && (
              <span className="font-ex font-bold text-[13px] tracking-[0.1em] relative z-10 whitespace-nowrap uppercase" style={{ fontFamily: 'var(--font-inter)' }}>
                {success ? 'Dispatched' : loading ? 'Sending...' : 'Trigger SOS'}
              </span>
          )}
      </div>
    </button>
  );
}
