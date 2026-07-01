import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { ChineseModeProvider } from "@/context/ChineseModeContext";

export const metadata: Metadata = {
  title: "Wellspring",
  description: "A collection of Chinese songs and terms for learning and reference.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="antialiased"
    >
      <body>
        <ChineseModeProvider>
          <div className="flex flex-col lg:flex-row min-h-dvh">
            <Sidebar />
            <main className="flex-1 min-w-0">{children}</main>
          </div>
        </ChineseModeProvider>
      </body>
    </html>
  );
}
