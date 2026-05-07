"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

const noopSubscribe = () => () => {};

export const CustomCursor = () => {
  const isClient = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const [isHovering, setIsHovering] = useState(false);
  const [isClicking, setIsClicking] = useState(false);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  // Create a spring for exceptionally smooth following
  const springConfig = { damping: 25, stiffness: 300, mass: 0.5 };
  const smoothX = useSpring(mouseX, springConfig);
  const smoothY = useSpring(mouseY, springConfig);
  
  // Create a trailing spring
  const trailSpringConfig = { damping: 40, stiffness: 200, mass: 1 };
  const trailX = useSpring(mouseX, trailSpringConfig);
  const trailY = useSpring(mouseY, trailSpringConfig);
  
  // Track previous positions for rotation
  const [rotation, setRotation] = useState(0);
  
  useEffect(() => {
    if (!isClient) return;
    let lastX = 0;
    let lastY = 0;

    const manageMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
      
      // Calculate rotation based on movement direction
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
        const angle = Math.atan2(dy, dx) * (180 / Math.PI);
        setRotation(angle);
      }
      
      lastX = e.clientX;
      lastY = e.clientY;
    };

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName.toLowerCase() === "button" ||
        target.tagName.toLowerCase() === "a" ||
        target.closest("button") ||
        target.closest("a")
      ) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };
    
    const handleMouseDown = () => setIsClicking(true);
    const handleMouseUp = () => setIsClicking(false);

    window.addEventListener("mousemove", manageMouseMove);
    window.addEventListener("mouseover", handleMouseOver);
    window.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", manageMouseMove);
      window.removeEventListener("mouseover", handleMouseOver);
      window.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isClient, mouseX, mouseY]);

  if (!isClient) return null;

  // Pacman SVG setup
  // We simulate "chewing" with motion when hovering or clicking
  return (
    <>
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[9999] mix-blend-screen"
        style={{
          x: smoothX,
          y: smoothY,
          translateX: "-50%",
          translateY: "-50%",
          rotate: rotation,
        }}
      >
        <motion.div
          animate={{
            scale: isClicking ? 0.8 : isHovering ? 1.2 : 1,
          }}
          className="relative w-8 h-8 flex items-center justify-center glow-primary rounded-full bg-pac-yellow/20"
        >
          {/* Pac-Man Shape using SVG */}
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            className="text-pac-yellow fill-current drop-shadow-[0_0_8px_rgba(252,238,9,0.8)]"
          >
            <motion.path
              initial={{ d: "M12,12 L24,4 A12,12 0 1,0 24,20 Z" }}
              animate={{
                d:
                  isHovering || isClicking
                    ? ["M12,12 L24,2 A12,12 0 1,0 24,22 Z", "M12,12 L24,12 A12,12 0 1,0 24,12 Z"]
                    : "M12,12 L24,4 A12,12 0 1,0 24,20 Z"
              }}
              transition={
                isHovering || isClicking
                  ? { repeat: Infinity, duration: 0.2 }
                  : { duration: 0.3 }
              }
            />
          </svg>
        </motion.div>
      </motion.div>

      {/* Trailing particle */}
      <motion.div
        className="fixed top-0 left-0 w-2 h-2 rounded-full bg-pac-yellow pointer-events-none z-[9998] mix-blend-screen opacity-50 blur-[2px]"
        style={{
          x: trailX,
          y: trailY,
          translateX: "-50%",
          translateY: "-50%",
        }}
      />
    </>
  );
};
