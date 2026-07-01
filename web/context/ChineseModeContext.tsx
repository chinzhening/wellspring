"use client"
import { createContext, useContext, useState } from "react";

type ChineseMode = "simplified" | "traditional";

interface ChineseModeContextType {
  mode: ChineseMode;
  setMode: (mode: ChineseMode) => void;
  toggleMode: () => void;
}

const ChineseModeContext = createContext<ChineseModeContextType | null>(null);

export function ChineseModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<ChineseMode>("simplified");

  const toggleMode = () => {
    setMode((prev) =>
      prev === "simplified" ? "traditional" : "simplified"
    );
  };

  return (
    <ChineseModeContext.Provider value={{ mode, setMode, toggleMode }}>
      {children}
    </ChineseModeContext.Provider>
  );
}

export function useChineseMode() {
  const context = useContext(ChineseModeContext);
  if (!context) {
    throw new Error("useChineseMode must be called within ChineseModeProvider");
  }
  return context;
}