import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import PageTransition from '@/components/layout/PageTransition';
import HyperspeedBackground from '@/components/layout/HyperspeedBackground';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ZeroTRUST | Multi-Agent AI Verification Hub",
  description: "Advanced multi-agent AI system for real-time claim verification, deepfake detection, and news integrity analysis.",
  icons: {
    icon: "/icon.png",
    shortcut: "/icon.png",
    apple: "/icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <HyperspeedBackground />
        <PageTransition>
          {children}
        </PageTransition>
      </body>
    </html>
  );
}
