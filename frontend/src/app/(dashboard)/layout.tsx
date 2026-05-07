"use client";

import React, { useState } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import { motion, AnimatePresence } from "framer-motion";
import PacbotWidget from "@/components/chat/PacbotWidget";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);

  return (
    <div className="flex h-screen bg-[#0f1419] overflow-hidden text-white" style={{ fontFamily: 'var(--font-inter)' }}>
      <div onMouseEnter={() => setIsSidebarExpanded(true)} onMouseLeave={() => setIsSidebarExpanded(false)} className="h-full z-[110]">
        <Sidebar isExpanded={isSidebarExpanded} onLinkClick={() => setIsSidebarExpanded(false)} />
      </div>
      
      <main 
        className="flex-1 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] h-full overflow-y-auto relative"
        style={{ marginLeft: 80 }}
      >
        {/* Subtle background glow from primary brand color */}
        <div className="absolute top-0 left-0 w-full h-[500px] bg-gradient-to-b from-[#ffd09f]/5 to-transparent pointer-events-none" />
        
        <div className="p-8 max-w-[1600px] mx-auto min-h-full">
            <AnimatePresence mode="wait">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.4 }}
                    className="h-full flex flex-col pt-4"
                >
                    {children}
                </motion.div>
            </AnimatePresence>
        </div>
      </main>
      <PacbotWidget />
    </div>
  );
}
