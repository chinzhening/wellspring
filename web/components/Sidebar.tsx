"use client";

import Link from "next/link";

import { FileText, Home } from "lucide-react";
import { ChineseModeToggle } from "./ChineseModeToggle";

export default function Sidebar() {
  return (
    <aside className="
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
      <Link
          href="/"
          className="items-center lg:w-full"
        >
          <div className="hidden lg:block p-4 text-xl font-bold">Wellspring</div>
          <div className="flex lg:hidden p-4 items-center gap-1">
            <Home size={20}/>
            <span>Home</span>
          </div>    
        </Link>
      

      <nav className="flex lg:flex-col gap-1 h-full lg:w-full px-2">
        <Link
          href="/terms"
          className="flex items-center gap-1 rounded-lg p-2 hover:bg-gray-100"
        >
          <FileText size={20} />
          Terms
        </Link>
      </nav>

      {/* Settings */}
      <div className="flex items-center lg:h-16 justify-center p-2">
        <ChineseModeToggle />
      </div>
    </aside>
  );
}