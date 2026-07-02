import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
}

export function GlassCard({ children, className = "" }: GlassCardProps) {
  return (
    <section
      className={`relative overflow-hidden rounded-4xl border border-white/15 bg-surface/55 shadow-[0_24px_80px_rgba(0,0,0,0.12)] backdrop-blur-3xl ${className}`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.30),transparent_34%),radial-gradient(circle_at_85%_15%,rgba(255,255,255,0.16),transparent_30%),radial-gradient(circle_at_bottom,rgba(255,255,255,0.10),transparent_42%)]" />
      <div className="pointer-events-none absolute -left-24 top-8 h-56 w-56 rounded-full bg-white/20 blur-3xl" />
      <div className="pointer-events-none absolute -right-20 bottom-0 h-64 w-64 rounded-full bg-cyan-400/12 blur-3xl" />

      <div className="relative z-10 h-full w-full">{children}</div>
    </section>
  );
}