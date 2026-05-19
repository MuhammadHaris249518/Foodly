"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface Meal {
  id: number;
  name: string;
  price: number;
  location: string;
  confidence: number;
  image_url: string;
}

export default function SavedMealsPage() {
  const [savedMeals, setSavedMeals] = useState<Meal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadSaved = async () => {
      setIsLoading(true);
      try {
        const token = window.localStorage.getItem("authToken");
        if (token) {
          const res = await fetch("http://localhost:8000/api/v1/users/me/saved", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (res.ok) {
            const data = await res.json();
            setSavedMeals(data);
            setIsLoading(false);
            return;
          }
        }

        const raw = window.localStorage.getItem("savedMeals");
        setSavedMeals(raw ? JSON.parse(raw) : []);
      } catch (error) {
        console.error("Failed to load saved meals", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSaved();
  }, []);

  return (
    <main className="min-h-screen bg-[#FDFCFB] p-6 pt-20 md:pt-28 font-[family-name:var(--font-outfit)]">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-emerald-600 font-bold">
            ← Back to search
          </Link>
          <Link href="/profile" className="text-slate-400 hover:text-slate-600 text-sm font-semibold">
            Profile
          </Link>
        </div>

        <div className="mt-8 flex items-center justify-between">
          <h1 className="text-3xl font-black text-slate-900">Saved meals</h1>
          <span className="text-sm text-slate-400">
            {isLoading ? "Loading..." : `${savedMeals.length} saved`}
          </span>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {!isLoading && savedMeals.map((meal) => (
            <Link href={`/meals/${meal.id}`} key={meal.id} className="block group">
              <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm hover:shadow-2xl transition-all duration-500 flex items-center gap-6">
                <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center overflow-hidden">
                  {meal.image_url ? (
                    <img src={meal.image_url} alt={meal.name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-3xl">🍽️</span>
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="text-lg font-bold text-slate-800">{meal.name}</h3>
                    <span className="text-lg font-black text-emerald-600">{meal.price} <span className="text-[10px] font-bold">PKR</span></span>
                  </div>
                  <p className="text-slate-400 text-sm mb-2">{meal.location}</p>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{meal.confidence}% confidence</span>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {!isLoading && savedMeals.length === 0 && (
          <div className="mt-12 text-center py-16 bg-slate-50 rounded-[3rem] border-2 border-dashed border-slate-200">
            <p className="text-slate-400 font-medium text-lg">No saved meals yet.</p>
          </div>
        )}
      </div>
    </main>
  );
}
