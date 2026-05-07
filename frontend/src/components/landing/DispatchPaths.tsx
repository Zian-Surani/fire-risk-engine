"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { EatableText } from "@/components/landing/EatableText";

const AnimatedRiskPacman = () => (
  <motion.div
    className="absolute top-0 left-0 w-8 h-8 -ml-4 -mt-4 text-pac-yellow z-30 drop-shadow-[0_0_10px_rgba(250,204,21,0.8)]"
    animate={{
      x: [100, 100, 100, 500, 500, 500, 500, 500],
      y: [460, 280, 280, 280, 280, 200, 200, 200],
      rotate: [-90, -90, 0, 0, -90, -90, -90, -90],
      opacity: [1, 1, 1, 1, 1, 1, 1, 0]
    }}
    transition={{ duration: 4, repeat: Infinity, times: [0, 0.244, 0.245, 0.79, 0.791, 0.9, 0.95, 1], ease: "linear" }}
  >
    <motion.div animate={{ scale: [1, 1, 1, 1, 1, 1.3, 0, 0] }} transition={{ duration: 4, repeat: Infinity, times: [0, 0.244, 0.79, 0.89, 0.9, 0.95, 0.96, 1] }} className="w-full h-full relative">
      <svg viewBox="-12 -12 24 24" className="w-full h-full">
        <motion.path 
          animate={{ d: ["M0,0 L12,-6 A12,12 0 1,0 12,6 Z", "M0,0 L12,0 A12,12 0 1,0 12,0 Z"] }}
          transition={{ repeat: Infinity, duration: 0.2 }}
          fill="currentColor"
        />
        <motion.circle cx="-2" cy="-6" r="1.5" fill="black" animate={{ opacity: [1, 0, 0] }} transition={{ duration: 4, repeat: Infinity, times: [0.89, 0.9, 1] }} />
        <motion.path d="M-4,-8 L0,-4 M-4,-4 L0,-8" stroke="black" strokeWidth="1.5" animate={{ opacity: [0, 1, 1] }} transition={{ duration: 4, repeat: Infinity, times: [0.89, 0.9, 1] }} />
      </svg>
    </motion.div>
  </motion.div>
);

const AnimatedSafePacman = () => (
  <motion.div
    className="absolute top-0 left-0 w-8 h-8 -ml-4 -mt-4 text-intel-cyan z-30 drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]"
    animate={{
      x: [100, 350, 350, 350, 350, 500, 500, 500, 500],
      y: [460, 460, 460, 600, 600, 600, 600, 260, 260],
      rotate: [0, 0, 90, 90, 0, 0, -90, -90, -90]
    }}
    transition={{ duration: 6, repeat: Infinity, times: [0, 0.283, 0.284, 0.442, 0.443, 0.612, 0.613, 0.95, 1], ease: "linear" }}
  >
    <svg viewBox="-12 -12 24 24" className="w-full h-full">
      <motion.path 
         animate={{ d: ["M0,0 L12,-6 A12,12 0 1,0 12,6 Z", "M0,0 L12,0 A12,12 0 1,0 12,0 Z"] }}
         transition={{ repeat: Infinity, duration: 0.2 }}
         fill="currentColor"
      />
      <path d="M-4,-7 Q-2,-9 0,-7" stroke="black" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    </svg>
  </motion.div>
);

export const DispatchPaths = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "center center"],
  });

  const nodeOpacity = useTransform(scrollYProgress, [0.6, 0.8], [0, 1]);
  const yOffset = useTransform(scrollYProgress, [0, 1], [100, 0]);

  return (
    <section 
      ref={containerRef}
      className="relative w-full h-[100vh] flex flex-col items-center justify-center overflow-hidden bg-transparent"
    >
      {/* Abstract Arcade Maze Structure */}
      <div className="absolute inset-0 z-0 opacity-40"
           style={{
             maskImage: 'radial-gradient(circle at center top, black 40%, transparent 100%)',
             WebkitMaskImage: 'radial-gradient(circle at center top, black 40%, transparent 100%)'
           }}
      >
        <svg width="100%" height="100%" className="opacity-[0.15]">
          <pattern id="dispatch-grid" width="80" height="80" patternUnits="userSpaceOnUse">
            <rect x="0" y="0" width="80" height="80" fill="none" stroke="#fff" strokeWidth="1" strokeDasharray="4 4" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#dispatch-grid)" />
        </svg>
      </div>

      <motion.div 
        style={{ y: yOffset }}
        className="relative z-10 w-full max-w-6xl px-4 flex justify-between items-center h-full"
      >
        <div className="w-1/2 relative h-[600px] flex items-center justify-center">
          {/* Dispatch SVG Paths - Retro 90 degree "Dot/Pills" Path */}
          <svg className="absolute inset-0 w-full h-full" overflow="visible">
            
            {/* The rigid retro maze tracks (Neon Blue walls) */}
            <path d="M 100 460 L 100 280 L 500 280 L 500 200" fill="none" stroke="rgba(6,182,212,0.3)" strokeWidth="40" strokeLinecap="square" />
            
            <path d="M 100 460 L 350 460 L 350 600 L 500 600 L 500 260" fill="none" stroke="rgba(6,182,212,0.1)" strokeWidth="40" strokeLinecap="square" />

            {/* Path 1: Primary Data Dots Flow (Pac-Man Path) */}
            <motion.path 
              d="M 100 460 L 100 280 L 500 280 L 500 200" 
              fill="none" 
              stroke="#FACC15" 
              strokeWidth="6" 
              strokeDasharray="10 15"
              strokeLinecap="square"
              animate={{ strokeDashoffset: [100, 0] }}
              transition={{ repeat: Infinity, ease: "linear", duration: 1 }}
              className="drop-shadow-[0_0_8px_rgba(250,204,21,0.8)]"
            />
            
            {/* Path 2: Backup Safe Route (Cyan) */}
            <motion.path 
              d="M 100 460 L 350 460 L 350 600 L 500 600 L 500 260" 
              fill="none" 
              stroke="#06B6D4" 
              strokeWidth="4" 
              strokeDasharray="8 12"
              strokeLinecap="square"
              animate={{ strokeDashoffset: [100, 0] }}
              transition={{ repeat: Infinity, ease: "linear", duration: 2 }}
              className="drop-shadow-[0_0_5px_rgba(6,182,212,0.5)]"
            />
          </svg>

          {/* Animated Pacmans over the paths */}
          <AnimatedRiskPacman />
          <AnimatedSafePacman />

          {/* Source Node: Fire Station (The Safe Zone Start) */}
          <motion.div 
            style={{ opacity: nodeOpacity }}
            className="absolute left-[65px] top-[425px] w-[70px] h-[70px] bg-black border-4 border-pac-yellow flex items-center justify-center z-20 shadow-[0_0_20px_rgba(250,204,21,0.5)]"
          >
            <ShieldCheck className="text-pac-yellow" size={32} strokeWidth={2} />
          </motion.div>

          {/* Target Node: The Fire Incident location */}
          <motion.div 
            style={{ opacity: nodeOpacity }}
            className="absolute left-[480px] top-[180px] w-[40px] h-[40px] bg-risk-red z-20 border-2 border-white flex items-center justify-center"
          >
             <div className="w-2 h-2 bg-white animate-ping" />
          </motion.div>
        </div>

        <div className="w-1/2 space-y-8 pl-12">
          <motion.div style={{ opacity: nodeOpacity, fontFamily: 'var(--font-press-start)' }} className="inline-block px-4 py-2 bg-pac-yellow text-black font-bold text-xs tracking-widest mb-4 font-mono">
            <EatableText text="LEVEL 03: ESCAPE ROUTE" />
          </motion.div>

          <motion.h2 
            style={{ opacity: nodeOpacity, fontFamily: 'var(--font-press-start)' }}
            className="text-3xl md:text-5xl font-bold text-white leading-tight"
          >
            <span className="text-pac-yellow"><EatableText text="SMART" /></span><br/>
            <EatableText text="DISPATCH." />
          </motion.h2>

          <motion.p 
            style={{ opacity: nodeOpacity }}
            className="text-foreground/80 text-lg md:text-xl font-light font-sans"
          >
            <EatableText text="It's not just about predicting the risk; it's about navigating around it. The system computes dynamic dispatch routes, generating escape and response paths that actively avoid expanding heat zones." />
          </motion.p>
          
          <motion.div 
            style={{ opacity: nodeOpacity }}
            className="space-y-4 pt-6 font-mono text-sm border-t-2 border-white/20"
          >
            <div className="flex items-center gap-4 bg-pac-yellow/10 p-4 border-2 border-pac-yellow/40">
              <div className="w-4 h-4 bg-pac-yellow animate-pulse" />
              <div className="flex flex-col">
                 <span className="text-white font-bold" style={{ fontFamily: 'var(--font-press-start)', fontSize: '10px' }}>&gt;&gt;&gt; ALGORITHM: A* PATHFINDING</span>
                 <span className="text-pac-yellow/80 text-xs mt-1">STATUS: OPTIMAL ROUTE LOCKED</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4 bg-intel-cyan/10 p-4 border-2 border-intel-cyan/20">
              <div className="w-4 h-4 bg-intel-cyan" />
              <div className="flex flex-col">
                 <span className="text-white font-bold" style={{ fontFamily: 'var(--font-press-start)', fontSize: '10px' }}>&gt;&gt;&gt; BYPASS HAZARDS</span>
                 <span className="text-intel-cyan/70 text-xs mt-1">COMPUTING ALT-ROUTES...</span>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  );
};
