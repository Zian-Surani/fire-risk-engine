"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { EatableText } from "@/components/landing/EatableText";

const GHOST_TOPS = [15, 35, 55, 75] as const;

const PacmanBackground = () => {
  const [pacmans, setPacmans] = useState<{ id: number; top: number; delay: number; duration: number }[]>([]);
  const [ghosts, setGhosts] = useState<{ top: number; duration: number; delay: number }[]>([]);

  useEffect(() => {
    // Generate background moving pacmans to make the background "live"
    const generate = () => {
      return Array.from({ length: 8 }).map((_, i) => ({
        id: i,
        top: Math.random() * 80 + 10,
        delay: Math.random() * 5,
        duration: Math.random() * 15 + 20,
      }));
    };
    queueMicrotask(() => {
      setPacmans(generate());
      setGhosts(
        GHOST_TOPS.map((top) => ({
          top,
          duration: 25 + Math.random() * 10,
          delay: Math.random() * 5,
        }))
      );
    });
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20 z-0">
      {pacmans.map(p => (
        <motion.div
          key={`pac-${p.id}`}
          initial={{ x: "-10vw", y: `${p.top}vh` }}
          animate={{ x: "110vw" }}
          transition={{
            repeat: Infinity,
            duration: p.duration,
            ease: "linear",
            delay: p.delay
          }}
          className="absolute text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.6)]"
        >
          {/* Simple Pacman SVG Icon */}
          <svg width="24" height="24" viewBox="0 0 24 24">
            <path d="M12 2a10 10 0 1 0 10 10h-10z" fill="currentColor" />
          </svg>
        </motion.div>
      ))}
      
      {/* TASK 4: Ghost Antagonists drifting RIGHT to LEFT */}
      {ghosts.map((g, i) => (
        <motion.div
          key={`ghost-${i}`}
          initial={{ x: "110vw", y: `${g.top}vh` }}
          animate={{ x: "-10vw" }}
          transition={{
            repeat: Infinity,
            duration: g.duration,
            ease: "linear",
            delay: g.delay,
          }}
          className="absolute text-[var(--risk-red)] drop-shadow-[0_0_10px_rgba(239,68,68,0.8)] opacity-25"
        >
          <svg width="28" height="28" viewBox="0 0 14 14" fill="currentColor">
            <path d="M7,0 C3.134,0 0,3.134 0,7 L0,14 L2,12 L4,14 L7,11 L10,14 L12,12 L14,14 L14,7 C14,3.134 10.866,0 7,0 Z M4,6 C3.448,6 3,5.105 3,4 C3,2.895 3.448,2 4,2 C4.552,2 5,2.895 5,4 C5,5.105 4.552,6 4,6 Z M10,6 C9.448,6 9,5.105 9,4 C9,2.895 9.448,2 10,2 C10.552,2 11,2.895 11,4 C11,5.105 10.552,6 10,6 Z" />
            <circle cx="4.5" cy="4.5" r="1" fill="#000" />
            <circle cx="10.5" cy="4.5" r="1" fill="#000" />
          </svg>
        </motion.div>
      ))}
    </div>
  );
};

type ParticleSpec = {
  id: number;
  left: number;
  top: number;
  y1: number;
  duration: number;
  delay: number;
};

export const HeroSection = ({ onEnter }: { onEnter: () => void }) => {
  const [particles, setParticles] = useState<ParticleSpec[]>([]);
  const [isHoveringBtn, setIsHoveringBtn] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      setParticles(
        Array.from({ length: 15 }, (_, i) => ({
          id: i,
          left: Math.random() * 100,
          top: Math.random() * 100,
          y1: Math.random() * -50,
          duration: 4 + Math.random() * 4,
          delay: Math.random() * 5 + 6,
        }))
      );
    });
  }, []);

  return (
    <section className="relative w-[100vw] h-[100vh] flex flex-col items-center justify-center overflow-hidden bg-[#0B0F14]">
      
      {/* 5. Background grid subtly lights up + Parallax Layer */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 0.5, y: 0 }}
        transition={{ delay: 0.5, duration: 2, ease: "easeOut" }}
        className="absolute inset-0 bg-dot-pattern mix-blend-screen"
      />
      
      {/* Retro Arcade Grid Overlay */}
      <motion.div 
           initial={{ opacity: 0 }}
           animate={{ opacity: 0.15 }}
           transition={{ delay: 0.5, duration: 3 }}
           className="absolute inset-0 pointer-events-none" 
           style={{ 
             backgroundImage: 'linear-gradient(rgba(6, 182, 212, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(6, 182, 212, 0.4) 1px, transparent 1px)',
             backgroundSize: '40px 40px',
             maskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)',
             WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)'
           }} 
      />
      <PacmanBackground />
      <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background to-background pointer-events-none z-0" />
      
      {/* 3. Ghost entity appears -> 4. Morphs into soft glowing fire risk zone */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 20 }}
        animate={{ opacity: [0, 1, 0], scale: [0.8, 1, 2], y: [20, 0, -20] }}
        transition={{ delay: 0.5, duration: 3, times: [0, 0.4, 1] }}
        className="absolute top-[25%] left-[60%] text-risk-red z-0 flex flex-col items-center justify-center transform -translate-x-1/2 -translate-y-1/2"
      >
        {/* Using a blockier representation for the ghost/fire element to fit the theme */}
        <div className="w-16 h-16 bg-risk-red/80 glow-danger" style={{ clipPath: "polygon(0 0, 100% 0, 100% 100%, 75% 80%, 50% 100%, 25% 80%, 0 100%)" }} />
      </motion.div>
      
      {/* Morph Glow blob that replaces the ghost */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: [0, 0.8, 0.6], scale: [0.5, 1.2, 1] }}
        transition={{ delay: 2.5, duration: 3, ease: "easeOut" }}
        className="absolute top-[10%] left-[50%] w-[350px] h-[350px] bg-risk-red/30 rounded-full blur-[100px] z-[0] mix-blend-screen pointer-events-none"
      />

      {/* 6. Headline fades in upwards */}
      <div className="relative z-10 flex flex-col items-center text-center max-w-5xl px-4 mt-20 font-sans">
        
        {/* Retro Header Label */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
          className="mb-8 inline-flex items-center gap-2 px-6 py-2 border-2 border-intel-cyan/50 bg-black text-intel-cyan text-xs tracking-widest glow-intel"
          style={{ fontFamily: 'var(--font-press-start)' }}
        >
          <span className="w-2 h-2 bg-intel-cyan animate-pulse" />
          SYSTEM_ACTIVE
        </motion.div>

        {/* Eatable Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1, ease: "easeOut" }}
          className="text-4xl md:text-5xl font-bold leading-relaxed text-foreground mb-8 text-shadow-sm"
          style={{ fontFamily: 'var(--font-press-start)' }}
        >
          <EatableText text="NAVIGATE FIRE RISK." /> <br/>
          <span className="text-risk-orange mt-4 inline-block">
            <EatableText text="ACT BEFORE IT SPREADS." />
          </span>
        </motion.h1>

        {/* Supportive text with modern sci-fi readability (no pixel font here so it's readable) */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.5, ease: "easeOut" }}
          className="text-xl md:text-2xl text-foreground/80 mb-6 max-w-3xl font-light"
        >
          <EatableText text="A self-learning intelligence system for predictive risk, optimized response, and continuous improvement." />
        </motion.p>
        
        <motion.p
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 2.5, ease: "easeOut" }}
          className="text-lg md:text-xl text-pac-yellow/90 mb-16 max-w-2xl font-bold tracking-wide"
        >
          <EatableText text="Every second of delay increases risk." />
        </motion.p>

        {/* Arcade CTA Button */}
        <div className="relative mt-4 z-50">
           <AnimatePresence>
             {isHoveringBtn && (
                <motion.div
                   initial={{ x: -40, opacity: 0, scale: 0.5 }}
                   animate={{ x: -10, opacity: 1, scale: 1 }}
                   exit={{ x: -40, opacity: 0, scale: 0.5 }}
                   transition={{ duration: 0.2, ease: "easeOut" }}
                   className="absolute top-1/2 -left-[60px] -translate-y-1/2 z-20 pointer-events-none w-10 h-10 bg-pac-yellow rounded-full glow-primary drop-shadow-[0_0_10px_rgba(250,204,21,1)]"
                   style={{ clipPath: "polygon(100% 74%, 44% 48%, 100% 21%, 100% 0, 0 0, 0 100%, 100% 100%)" }}
                />
             )}
           </AnimatePresence>

          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ 
               opacity: 1, 
               y: 0, 
               scale: isHoveringBtn ? 1.1 : 1,
               boxShadow: isHoveringBtn ? "0 0 35px rgba(250, 204, 21, 0.5)" : "0 0 0px rgba(250, 204, 21, 0)"
            }}
            transition={{ opacity: { duration: 0.8, delay: 3 }, y: { duration: 0.8, delay: 3 }, scale: { duration: 0.3 } }}
            onMouseEnter={() => setIsHoveringBtn(true)}
            onMouseLeave={() => setIsHoveringBtn(false)}
            onClick={onEnter}
            className="group relative px-10 py-6 border-4 border-pac-yellow text-md font-bold text-pac-yellow bg-black uppercase tracking-[0.3em] overflow-hidden hover:bg-pac-yellow hover:text-black transition-colors duration-300"
            style={{ fontFamily: 'var(--font-press-start)' }}
          >
            <span className="relative z-10 flex items-center justify-center gap-4">
              {/* TASK 3: INSERT COIN BLINK */}
              <span className="animate-[insertCoin_1s_step-end_infinite] group-hover:[animation-play-state:paused]">
                PAC IN !
              </span>
            </span>
          </motion.button>
        </div>
      </div>

      {/* Floating particles (data pixels) - Parallax layer */}
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute w-2 h-2 bg-intel-cyan/60 shadow-[0_0_8px_#06B6D4]"
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
          }}
          animate={{
            y: [0, p.y1, 0],
            opacity: [0, 0.8, 0],
          }}
          transition={{
            duration: p.duration,
            repeat: Infinity,
            delay: p.delay,
          }}
        />
      ))}
    </section>
  );
};
