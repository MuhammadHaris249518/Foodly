"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import dynamic from "next/dynamic";
import type { Meal, LivePriceData, LiveSearchStatus, BackendStatus } from "../lib/types";
import { apiUrl, CONFIDENCE_COLOR } from "../lib/api";

const MapPanel = dynamic(() => import("../components/MapPanel"), {
  ssr: false,
  loading: () => (
    <div className="h-[380px] w-full rounded-2xl border border-slate-100 bg-slate-50 flex items-center justify-center text-slate-400 text-sm font-medium">
      Loading map…
    </div>
  ),
});

export default function HomePage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [budget, setBudget] = useState(600);
  const [sliderBudget, setSliderBudget] = useState(600); // local display only — committed on release
  const [meals, setMeals] = useState<Meal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState({ lat: 33.6844, lng: 73.0479 });
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set());

  // Backend health state — polls until both server and database are reachable
  const [backendReady, setBackendReady] = useState(false);
  const [backendConnecting, setBackendConnecting] = useState(true);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("starting");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // AI Agent States
  const [liveSearchStatus, setLiveSearchStatus] = useState<LiveSearchStatus>("idle");
  const [liveSearchMessage, setLiveSearchMessage] = useState("");
  const [livePriceData, setLivePriceData] = useState<LivePriceData | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const raw = typeof window !== "undefined" ? window.localStorage.getItem("savedMeals") : null;
    if (raw) {
      try {
        const parsed: Meal[] = JSON.parse(raw);
        setSavedIds(new Set(parsed.map((m) => m.id)));
      } catch {}
    }
  }, []);

  // Poll the backend root every 2 s until it responds, then set backendReady.
  // This prevents the "Failed to fetch" console error that fires before uvicorn is up.
  useEffect(() => {
    let cancelled = false;

    const check = async () => {
      const abort = new AbortController();
      const timeout = setTimeout(() => abort.abort(), 1500);
      try {
        const res = await fetch(apiUrl("/health"), { signal: abort.signal });
        if (cancelled) return;
        if (res.ok) {
          // Server + database both up
          setBackendStatus("ready");
          setBackendReady(true);
          setBackendConnecting(false);
          if (pollRef.current) clearInterval(pollRef.current);
        } else if (res.status === 503) {
          // Server up but database not ready yet — keep polling, update label
          setBackendStatus("db_error");
        }
        // any other non-ok status: keep polling silently
      } catch {
        // Server not up yet — silent, keep polling
        if (!cancelled) setBackendStatus("starting");
      } finally {
        clearTimeout(timeout);
      }
    };

    check();
    pollRef.current = setInterval(check, 2000);

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  useEffect(() => {
    if (!backendReady) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const nearbyQ = new URLSearchParams({
          budget: budget.toString(),
          lat: selectedLocation.lat.toString(),
          lng: selectedLocation.lng.toString(),
          radius_km: "3",
          ...(searchTerm ? { search: searchTerm } : {}),
        });

        let res = await fetch(`${apiUrl("/api/v1/meals/nearby")}?${nearbyQ}`, {
          signal: controller.signal,
        });
        if (!res.ok) {
          const baseQ = new URLSearchParams({ budget: budget.toString(), ...(searchTerm ? { search: searchTerm } : {}) });
          res = await fetch(`${apiUrl("/api/v1/meals/")}?${baseQ}`, { signal: controller.signal });
        }
        if (res.ok) setMeals(await res.json());

        // Stop any previous running agent connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }

        // Trigger AI Agent Search if there's a search term
        if (searchTerm) {
          setLiveSearchStatus("starting");
          setLiveSearchMessage("Connecting to AI agent...");
          setLivePriceData(null);
          
          const es = new EventSource(`${apiUrl("/api/v1/agent/live-price")}?query=${encodeURIComponent(searchTerm)}`);
          eventSourceRef.current = es;

          es.onmessage = (event) => {
              const data = JSON.parse(event.data);
              
              if (data.status === "searching" || data.status === "extracting" || data.status === "starting") {
                 setLiveSearchStatus(data.status);
                 setLiveSearchMessage(data.message);
              } else if (data.status === "complete") {
                 setLiveSearchStatus("complete");
                 setLivePriceData(data.data);
                 es.close();
              } else if (data.status === "failed" || data.status === "error") {
                 setLiveSearchStatus("failed");
                 setLiveSearchMessage(data.message);
                 es.close();
              }
          };

          es.onerror = (err) => {
              console.error("SSE Error:", err);
              setLiveSearchStatus("failed");
              setLiveSearchMessage("Connection to AI agent lost.");
              es.close();
          };
        } else {
          setLiveSearchStatus("idle");
          setLivePriceData(null);
        }

      } catch (e: unknown) {
        if ((e as Error).name !== "AbortError") console.error(e);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(timer);
      controller.abort();
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [budget, searchTerm, selectedLocation, backendReady]);

  const toggleSave = async (meal: Meal, e: React.MouseEvent) => {
    e.preventDefault();
    const token = typeof window !== "undefined" ? window.localStorage.getItem("authToken") : null;
    const next = new Set(savedIds);

    if (savedIds.has(meal.id)) {
      next.delete(meal.id);
    } else {
      next.add(meal.id);
      if (token) {
        fetch(`${apiUrl(`/api/v1/meals/${meal.id}/save`)}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }).catch(console.error);
      }
    }

    setSavedIds(next);
    const allSaved: Meal[] = JSON.parse(window.localStorage.getItem("savedMeals") || "[]");
    const updated = next.has(meal.id)
      ? [...allSaved.filter((m) => m.id !== meal.id), meal]
      : allSaved.filter((m) => m.id !== meal.id);
    window.localStorage.setItem("savedMeals", JSON.stringify(updated));
  };

  return (
    <main className="min-h-screen bg-[#FAFAF9] font-[family-name:var(--font-outfit)]">

      {/* Backend status pill — auto-hides once server + database are ready */}
      <AnimatePresence>
        {backendConnecting && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 24 }}
            transition={{ duration: 0.3 }}
            className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2.5 px-5 py-2.5 rounded-full text-sm font-semibold shadow-2xl pointer-events-none ${
              backendStatus === "db_error"
                ? "bg-rose-600 text-white"
                : "bg-slate-900 text-white"
            }`}
          >
            <span className="relative flex h-2.5 w-2.5">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${backendStatus === "db_error" ? "bg-rose-300" : "bg-amber-400"}`} />
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${backendStatus === "db_error" ? "bg-rose-300" : "bg-amber-400"}`} />
            </span>
            {backendStatus === "db_error"
              ? "Database unavailable — is PostgreSQL running?"
              : "Backend starting…"}
          </motion.div>
        )}
      </AnimatePresence>
      {/* HERO */}
      <section className="mx-auto max-w-6xl px-6 pt-16 pb-12">
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <span className="inline-block mb-4 rounded-full bg-emerald-50 border border-emerald-100 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-emerald-700">
            Islamabad &amp; Rawalpindi
          </span>
          <h1 className="text-5xl md:text-7xl font-black text-slate-900 tracking-tighter mb-4">
            Find food that fits<br />
            <span className="text-emerald-500">your budget.</span>
          </h1>
          <p className="text-slate-500 text-base md:text-lg max-w-xl mx-auto">
            Live prices, AI-verified confidence scores, and community-driven updates — all within your budget.
          </p>
        </motion.div>

        {/* SEARCH + BUDGET */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="mt-10 max-w-2xl mx-auto space-y-4"
        >
          {/* Search */}
          <div className="relative flex items-center shadow-lg shadow-slate-200/60 rounded-2xl">
            <svg className="absolute left-5 w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search meals, restaurants…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full h-14 pl-14 pr-36 rounded-2xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400 text-base text-slate-900 placeholder:text-slate-400 transition-all"
            />
            <button className="absolute right-2 h-10 px-6 bg-emerald-600 text-white text-sm font-bold rounded-xl hover:bg-emerald-700 transition-all active:scale-95">
              Search
            </button>
          </div>

          {/* Budget Slider */}
          <div className="bg-slate-900 rounded-2xl px-6 py-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 mb-0.5">Max Budget</p>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-black text-white">{sliderBudget.toLocaleString()}</span>
                  <span className="text-xs font-bold text-emerald-400">PKR</span>
                </div>
              </div>
              <div className="flex gap-2">
                {[200, 500, 1000, 2000].map((v) => (
                  <button
                    key={v}
                    onClick={() => { setBudget(v); setSliderBudget(v); }}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg transition-all ${
                      sliderBudget === v ? "bg-emerald-500 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
            <input
              type="range"
              min="100"
              max="2000"
              step="50"
              value={sliderBudget}
              onChange={(e) => setSliderBudget(parseInt(e.target.value))}
              onMouseUp={(e) => setBudget(parseInt((e.target as HTMLInputElement).value))}
              onTouchEnd={(e) => setBudget(parseInt((e.target as HTMLInputElement).value))}
              className="w-full bg-slate-700"
              style={{ accentColor: "#10b981" }}
            />
            <div className="flex justify-between mt-2 text-[9px] font-bold uppercase tracking-widest text-slate-600">
              <span>Economy · 100</span>
              <span>Premium · 2000</span>
            </div>
          </div>
        </motion.div>
      </section>

      {/* MAP + RESULTS */}
      <section className="mx-auto max-w-6xl px-6 pb-24 space-y-10">
        {/* Map */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-bold text-slate-700">Pick a location</h2>
            <span className="text-xs text-slate-400 font-mono">
              {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
            </span>
          </div>
          <MapPanel
            selected={selectedLocation}
            onSelect={(coords) => setSelectedLocation(coords)}
          />
        </div>

        {/* AI Agent Live Web Results */}
        {searchTerm && liveSearchStatus !== "idle" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 shadow-sm"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="flex h-3 w-3 relative">
                {liveSearchStatus !== "complete" && liveSearchStatus !== "failed" && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex rounded-full h-3 w-3 ${liveSearchStatus === "complete" ? "bg-emerald-500" : liveSearchStatus === "failed" ? "bg-rose-500" : "bg-indigo-500"}`}></span>
              </span>
              <h3 className="font-bold text-indigo-900 flex-1">Live Web Intelligence</h3>
            </div>
            
            {liveSearchStatus !== "complete" && liveSearchStatus !== "failed" && (
              <p className="text-sm font-medium text-indigo-700 ml-6 animate-pulse">
                {liveSearchMessage}
              </p>
            )}

            {liveSearchStatus === "failed" && (
              <p className="text-sm font-medium text-rose-600 ml-6">
                {liveSearchMessage}
              </p>
            )}

            {liveSearchStatus === "complete" && livePriceData && (
              <div className="ml-6 mt-3 bg-white p-4 rounded-xl border border-indigo-100/50 shadow-sm flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-widest text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-md">Found on Web</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${CONFIDENCE_COLOR(livePriceData.confidence)}`}>
                        {livePriceData.confidence}% verified
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900">{livePriceData.restaurant}</h4>
                  <p className="text-sm font-medium text-slate-500">{livePriceData.meal}</p>
                </div>
                <div className="text-right">
                  <span className="font-black text-emerald-600 text-2xl">
                    {livePriceData.price_pkr.toLocaleString()}
                  </span>
                  <span className="text-xs font-bold text-emerald-500/70 ml-1">PKR</span>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Results header */}
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black text-slate-900">
            {backendStatus === "db_error" ? "Database unavailable" : backendConnecting ? "Waiting for backend…" : isLoading ? "Finding meals…" : `${meals.length} meals found`}
          </h2>
          <span className="text-xs text-slate-400 font-medium">within 3 km · under {budget} PKR</span>
        </div>

        {/* Meal Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          <AnimatePresence mode="popLayout">
            {!isLoading &&
              meals.map((meal, i) => (
                <Link href={`/meals/${meal.id}`} key={meal.id} className="block group">
                  <motion.div
                    layout
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: i * 0.04 }}
                    whileHover={{ y: -4 }}
                    className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300"
                  >
                    {/* Image */}
                    <div className="relative h-40 bg-slate-50 overflow-hidden">
                      {meal.image_url ? (
                        <img
                          src={meal.image_url}
                          alt={meal.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-5xl">🍽️</div>
                      )}
                      {/* Save button */}
                      <button
                        onClick={(e) => toggleSave(meal, e)}
                        className={`absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all shadow-md ${
                          savedIds.has(meal.id)
                            ? "bg-emerald-600 text-white"
                            : "bg-white/90 text-slate-500 hover:bg-white hover:text-emerald-600"
                        }`}
                      >
                        {savedIds.has(meal.id) ? "★" : "☆"}
                      </button>
                      {/* Confidence badge */}
                      <span className={`absolute bottom-3 left-3 text-[10px] font-bold px-2 py-0.5 rounded-full ${CONFIDENCE_COLOR(meal.confidence)}`}>
                        {meal.confidence}% verified
                      </span>
                    </div>

                    {/* Info */}
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-bold text-slate-900 text-base leading-snug">{meal.name}</h3>
                        <span className="font-black text-emerald-600 text-base whitespace-nowrap">
                          {meal.price.toLocaleString()} <span className="text-[9px] font-bold text-emerald-500/70">PKR</span>
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-400 font-medium truncate">{meal.location}</p>
                    </div>
                  </motion.div>
                </Link>
              ))}
          </AnimatePresence>
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm animate-pulse">
                <div className="h-40 bg-slate-100" />
                <div className="p-4 space-y-2">
                  <div className="h-4 bg-slate-100 rounded w-3/4" />
                  <div className="h-3 bg-slate-100 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && meals.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-200"
          >
            <div className="text-4xl mb-4">🔍</div>
            <p className="text-slate-600 font-semibold text-lg">No meals found</p>
            <p className="text-slate-400 text-sm mt-1">Try increasing your budget or moving the map</p>
          </motion.div>
        )}
      </section>
    </main>
  );
}
