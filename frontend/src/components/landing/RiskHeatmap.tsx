"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Ghost } from "lucide-react";
import { EatableText } from "@/components/landing/EatableText";

export const RiskHeatmap = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  // Parallax and morphing effects
  // Heat zone starts small and expands drastically like a virus/fire spread
  const riskOpacity = useTransform(scrollYProgress, [0.3, 0.6], [0, 1]);
  const riskScale1 = useTransform(scrollYProgress, [0.3, 0.7], [0.5, 2.5]);
  const textX = useTransform(scrollYProgress, [0.3, 0.5], [-50, 0]);

  return (
    <section 
      ref={containerRef}
      className="relative w-full h-[120vh] flex flex-col items-center justify-center overflow-hidden bg-transparent"
    >
      {/* Arcade Maze Background Grid */}
      <div className="absolute inset-0 z-0 opacity-20" 
           style={{
             backgroundImage: `
               linear-gradient(rgba(6, 182, 212, 0.8) 2px, transparent 2px),
               linear-gradient(90deg, rgba(6, 182, 212, 0.8) 2px, transparent 2px)
             `,
             backgroundSize: '60px 60px',
             maskImage: 'radial-gradient(circle at center top, black 50%, transparent 100%)',
             WebkitMaskImage: 'radial-gradient(circle at center top, black 50%, transparent 100%)'
           }}
      />
      
      {/* Maze "Walls" - abstract blocks in the background */}
      <motion.div 
        style={{ y: useTransform(scrollYProgress, [0, 1], [-100, 100]) }}
        className="absolute inset-0 pointer-events-none z-0"
      >
        <div className="absolute top-[20%] left-[10%] w-[120px] h-[60px] border-4 border-intel-cyan bg-[#0B0F14]" />
        <div className="absolute top-[60%] left-[70%] w-[180px] h-[60px] border-4 border-intel-cyan bg-[#0B0F14]" />
        <div className="absolute top-[40%] left-[40%] w-[60px] h-[120px] border-4 border-intel-cyan bg-[#0B0F14]" />
      </motion.div>

      <div className="relative z-10 w-full max-w-6xl px-4 flex justify-between items-center h-full">
        
        {/* Storytelling Text Side */}
        <div className="w-1/2 space-y-8 p-8 bg-black/60 border-2 border-intel-cyan/30 backdrop-blur-md">
          <motion.div style={{ opacity: riskOpacity, x: textX, fontFamily: 'var(--font-press-start)' }} className="inline-block px-4 py-2 bg-risk-red text-black font-bold text-xs tracking-widest mb-4 font-mono">
            <EatableText text="LEVEL 02: THE SPREAD" />
          </motion.div>
          
          <motion.h2 
            style={{ opacity: riskOpacity, x: textX, fontFamily: 'var(--font-press-start)' }}
            className="text-3xl md:text-5xl font-bold text-white leading-tight"
          >
            <span className="text-risk-red"><EatableText text="FIRE NEVER" /></span><br/>
            <EatableText text="PLAYS FAIR." />
          </motion.h2>
          
          <motion.p 
            style={{ opacity: riskOpacity }}
            className="text-foreground/80 text-lg md:text-xl font-light font-sans"
          >
            <EatableText text="It mutates. It jumps. It spreads through complex terrain logic based on wind vectors and fuel volatility. Our cognitive engine maps this maze in real-time." />
          </motion.p>
          
          {/* Data overlay UI snippet - Retro Terminal Style */}
          <motion.div 
             style={{ opacity: riskOpacity, y: useTransform(scrollYProgress, [0.4, 0.6], [30, 0]) }}
             className="p-6 border-l-4 border-risk-orange bg-black/80 font-mono text-sm space-y-3"
          >
            <div className="flex justify-between items-center text-intel-cyan">
              <span>&gt; WIND_VECTORS</span>
              <span className="animate-pulse">ANALYZING...</span>
            </div>
            <div className="flex justify-between items-center text-risk-orange">
              <span>&gt; TERRAIN_FUEL_INDEX</span>
              <span>CRITICAL</span>
            </div>
            <div className="flex justify-between items-center text-risk-red font-bold">
              <span>&gt; IGNITION_PROBABILITY</span>
              <span>87.4% [THREAT DETECTED]</span>
            </div>
          </motion.div>
        </div>

        {/* Heatmap visualization - Retro Pixel Spread */}
        <div className="relative w-1/2 h-[600px] flex items-center justify-center">
          
          {/* Central Threat Node */}
          <div className="absolute z-20 flex items-center justify-center w-16 h-16 bg-risk-red shadow-[0_0_20px_rgba(239,68,68,1)] border-2 border-white">
            <Ghost size={32} className="text-white animate-bounce" />
          </div>

          {/* Expanding "Pixel" Spread */}
          <motion.div 
            style={{ scale: riskScale1, opacity: riskOpacity }}
            className="absolute z-10 grid grid-cols-5 grid-rows-5 gap-1"
          >
             {/* Creating a blocky pixel explosion pattern */}
             {[...Array(25)].map((_, i) => (
                <motion.div 
                  key={i} 
                  className={`w-8 h-8 ${[12, 7, 11, 13, 17, 6, 8, 16, 18].includes(i) ? 'bg-risk-red/90' : [1,2,3,5,9,10,14,15,19,21,22,23].includes(i) ? 'bg-risk-orange/60' : 'bg-transparent'} 
                  ${[12].includes(i) ? 'bg-white' : ''}
                  `}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 1, 0.5, 1] }}
                  transition={{ 
                    repeat: Infinity, 
                    duration: 0.5 + (i % 3) * 0.5,
                    delay: (i % 5) * 0.1 
                  }}
                />
             ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
};
