"use client";

import Link from "next/link";

import { FileText, Home, Music } from "lucide-react";
import { ChineseModeToggle } from "./ChineseModeToggle";

export default function Sidebar() {
  return (
    <aside
      className="
      sticky top-0
      w-full lg:w-64
      h-16 lg:h-screen
      flex lg:flex-col
      items-center lg:items-start
      gap-1
      z-50
    bg-surface
      shadow-sm lg:shadow-none lg:border-r lg:border-border"
    >
      <Link href="/" className="items-center lg:w-full">
        <div className="hidden lg:block p-4 text-xl uppercase tracking-[0.15em]">Wellspring</div>
        <div className="block lg:hidden p-4 mx-1">
          <Home size={20} />
        </div>
      </Link>

      <nav className="text-xs flex lg:flex-col gap-1 h-full lg:h-auto lg:w-full p-2 lg:px-2 lg:border-t lg:border-border">
        <Link
          href="/songs"
          className="flex items-center gap-2 rounded-lg px-2 lg:p-2 hover:bg-gray-100"
        >
          <Music size={20} />
          <p className="uppercase tracking-[0.24em] text-muted-foreground/70">
            Songs
          </p>
        </Link>

        <Link
          href="/terms"
          className="flex items-center gap-2 rounded-lg px-2 lg:p-2 hover:bg-gray-100"
        >
          <FileText size={20} />
          <p className="uppercase tracking-[0.24em] text-muted-foreground/70">
            Terms
          </p>
        </Link>
      </nav>

      {/* Settings */}
      <div className="hidden lg:block w-full mt-3 border-t border-border pt-3">
        <h2 className="px-4 text-sm uppercase tracking-[0.2em]">Settings</h2>
        <div className="lg:h-16 px-2 lg:p-2">
          <ChineseModeToggle />
        </div>
      </div>
    </aside>
  );
}
