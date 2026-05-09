import type { Metadata } from "next";
import { Fraunces, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "react-hot-toast";

const fraunces = Fraunces({ 
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-fraunces"
});

const dmSans = DM_Sans({ 
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-dm-sans"
});

const jetBrainsMono = JetBrains_Mono({ 
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono"
});

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
    <html lang="en" className={`${fraunces.variable} ${dmSans.variable} ${jetBrainsMono.variable}`}>
      <body className="bg-cream-50 font-body antialiased">
        <div className="flex h-screen overflow-hidden">
          {children}
        </div>
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
