"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/", label: "Discover" },
  { href: "/saved", label: "Saved" },
  { href: "/profile", label: "Profile" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-100 bg-[#FAFAF9]/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <Link
          href="/"
          className="text-xl font-black tracking-tighter text-slate-900 hover:text-emerald-600 transition-colors"
        >
          Foodly<span className="text-emerald-500">.</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-all ${
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                {link.label}
              </Link>
            );
          })}

          <div className="ml-3 h-4 w-px bg-slate-200" />

          <Link
            href="/admin"
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-all ${
              pathname === "/admin"
                ? "bg-emerald-600 text-white"
                : "text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            }`}
          >
            Admin
          </Link>
        </div>
      </nav>
    </header>
  );
}
