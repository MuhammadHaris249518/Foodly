"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import type { Meal } from "../../lib/types";
import { apiUrl, CONFIDENCE_COLOR } from "../../lib/api";

export default function SavedMealsPage() {
  const [savedMeals, setSavedMeals] = useState<Meal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const token = window.localStorage.getItem("authToken");
        if (token) {
          const res = await fetch(apiUrl("/api/v1/users/me/saved"), {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (res.ok) { setSavedMeals(await res.json()); return; }
        }
        const raw = window.localStorage.getItem("savedMeals");
        setSavedMeals(raw ? JSON.parse(raw) : []);
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const removeSaved = async (id: number) => {
    const token = window.localStorage.getItem("authToken");
    if (token) {
      try {
        await fetch(apiUrl(`/api/v1/meals/${id}/save`), {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // best-effort — still remove from local state
      }
    }
    const updated = savedMeals.filter((m) => m.id !== id);
    setSavedMeals(updated);
    window.localStorage.setItem("savedMeals", JSON.stringify(updated));
  };

  return (
    <main className="min-h-screen bg-[#FAFAF9] font-(family-name:--font-outfit)">
      <div className="mx-auto max-w-5xl px-6 py-10">
        {/* Header */}
        <div className="flex items-end justify-between mb-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Your Collection</p>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Saved Meals</h1>
          </div>
          <span className="text-sm font-medium text-slate-400">
            {isLoading ? "Loading…" : `${savedMeals.length} saved`}
          </span>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AnimatePresence mode="popLayout">
            {!isLoading &&
              savedMeals.map((meal, i) => (
                <motion.div
                  key={meal.id}
                  layout
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <Link href={`/meals/${meal.id}`} className="block group">
                    <div className="bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden flex">
                      {/* Thumbnail */}
                      <div className="w-28 h-28 bg-slate-50 shrink-0 overflow-hidden">
                        {meal.image_url ? (
                          <img
                            src={meal.image_url}
                            alt={meal.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-3xl">🍽️</div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="flex-1 p-4 flex flex-col justify-between min-w-0">
                        <div>
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="font-bold text-slate-900 text-sm leading-snug truncate">{meal.name}</h3>
                            <span className="font-black text-emerald-600 text-sm whitespace-nowrap shrink-0">
                              {meal.price.toLocaleString()} <span className="text-[9px] font-bold text-emerald-500/70">PKR</span>
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5 truncate">{meal.location}</p>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${CONFIDENCE_COLOR(meal.confidence)}`}>
                            {meal.confidence}% verified
                          </span>
                          <button
                            onClick={(e) => { e.preventDefault(); removeSaved(meal.id); }}
                            className="text-xs text-slate-400 hover:text-rose-500 font-semibold transition-colors"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
          </AnimatePresence>
        </div>

        {/* Skeleton */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white border border-slate-100 rounded-2xl h-28 animate-pulse" />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && savedMeals.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-200"
          >
            <div className="text-4xl mb-4">⭐</div>
            <p className="text-slate-700 font-bold text-lg">No saved meals yet</p>
            <p className="text-slate-400 text-sm mt-1 mb-6">Browse meals and tap the star to save them here</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-emerald-600 text-white px-5 py-2.5 rounded-full text-sm font-bold hover:bg-emerald-700 transition-colors"
            >
              Discover meals →
            </Link>
          </motion.div>
        )}
      </div>
    </main>
  );
}
