"use client";

import { motion } from "framer-motion";

export const EatableText = ({ text, className }: { text: string, className?: string }) => {
  // Split the text into words to maintain proper line wrapping/alignment
  const words = text.split(" ");
  
  return (
    <span className={`inline-block ${className || ''}`}>
      {words.map((word, wordIndex) => (
        <span key={wordIndex} className="inline-block whitespace-nowrap mr-[1em] mb-2">
          {word.split("").map((char, charIndex) => (
            <motion.span
              key={`${wordIndex}-${charIndex}`}
              whileHover={{ 
                opacity: 0, 
                scale: 0.1, 
                rotate: 180,
                transition: { duration: 0.1 } 
              }}
              transition={{ duration: 0.3, type: "spring" }} // Smooth return when hover ends
              className="cursor-crosshair inline-block"
            >
              {char}
            </motion.span>
          ))}
        </span>
      ))}
    </span>
  );
};
