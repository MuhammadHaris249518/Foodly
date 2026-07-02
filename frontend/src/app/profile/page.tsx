"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import type { Meal, ProfileStats } from "../../lib/types";
import { apiUrl } from "../../lib/api";


const STAT_CARDS = (stats: ProfileStats, savedCount: number) => [
  { label: "Saved Meals", value: stats.saved_count ?? savedCount, color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-100" },
  { label: "Reports Submitted", value: stats.report_count ?? 0, color: "text-slate-700", bg: "bg-slate-50 border-slate-100" },
];

export default function ProfilePage() {
  const [savedMeals, setSavedMeals] = useState<Meal[]>([]);
  const [profile, setProfile] = useState<ProfileStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const token = window.localStorage.getItem("authToken");
        if (token) {
          setIsAuthed(true);
          const [profileRes, savedRes] = await Promise.all([
            fetch(apiUrl("/api/v1/users/me/profile"), { headers: { Authorization: `Bearer ${token}` } }),
            fetch(apiUrl("/api/v1/users/me/saved"), { headers: { Authorization: `Bearer ${token}` } }),
          ]);
          if (profileRes.ok) setProfile(await profileRes.json());
          if (savedRes.ok) setSavedMeals(await savedRes.json());
          return;
        }
        const local: Meal[] = JSON.parse(window.localStorage.getItem("savedMeals") || "[]");
        setSavedMeals(local);
        setProfile({ email: "Guest User", saved_count: local.length, report_count: 0 });
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  return (
    <main className="min-h-screen bg-[#FAFAF9] font-(family-name:--font-outfit)">
      <div className="mx-auto max-w-5xl px-6 py-10">
        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-slate-100 rounded-2xl shadow-sm overflow-hidden mb-8"
        >
          {/* Top banner */}
          <div className="h-20 bg-linear-to-r from-emerald-500 to-teal-500" />

          <div className="px-6 pb-6 -mt-8">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-2xl bg-white border-4 border-white shadow-md flex items-center justify-center text-2xl mb-3">
              👤
            </div>

            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                  {isLoading ? "Loading…" : profile?.email ?? "Guest User"}
                </h1>
                {!isAuthed && (
                  <span className="inline-block mt-1 text-[10px] font-bold uppercase tracking-widest text-amber-600 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full">
                    Guest · local saves only
                  </span>
                )}
                {isAuthed && (
                  <span className="inline-block mt-1 text-[10px] font-bold uppercase tracking-widest text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">
                    Verified Member
                  </span>
                )}
              </div>

              {/* Stats */}
              {profile && (
                <div className="flex gap-3">
                  {STAT_CARDS(profile, savedMeals.length).map((s) => (
                    <div key={s.label} className={`border rounded-xl px-4 py-3 text-center ${s.bg}`}>
                      <p className={`text-2xl font-black ${s.color}`}>{isLoading ? "—" : s.value}</p>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mt-0.5">{s.label}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Saved meals section */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-black text-slate-900">Saved Meals</h2>
          <Link href="/saved" className="text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition-colors">
            View all →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {!isLoading &&
            savedMeals.slice(0, 6).map((meal, i) => (
              <motion.div
                key={meal.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Link href={`/meals/${meal.id}`} className="block group">
                  <div className="bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden flex">
                    <div className="w-24 h-24 bg-slate-50 shrink-0 overflow-hidden">
                      {meal.image_url ? (
                        <img src={meal.image_url} alt={meal.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-2xl">🍽️</div>
                      )}
                    </div>
                    <div className="flex-1 p-3 flex flex-col justify-center min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-bold text-slate-900 text-sm truncate">{meal.name}</h3>
                        <span className="font-black text-emerald-600 text-sm whitespace-nowrap shrink-0">
                          {meal.price.toLocaleString()} <span className="text-[9px]">PKR</span>
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 truncate">{meal.location}</p>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
        </div>

        {/* Skeleton */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white border border-slate-100 rounded-2xl h-24 animate-pulse" />
            ))}
          </div>
        )}

        {!isLoading && savedMeals.length === 0 && (
          <div className="text-center py-14 bg-white rounded-2xl border border-dashed border-slate-200">
            <div className="text-3xl mb-3">⭐</div>
            <p className="text-slate-600 font-semibold">No saved meals yet</p>
            <Link href="/" className="inline-block mt-4 text-sm font-bold text-emerald-600 hover:text-emerald-700">
              Start discovering →
            </Link>
          </div>
        )}

        {/* Login prompt for guests */}
        {!isAuthed && !isLoading && (
          <div className="mt-8 bg-slate-900 rounded-2xl px-6 py-5 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-bold text-white">Sign in to sync across devices</p>
              <p className="text-xs text-slate-400 mt-0.5">Your saves and reports follow you everywhere</p>
            </div>
            <Link
              href="/auth/login"
              className="shrink-0 bg-emerald-500 text-white text-sm font-bold px-4 py-2 rounded-xl hover:bg-emerald-600 transition-colors"
            >
              Sign In
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}
