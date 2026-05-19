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

interface ProfileStats {
  email: string;
  saved_count: number;
  report_count: number;
}

export default function ProfilePage() {
  const [savedMeals, setSavedMeals] = useState<Meal[]>([]);
  const [profile, setProfile] = useState<ProfileStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);

  const loadLocalSaved = () => {
    if (typeof window === "undefined") return [] as Meal[];
    const raw = window.localStorage.getItem("savedMeals");
    if (!raw) return [] as Meal[];
    try {
      return JSON.parse(raw) as Meal[];
    } catch {
      return [] as Meal[];
    }
  };

  useEffect(() => {
    const loadProfile = async () => {
      setIsLoading(true);
      try {
        const token = window.localStorage.getItem("authToken");
        if (token) {
          setIsAuthed(true);
          const [profileRes, savedRes] = await Promise.all([
            fetch("http://localhost:8000/api/v1/users/me/profile", {
              headers: { Authorization: `Bearer ${token}` },
            }),
            fetch("http://localhost:8000/api/v1/users/me/saved", {
              headers: { Authorization: `Bearer ${token}` },
            }),
          ]);

          if (profileRes.ok) {
            const profileData = await profileRes.json();
            setProfile(profileData);
          }

          if (savedRes.ok) {
            const savedData = await savedRes.json();
            setSavedMeals(savedData);
          }
          return;
        }

        const localSaved = loadLocalSaved();
        setSavedMeals(localSaved);
        setProfile({
          email: "Guest",
          saved_count: localSaved.length,
          report_count: 0,
        });
      } catch (error) {
        console.error("Failed to load profile", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  return (
    <main className="min-h-screen bg-[#FDFCFB] p-6 pt-20 md:pt-28 font-[family-name:var(--font-outfit)]">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-emerald-600 font-bold">
            ← Back to search
          </Link>
          <Link href="/saved" className="text-slate-400 hover:text-slate-600 text-sm font-semibold">
            Saved meals
          </Link>
        </div>

        <div className="mt-8 bg-white border border-slate-100 rounded-[2rem] p-6 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-black text-slate-900">Profile</h1>
              <p className="text-sm text-slate-500 mt-1">
                {profile?.email || "Loading..."}
                {!isAuthed && " (local)"}
              </p>
            </div>
            <div className="flex gap-4">
              <div className="bg-emerald-50 border border-emerald-100 px-4 py-3 rounded-2xl">
                <p className="text-[10px] uppercase tracking-wider text-emerald-600 font-bold">Saved</p>
                <p className="text-2xl font-black text-emerald-700">
                  {isLoading ? "—" : profile?.saved_count ?? 0}
                </p>
              </div>
              <div className="bg-slate-50 border border-slate-100 px-4 py-3 rounded-2xl">
                <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Reports</p>
                <p className="text-2xl font-black text-slate-700">
                  {isLoading ? "—" : profile?.report_count ?? 0}
                </p>
              </div>
            </div>
          </div>

          {!isAuthed && (
            <div className="mt-4 text-xs text-slate-400">
              You are viewing local saves. Log in to see your verified profile stats.
            </div>
          )}
        </div>

        <div className="mt-10 flex items-center justify-between">
          <h2 className="text-2xl font-black text-slate-900">Saved meals</h2>
          <span className="text-sm text-slate-400">
            {isLoading ? "Loading..." : `${savedMeals.length} saved`}
          </span>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
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
                    <span className="text-lg font-black text-emerald-600">
                      {meal.price} <span className="text-[10px] font-bold">PKR</span>
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm mb-2">{meal.location}</p>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {meal.confidence}% confidence
                  </span>
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
