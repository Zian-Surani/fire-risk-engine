"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

export const LevelFlash = () => {
  const [levelInfo, setLevelInfo] = useState<string | null>(null);
  const seenLevels = useRef<Set<string>>(new Set());

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const level = entry.target.getAttribute("data-level");
            if (level && !seenLevels.current.has(level)) {
              seenLevels.current.add(level);
              setLevelInfo(level);
              
              // Unmount after animation duration (100ms in + 400ms hold + 200ms out = 700ms)
              setTimeout(() => {
                setLevelInfo(null);
              }, 700);
            }
          }
        });
      },
      { threshold: 0.3 }
    );

    const checkLevelNodes = () => {
      document.querySelectorAll("[data-level]").forEach((node) => observer.observe(node));
    };
    
    // Initial and periodic check in case elements mount later
    checkLevelNodes();
    const interval = setInterval(checkLevelNodes, 1000);

    return () => {
      observer.disconnect();
      clearInterval(interval);
    };
  }, []);

  return (
    <AnimatePresence>
      {levelInfo && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.2 } }}
          transition={{ duration: 0.1 }}
          className="fixed inset-0 z-[10000] flex items-center justify-center bg-black pointer-events-none"
        >
          <div 
            className="text-[var(--pac-yellow)] text-3xl md:text-5xl text-center glow-primary"
            style={{ fontFamily: 'var(--font-press-start)' }}
          >
            LEVEL {levelInfo} UNLOCKED
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
