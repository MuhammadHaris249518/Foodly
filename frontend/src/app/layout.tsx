import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";
import Navbar from "../components/Navbar";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  weight: ["400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "Foodly — Budget Food Discovery in Islamabad",
  description:
    "Discover nearby, affordable meals with live price updates, GPS filtering, and community trust signals. Powered by AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${outfit.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#FAFAF9] text-slate-900">
        <Navbar />
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}
