"use client";

import { useState, useEffect, useRef } from "react";

export const ArcadeHUD = () => {
  const [score, setScore] = useState(0);
  const [lives, setLives] = useState(3);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scoreIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Scroll tracking for score
    const handleScrollId = () => {
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
      
      if (!scoreIntervalRef.current) {
        // Start incrementing score while actively scrolling
        scoreIntervalRef.current = setInterval(() => {
          setScore(prev => Math.min(prev + 10, 999990));
        }, 300);
      }

      scrollTimeoutRef.current = setTimeout(() => {
        // Stop incrementing after 500ms of no scroll
        if (scoreIntervalRef.current) {
          clearInterval(scoreIntervalRef.current);
          scoreIntervalRef.current = null;
        }
      }, 500);
    };

    window.addEventListener("scroll", handleScrollId, { passive: true });

    return () => {
      window.removeEventListener("scroll", handleScrollId);
      if (scoreIntervalRef.current) clearInterval(scoreIntervalRef.current);
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    // Observer for LIVES logic based on data-level="02"
    const level02Node = document.querySelector('[data-level="02"]');
    if (!level02Node) return;

    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (entry.isIntersecting) {
        setLives(2); // In level 2 -> subtract 1 life
      } else {
        // if we are above level02, restore life. 
        // We can check boundary by looking at intersection rect bounding
        if (entry.boundingClientRect.top > 0) {
           setLives(3); // Scrolled back up
        }
      }
    }, { threshold: 0.1 });

    observer.observe(level02Node);
    return () => observer.disconnect();
  }, []);

  return (
    <div 
      className="fixed top-6 right-6 z-[50] pointer-events-none flex gap-8 text-[var(--pac-yellow)] text-sm md:text-base drop-shadow-[0_0_8px_rgba(250,204,21,0.6)]"
      style={{ fontFamily: 'var(--font-press-start)' }}
    >
      <div>SCORE: {score.toString().padStart(6, '0')}</div>
      <div className="flex gap-2">
        LIVES: 
        <span className="tracking-widest">
          {Array(3).fill('O').map((_, i) => (
             <span key={i} style={{ opacity: i < lives ? 1 : 0.2 }}>●</span>
          ))}
        </span>
      </div>
    </div>
  );
};
