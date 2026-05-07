"use client";

import { useCallback, useEffect, useState, useRef } from "react";

export const AudioEngine = () => {
  const [muted, setMuted] = useState(true);
  const audioCtxRef = useRef<AudioContext | null>(null);
  
  // Oscillators
  const sirenOscRef = useRef<OscillatorNode | null>(null);
  const sirenGainRef = useRef<GainNode | null>(null);
  const wakaOscRef = useRef<OscillatorNode | null>(null);
  const wakaGainRef = useRef<GainNode | null>(null);
  
  // Logic refs
  const wakaIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const wakaHighRef = useRef(true);
  const lastEatTimeRef = useRef(0);

  // Initialize Audio Context on first unmute
  const initAudio = () => {
    if (!audioCtxRef.current && typeof window !== "undefined") {
      const w = window as Window & { webkitAudioContext?: typeof AudioContext };
      const Ctor = window.AudioContext ?? w.webkitAudioContext;
      if (Ctor) {
        audioCtxRef.current = new Ctor();
      }
    }
  };

  const playDotEat = useCallback(() => {
    if (muted || !audioCtxRef.current) return;
    const now = performance.now();
    if (now - lastEatTimeRef.current < 50) return; // throttle 50ms
    lastEatTimeRef.current = now;

    const ctx = audioCtxRef.current;
    if (ctx.state === "suspended") void ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "triangle";
    osc.frequency.setValueAtTime(200, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.08);

    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.08);
  }, [muted]);

  useEffect(() => {
    // EatableText DOT_EAT hook using event delegation
    // We target spans inside EatableText container
    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      // Depending on the implementation of EatableText, its individual characters usually have a motion span child.
      // A safe check is finding if it's text within the landing page boundaries wrapped in our EatableText span.
      // We know it drops characters, so if it contains a single letter or word wrapped, we consider it.
      // Even broadly firing on any hovered span that isn't empty will work since we want that sweeping retro vibe on text.
      if (target.tagName.toLowerCase() === 'span' && target.textContent && target.textContent.trim().length > 0 && target.closest('p, h1, h2, div')) {
         // Because EatableText animates spans, we listen globally
         // This can be noisy if we have lots of spans, but the throttle keeps it safe.
         playDotEat();
      }
    };

    if (!muted) {
      window.addEventListener("mouseover", handleMouseOver, { passive: true });
    }

    return () => {
      window.removeEventListener("mouseover", handleMouseOver);
    };
  }, [muted, playDotEat]);

  useEffect(() => {
    if (!audioCtxRef.current) return;
    const ctx = audioCtxRef.current;

    if (muted) {
      ctx.suspend();
    } else {
      ctx.resume();
    }
  }, [muted]);

  useEffect(() => {
    // Background Loops (Siren & Waka)
    if (!audioCtxRef.current) return;
    const ctx = audioCtxRef.current;

    // Siren
    const setupSiren = () => {
      sirenOscRef.current = ctx.createOscillator();
      sirenOscRef.current.type = "sawtooth";
      sirenOscRef.current.frequency.value = 120;
      sirenGainRef.current = ctx.createGain();
      sirenGainRef.current.gain.value = 0; // default off 
      sirenOscRef.current.connect(sirenGainRef.current);
      sirenGainRef.current.connect(ctx.destination);
      sirenOscRef.current.start();
    };

    // Waka 
    const setupWaka = () => {
      wakaOscRef.current = ctx.createOscillator();
      wakaOscRef.current.type = "square";
      wakaGainRef.current = ctx.createGain();
      wakaGainRef.current.gain.value = 0; // default off
      wakaOscRef.current.connect(wakaGainRef.current);
      wakaGainRef.current.connect(ctx.destination);
      wakaOscRef.current.start();
    };

    if (!sirenOscRef.current) setupSiren();
    if (!wakaOscRef.current) setupWaka();

    // Intersection observers to toggle sound lines
    const checkWaka = () => {
      // Logic: Waka is active anywhere unless paused.
      // To strictly follow "loop while Pac-Man path animations are active", we can assume level 03 is running them.
      // But they are always running looping in DispatchPaths.
      if (!wakaGainRef.current || !wakaOscRef.current) return;
      wakaGainRef.current.gain.setTargetAtTime(0.02, ctx.currentTime, 0.05);
      
      if (!wakaIntervalRef.current) {
        wakaIntervalRef.current = setInterval(() => {
          if (!wakaOscRef.current) return;
          wakaHighRef.current = !wakaHighRef.current;
          wakaOscRef.current.frequency.setValueAtTime(wakaHighRef.current ? 440 : 330, ctx.currentTime);
        }, 120);
      }
    };

    const stopWaka = () => {
      if (wakaGainRef.current) wakaGainRef.current.gain.setTargetAtTime(0, ctx.currentTime, 0.05);
      if (wakaIntervalRef.current) {
        clearInterval(wakaIntervalRef.current);
        wakaIntervalRef.current = null;
      }
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const level = entry.target.getAttribute("data-level");
        if (level === "02") {
          // GHOST SIREN
          if (sirenGainRef.current) {
             sirenGainRef.current.gain.setTargetAtTime(entry.isIntersecting ? 0.04 : 0, ctx.currentTime, 0.1);
          }
        }
        if (level === "03" || level === "01") {
          // Waka active on 01 (pacman drift) and 03 (paths)
          if (entry.isIntersecting) {
            checkWaka();
          } else {
            // Need robust checks if neither are intersecting, but simplistic approximation:
            // if we are leaving a waka zone, turn off.
            // If another waka zone intersects immediately, it turns back on.
            stopWaka();
          }
        }
      });
    }, { threshold: 0 });

    document.querySelectorAll("[data-level]").forEach(el => observer.observe(el));

    // Wait, initially if level 01 is active we need to kickstart waka.
    const level1 = document.querySelector('[data-level="01"]');
    if (level1) observer.observe(level1);

    return () => {
      observer.disconnect();
    };

  }, [muted]);

  const toggleMute = () => {
    if (muted) {
      initAudio();
    }
    setMuted(!muted);
  };

  return (
    <button 
      onClick={toggleMute}
      className="fixed bottom-6 left-6 z-[100] text-[var(--pac-yellow)] bg-transparent hover:scale-110 transition-transform font-bold text-2xl drop-shadow-[0_0_8px_rgba(250,204,21,0.6)] cursor-none"
      style={{ fontFamily: 'var(--font-press-start)' }}
      aria-label="Toggle Audio"
    >
      {muted ? "🔇" : "🔊"}
    </button>
  );
};
