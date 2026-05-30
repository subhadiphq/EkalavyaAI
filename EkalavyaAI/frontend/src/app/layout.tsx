import type { Metadata, Viewport } from "next";
import { Inter, Caveat } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/layout/Providers";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const caveat = Caveat({ subsets: ["latin"], variable: "--font-caveat" });

export const metadata: Metadata = {
  title: "EkalavyaAI — Learn Like a Topper",
  description:
    "India's first AI Education OS for CA Foundation, CA Intermediate, CA Final, JEE & NEET students. 7 AI agents generate premium exam-quality notes.",
  keywords: ["CA Foundation", "JEE preparation", "NEET", "AI study", "exam notes"],
  authors: [{ name: "EkalavyaAI" }],
  openGraph: {
    title: "EkalavyaAI — Learn Like a Topper",
    description: "AI-powered exam preparation for CA, JEE & NEET students",
    type: "website",
    url: "https://ekalavya.ai",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#1e40af",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${caveat.variable}`}>
      <body className="font-inter bg-white antialiased">
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
