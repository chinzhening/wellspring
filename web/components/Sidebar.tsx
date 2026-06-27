import Link from "next/link";

import { Home, FileText } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="
      sticky top-0
      w-64 h-screen border-r-border bg-white"
    >
      <div className="p-6 text-xl font-bold">Wellspring</div>

      <nav className="px-3 space-y-1">
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