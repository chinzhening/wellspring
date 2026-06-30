import Link from "next/link";

import { Home, FileText } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="
      sticky top-0
      w-screen lg:w-64
      h-16 lg:h-screen
      flex lg:flex-col
      items-center lg:items-start
      gap-4
      z-100
      border-r-border bg-white"
    >
      <div className="p-6 text-xl font-bold">Wellspring</div>

      <nav className="flex lg:flex-col px-3">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-lg px-4 py-3 hover:bg-gray-100"
        >
          <Home size={20} />
          Home
        </Link>

        <Link
          href="/terms"
          className="flex items-center gap-3 rounded-lg px-4 py-3 hover:bg-gray-100"
        >
          <FileText size={20} />
          Terms
        </Link>
      </nav>
    </aside>
  );
}