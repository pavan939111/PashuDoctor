import type { Metadata } from "next";
import { Outfit, Inter } from "next/font/google";
import "./globals.css";
import NavRail from "@/components/NavRail";
import Navbar from "@/components/Navbar";

const outfit = Outfit({ subsets: ["latin"], variable: '--font-outfit' });
const inter = Inter({ subsets: ["latin"], variable: '--font-inter' });

export const metadata: Metadata = {
  title: "PashuDoctor | AI Livestock Health Assistant",
  description: "Advanced AI-driven health support for Indian livestock farmers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${inter.variable} font-inter antialiased bg-stone-50 text-stone-900`}>
        <div className="flex h-screen overflow-hidden">
          <NavRail />
          <div className="flex-1 flex flex-col min-w-0 relative">
            <Navbar />
            <main className="flex-1 overflow-y-auto mt-20 ml-0 lg:ml-0">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
