import Link from "next/link";

import { FileText, Home } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="
      sticky top-0
      w-full lg:w-64
      h-16 lg:h-screen
      flex lg:flex-col
      items-center lg:items-start
      gap-3
      z-50
    bg-surface
      shadow-sm lg:shadow-none lg:border-r lg:border-border"
    >
      <Link
          href="/"
          className="flex items-center"
        >
          <div className="hidden lg:block p-4 text-xl font-bold">Wellspring</div>
          <span className="lg:hidden p-4">
            <Home size={20}/>
          </span>    
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
    </aside>
  );
}