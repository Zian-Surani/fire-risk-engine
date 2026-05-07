"use client";

import { motion } from "framer-motion";
import { Activity, Map, RadioReceiver, ShieldAlert, Users, CloudRainWind } from "lucide-react";

interface SystemTransitionProps {
  isEntered: boolean;
}

export const SystemTransition = ({ isEntered }: SystemTransitionProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={isEntered ? { opacity: 1, scale: 1, zIndex: 50, transition: { duration: 0.8, ease: "easeOut" } } : { opacity: 0, scale: 0.8, zIndex: -1 }}
      className="fixed inset-0 w-full h-full bg-background flex flex-col p-4 md:p-8 pointer-events-none"
      style={{ pointerEvents: isEntered ? "auto" : "none" }}
    >
      <div className="w-full h-full flex flex-col gap-6">
        {/* Top Navbar */}
        <motion.header 
          initial={{ y: -50, opacity: 0 }}
          animate={isEntered ? { y: 0, opacity: 1, transition: { delay: 0.4 } } : { y: -50, opacity: 0 }}
          className="w-full h-16 border-b border-white/10 flex items-center justify-between px-6"
        >
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-pac-yellow rounded-full glow-primary" />
            <span className="font-mono text-xl font-bold tracking-widest text-white">FIRE.OS</span>
          </div>
          <div className="flex items-center gap-6 text-sm font-mono text-foreground/60">
            <span className="text-intel-cyan">SYSTEM ONLINE</span>
            <span>12:24:45 UTC</span>
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-risk-red opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-risk-red"></span>
            </span>
          </div>
        </motion.header>

        {/* Main Dashboard Grid */}
        <div className="flex-1 w-full grid grid-cols-12 grid-rows-6 gap-6 min-h-0">
          
          {/* Main Map View */}
          <motion.div 
            initial={{ scale: 0.95, opacity: 0 }}
            animate={isEntered ? { scale: 1, opacity: 1, transition: { delay: 0.6 } } : { scale: 0.95, opacity: 0 }}
            className="col-span-12 lg:col-span-8 row-span-4 border border-white/10 rounded-2xl bg-black/50 relative overflow-hidden flex items-center justify-center"
          >
            {/* Abstract Map UI */}
            <div className="absolute inset-0 bg-dot-pattern opacity-50" />
            <div className="relative z-10 flex flex-col items-center opacity-60">
               <Map size={48} className="text-white mb-4" strokeWidth={1} />
               <span className="font-mono text-xs tracking-widest">MAP INTERFACE INITIALIZING...</span>
            </div>
          </motion.div>

          {/* Side Panels */}
          <motion.div 
            initial={{ x: 50, opacity: 0 }}
            animate={isEntered ? { x: 0, opacity: 1, transition: { delay: 0.7 } } : { x: 50, opacity: 0 }}
            className="col-span-12 lg:col-span-4 row-span-2 border border-white/10 rounded-2xl p-6 bg-black/50 flex flex-col"
          >
            <h3 className="font-mono text-xs text-foreground/50 mb-4 tracking-widest">ACTIVE ALERTS</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <ShieldAlert className="text-risk-red shrink-0" size={20} />
                <div>
                  <p className="text-sm font-bold text-white">Zone 7: Critical Threat</p>
                  <p className="text-xs text-foreground/60 mt-1">98% spread probability within 2 hours. Deployment required.</p>
                </div>
              </div>
              <div className="w-full h-px bg-white/10" />
              <div className="flex items-start gap-4 opacity-50">
                <Activity className="text-risk-orange shrink-0" size={20} />
                <div>
                  <p className="text-sm font-bold text-white">Zone 3: Elevated Temp</p>
                  <p className="text-xs text-foreground/60 mt-1">Monitoring heat anomaly.</p>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ x: 50, opacity: 0 }}
            animate={isEntered ? { x: 0, opacity: 1, transition: { delay: 0.8 } } : { x: 50, opacity: 0 }}
            className="col-span-12 lg:col-span-4 row-span-2 border border-white/10 rounded-2xl p-6 bg-black/50 flex flex-col"
          >
            <h3 className="font-mono text-xs text-foreground/50 mb-4 tracking-widest">WEATHER DYNAMICS</h3>
            <div className="flex items-center justify-between mt-auto mb-auto">
               <CloudRainWind className="text-intel-cyan" size={48} strokeWidth={1} />
               <div className="text-right">
                 <p className="text-3xl font-bold font-mono text-white">24<span className="text-lg text-foreground/50">kts</span></p>
                 <p className="text-sm font-mono text-intel-cyan">NW GUSTS</p>
               </div>
            </div>
          </motion.div>

          {/* Bottom Panels */}
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={isEntered ? { y: 0, opacity: 1, transition: { delay: 0.9 } } : { y: 50, opacity: 0 }}
            className="col-span-12 md:col-span-6 lg:col-span-4 row-span-2 border border-white/10 rounded-2xl p-6 bg-black/50 flex flex-col justify-center"
          >
            <div className="flex items-center gap-4">
              <RadioReceiver size={32} className="text-pac-yellow glow-primary" />
              <div>
                 <p className="font-mono text-xs text-foreground/50">COMMUNICATION UPLINK</p>
                 <p className="font-bold text-white mt-1">Stable</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={isEntered ? { y: 0, opacity: 1, transition: { delay: 1.0 } } : { y: 50, opacity: 0 }}
            className="col-span-12 md:col-span-6 lg:col-span-4 row-span-2 border border-white/10 rounded-2xl p-6 bg-black/50 flex flex-col justify-center"
          >
            <div className="flex items-center gap-4">
              <Users size={32} className="text-intel-cyan glow-intel" />
              <div>
                 <p className="font-mono text-xs text-foreground/50">ACTIVE UNITS</p>
                 <p className="font-bold text-white mt-1">12 Deployed / 4 Standby</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={isEntered ? { y: 0, opacity: 1, transition: { delay: 1.1 } } : { y: 50, opacity: 0 }}
            className="col-span-12 lg:col-span-4 row-span-2 border border-pac-yellow/30 bg-pac-yellow/5 rounded-2xl p-6 flex flex-col items-center justify-center relative overflow-hidden group cursor-pointer"
          >
            <div className="absolute inset-0 bg-pac-yellow/10 group-hover:bg-pac-yellow/20 transition-colors" />
            <span className="font-mono font-bold tracking-widest text-pac-yellow relative z-10 text-lg">
              [ COMMAND OVERRIDE ]
            </span>
          </motion.div>

        </div>
      </div>
    </motion.div>
  );
};
