"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { HeroSection } from "@/components/landing/HeroSection";
import { RiskHeatmap } from "@/components/landing/RiskHeatmap";
import { DispatchPaths } from "@/components/landing/DispatchPaths";
import { CustomCursor } from "@/components/landing/CustomCursor";
import { ArcadeHUD } from "@/components/landing/ArcadeHUD";
import { AudioEngine } from "@/components/landing/AudioEngine";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const [systemEntered, setSystemEntered] = useState(false);
  const router = useRouter();

  // Transition sequence
  const handleEnterSystem = () => {
    setSystemEntered(true);
    // Give enough time for the Pac-Man to eat, flash, and fade
    setTimeout(() => {
       router.push('/command-center');
    }, 3900);
  };

  return (
    <main className="arcade-cursor relative min-h-screen bg-background text-foreground selection:bg-intel-cyan/30">
      <CustomCursor />
      
      {/* Global ARcade Systems */}
      <ArcadeHUD />
      <AudioEngine />

      {/* Main scrollable content (Landing Page) */}
      <motion.div 
        initial={{ scale: 1, opacity: 1 }}
        animate={systemEntered ? { scale: 3, opacity: 0, filter: "blur(20px)" } : { scale: 1, opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
        className={`w-full flex flex-col ${systemEntered ? 'pointer-events-none' : ''}`}
      >
        <HeroSection onEnter={handleEnterSystem} />
        <RiskHeatmap />
        <DispatchPaths />
      </motion.div>

      {/* Target Destination Interface (Transition cover) */}
      <AnimatePresence>
        {systemEntered && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className="fixed inset-0 z-50 bg-[#0f1419] flex items-center justify-center flex-col gap-6"
          >
            <motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.6, type: "spring", bounce: 0.4 }}
              className="relative inline-flex items-center py-4 px-2"
            >
              {/* Inner wrapper that vanishes right when the flash bursts to obscure the old elements */}
              <motion.div 
                animate={{ opacity: [1, 1, 0] }}
                transition={{ duration: 3.4, times: [0, 0.99, 1] }}
                className="relative inline-flex items-center"
              >
                {/* Cover that hides eaten text */}
                <motion.div
                  initial={{ width: "40px" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 1.6, delay: 1.5, ease: "linear" }}
                  className="absolute left-0 top-0 bottom-0 bg-[#0f1419] z-10"
                />

                {/* Pac-Man Character */}
                <motion.div
                  initial={{ left: "8px" }}
                  animate={{ left: "calc(100% - 48px)" }}
                  transition={{ duration: 1.6, delay: 1.5, ease: "linear" }}
                  className="absolute top-1/2 -translate-y-1/2 z-20"
                >
                  <svg viewBox="0 0 100 100" className="w-10 h-10 md:w-12 md:h-12 fill-pac-yellow drop-shadow-[0_0_10px_rgba(253,224,71,0.8)] overflow-visible">
                    <motion.path
                      animate={{ 
                        d: [
                          "M50,50 L100,50 A50,50 0 1,0 100,50.1 Z",
                          "M50,50 L100,20 A50,50 0 1,0 100,80 Z",
                          "M50,50 L100,50 A50,50 0 1,0 100,50.1 Z"
                        ]
                      }}
                      transition={{ repeat: Infinity, duration: 0.25 }}
                    />
                  </svg>
                </motion.div>

                <h2 className="text-2xl md:text-4xl font-mono tracking-widest text-white whitespace-nowrap pl-16 pr-10 relative z-0 flex items-center gap-1">
                  Modernizing Experience<span className="animate-pulse">...</span>
                </h2>
              </motion.div>

              {/* Lightweight Flash Burst - Hardware Accelerated pure DOM circle */}
              <motion.div
                initial={{ scale: 0, opacity: 1 }}
                animate={{ scale: [0, 100, 100], opacity: [1, 1, 0] }}
                transition={{ 
                  duration: 0.8, delay: 3.1, ease: "easeOut", times: [0, 0.4, 1] 
                }}
                className="absolute top-1/2 -translate-y-1/2 z-[100] bg-pac-yellow rounded-full pointer-events-none"
                style={{
                  width: '48px',
                  height: '48px',
                  left: 'calc(100% - 48px)'
                }}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
