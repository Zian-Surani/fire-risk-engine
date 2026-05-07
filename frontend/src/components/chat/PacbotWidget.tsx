"use client";

import React, { useState, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import { MessageSquare, X, Send, Cpu, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Message = {
  role: "user" | "bot";
  content: string;
};

export default function PacbotWidget() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: "WAKA WAKA! I'm PAC-BOT, your Fire Risk Data Analyst. Ready to chomp some data? Insert query to begin!" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const toggleChat = () => setIsOpen(!isOpen);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      
      const response = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: messages.concat(userMsg).map((m) => ({
            role: m.role,
            content: m.content,
          })),
          page_context: pathname
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "bot", content: data.reply }]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "[GAME OVER] Connection to central mainframe lost. Please check endpoint configuration and retry." },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="mb-6 w-96 h-[520px] flex flex-col bg-[#0a0f14]/90 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden font-mono"
          >
            {/* Header */}
            <div className="p-5 bg-surface-container-low/50 border-b border-white/5 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-pac-yellow/10 flex items-center justify-center border border-pac-yellow/20">
                   <svg width="24" height="24" viewBox="0 0 24 24" className="text-pac-yellow fill-current">
                      <path d="M12,12 L24,4 A12,12 0 1,0 24,20 Z" />
                   </svg>
                </div>
                <div>
                  <h3 className="text-pac-yellow font-headline text-[10px] font-extrabold tracking-widest uppercase">Pac-Bot <span className="text-intel-cyan text-[8px] ml-1">v2.0</span></h3>
                  <div className="text-[8px] text-secondary flex items-center gap-1.5 uppercase font-bold tracking-widest mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
                    Ready
                  </div>
                </div>
              </div>
              <button
                onClick={toggleChat}
                className="text-slate-500 hover:text-white transition-colors bg-white/5 p-2 rounded-xl hover:bg-white/10 border border-white/5"
              >
                <X size={18} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 custom-scrollbar">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} gap-3`}>
                  {msg.role === "bot" && (
                    <div className="w-8 h-8 rounded-xl bg-pac-yellow/10 border border-pac-yellow/20 flex items-center justify-center flex-shrink-0">
                      <Cpu size={14} className="text-pac-yellow" />
                    </div>
                  )}
                  
                  <div
                    className={`px-5 py-3 rounded-2xl max-w-[85%] text-[11px] leading-relaxed ${
                      msg.role === "user"
                        ? "bg-intel-cyan/10 border border-intel-cyan/20 text-intel-cyan shadow-[0_4px_15px_rgba(6,182,212,0.1)] rounded-br-none"
                        : "bg-surface-container border border-white/5 text-slate-200 rounded-bl-none shadow-xl"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start gap-3">
                   <div className="w-8 h-8 rounded-xl bg-pac-yellow/10 border border-pac-yellow/20 flex items-center justify-center flex-shrink-0">
                      <Cpu size={14} className="text-pac-yellow" />
                    </div>
                  <div className="px-5 py-3 rounded-2xl bg-surface-container border border-white/5 text-slate-200 rounded-bl-none flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-pac-yellow animate-bounce"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-pac-yellow animate-bounce delay-100"></div>
                    <div className="w-1.5 h-1.5 rounded-full bg-pac-yellow animate-bounce delay-200"></div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Container */}
            <div className="p-5 border-t border-white/5 bg-surface-container-low/30">
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Insert query..."
                  className="w-full bg-[#0a0f14] border border-white/5 text-slate-200 text-xs rounded-2xl pl-5 pr-12 py-4 focus:outline-none focus:border-pac-yellow/30 focus:ring-1 focus:ring-pac-yellow/20 transition-all font-mono placeholder-slate-600"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isTyping}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-pac-yellow/90 hover:bg-pac-yellow text-slate-950 flex items-center justify-center disabled:opacity-30 disabled:hover:scale-100 transition-all active:scale-95 shadow-lg"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Trigger Button - The High Fidelity Pac-Man */}
      <button
        onClick={toggleChat}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="relative group outline-none"
      >
        <motion.div
           animate={{
             rotate: isOpen ? 0 : isHovered ? [0, 90, 180, 270, 360] : 0,
             scale: isHovered ? 1.1 : 1,
           }}
           transition={{
             rotate: isHovered ? { duration: 2, repeat: Infinity, ease: "linear" } : { duration: 0.5 },
             scale: { type: "spring", stiffness: 300, damping: 15 }
           }}
           className="relative w-20 h-20 flex items-center justify-center"
        >
          {/* Outer glow ring */}
          <div className={`absolute inset-0 rounded-full blur-xl transition-all duration-500 ${
            isOpen ? "bg-intel-cyan/20 scale-125" : "bg-pac-yellow/20 scale-110"
          }`} />

          {/* Pac-Man Body */}
          <div className="relative w-14 h-14">
            <svg viewBox="0 0 24 24" className={`w-full h-full drop-shadow-[0_0_10px_rgba(252,238,9,0.5)] ${isOpen ? 'text-intel-cyan' : 'text-pac-yellow'} fill-current transition-colors duration-500`}>
              <motion.path
                initial={{ d: "M12,12 L24,4 A12,12 0 1,0 24,20 Z" }}
                animate={{
                  d: (isHovered && !isOpen) 
                    ? ["M12,12 L24,4 A12,12 0 1,0 24,20 Z", "M12,12 L24,12 A12,12 0 1,0 24,12 Z", "M12,12 L24,4 A12,12 0 1,0 24,20 Z"]
                    : isOpen 
                      ? "M12,12 L24,4 A12,12 0 1,0 24,20 Z" // Mouth slightly open or fixed in chat mode
                      : "M12,12 L24,4 A12,12 0 1,0 24,20 Z"
                }}
                transition={{
                  repeat: (isHovered && !isOpen) ? Infinity : 0,
                  duration: 0.3
                }}
              />
            </svg>
            
            {/* Pac-Man Eye (optional but adds character) */}
            {!isOpen && (
              <div className="absolute top-1/4 left-1/2 w-1.5 h-1.5 bg-black rounded-full" style={{ transform: 'translateX(2px)' }}></div>
            )}
          </div>

          {/* Close Icon Overlay in Chat Mode */}
          {isOpen && (
            <motion.div 
               initial={{ opacity: 0, scale: 0 }}
               animate={{ opacity: 1, scale: 1 }}
               className="absolute inset-0 flex items-center justify-center"
            >
               <X className="text-intel-cyan" size={24} />
            </motion.div>
          )}
        </motion.div>

        {/* Tooltip Notification */}
        {!isOpen && !isHovered && (
          <div className="absolute -top-12 right-0 bg-pac-yellow text-slate-900 px-3 py-1 transparent rounded-lg text-[8px] font-headline font-extrabold uppercase tracking-widest animate-bounce shadow-lg after:content-[''] after:absolute after:top-full after:right-8 after:border-t-4 after:border-t-pac-yellow after:border-x-4 after:border-x-transparent">
             Insert Coin
          </div>
        )}
      </button>
    </div>
  );
}

