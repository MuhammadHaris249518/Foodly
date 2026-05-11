"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

interface Meal {
  id: number;
  name: string;
  price: number;
  location: string;
  confidence: number;
  image_url: string;
}

export default function HomePage() {
  // 1. State management
  const [searchTerm, setSearchTerm] = useState("");
  const [budget, setBudget] = useState(500);
  const [meals, setMeals] = useState<Meal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch meals from backend
  useEffect(() => {
    const fetchMeals = async () => {
      setIsLoading(true);
      try {
        const query = new URLSearchParams();
        query.append('budget', budget.toString());
        if (searchTerm) query.append('search', searchTerm);

        const response = await fetch(`http://localhost:8000/api/v1/meals/?${query.toString()}`);
        if (response.ok) {
          const data = await response.json();
          setMeals(data);
        }
      } catch (error) {
        console.error('Error fetching meals:', error);
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchMeals, 300); // Debounce
    return () => clearTimeout(timer);
  }, [budget, searchTerm]);

  return (
    <main className="min-h-screen bg-[#FDFCFB] flex flex-col items-center p-6 pt-20 md:pt-32 font-[family-name:var(--font-outfit)]">

      {/* --- HERO SECTION --- */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <h1 className="text-6xl md:text-8xl font-black text-slate-900 mb-4 tracking-tighter">
          Foodly<span className="text-emerald-500">.</span>
        </h1>
        <p className="text-slate-500 text-lg md:text-xl max-w-md mx-auto">
          The north star for budget-conscious food discovery in Islamabad.
        </p>
      </motion.div>

      {/* --- SEARCH & BUDGET CONTROLS --- */}
      <div className="w-full max-w-2xl space-y-8">
        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="relative group"
        >
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="What's your budget craving?"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full h-20 pl-8 pr-40 rounded-full border border-slate-200 bg-white shadow-2xl focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 text-xl text-slate-900 transition-all duration-300 placeholder:text-slate-400"
            />
            <button className="absolute right-3 top-3 bottom-3 px-10 bg-emerald-600 text-white font-bold rounded-full hover:bg-emerald-700 transition-all active:scale-95 shadow-lg shadow-emerald-500/20">
              Search
            </button>
          </div>
        </motion.div>

        {/* Budget Slider - Compact Professional Design */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-900 p-6 md:p-8 rounded-[2rem] shadow-2xl relative overflow-hidden group"
        >
          {/* Decorative background glow */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/10 blur-[80px] rounded-full group-hover:bg-emerald-500/20 transition-all duration-700"></div>

          <div className="flex justify-between items-center mb-6 relative z-10">
            <div>
              <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 mb-1">Set Your Limit</h3>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-black text-white tracking-tighter">{budget}</span>
                <span className="text-sm font-bold text-emerald-500">PKR</span>
              </div>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-lg border border-emerald-400/20">
                Budget Optimizer
              </span>
            </div>
          </div>

          <div className="relative h-4 flex items-center">
            <input
              type="range"
              min="100"
              max="2000"
              step="50"
              value={budget}
              onChange={(e) => setBudget(parseInt(e.target.value))}
              className="w-full h-1 bg-slate-800 rounded-full appearance-none cursor-pointer accent-emerald-500"
            />
          </div>

          <div className="flex justify-between mt-4 text-[9px] font-bold text-slate-600 uppercase tracking-widest">
            <span>Economy</span>
            <span>Balanced</span>
            <span>Premium</span>
          </div>
        </motion.div>
      </div>

      {/* --- RESULTS GRID --- */}
      <div className="w-full max-w-5xl mt-20">
        <div className="flex items-center justify-between mb-8 px-4">
          <h2 className="text-2xl font-bold text-slate-900">Best matches for you</h2>
          <span className="text-sm text-slate-400">{isLoading ? "Loading..." : `${meals.length} results found`}</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6 pb-20">
          <AnimatePresence>
            {!isLoading && meals.map((meal) => (
              <Link href={`/meals/${meal.id}`} key={meal.id} className="block group">
                <motion.div
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  whileHover={{ y: -5 }}
                  className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm hover:shadow-2xl transition-all duration-500 flex items-center gap-6 overflow-hidden"
                >
                  <div className="w-24 h-24 bg-slate-100 rounded-3xl flex items-center justify-center overflow-hidden flex-shrink-0 relative group-hover:scale-105 transition-transform duration-500">
                    {meal.image_url ? (
                      <img src={meal.image_url} alt={meal.name} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-4xl">🍽️</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-1">
                      <h3 className="text-xl font-bold text-slate-800">{meal.name}</h3>
                      <span className="text-lg font-black text-emerald-600">{meal.price} <span className="text-[10px] font-bold">PKR</span></span>
                    </div>
                    <p className="text-slate-400 text-sm mb-3">{meal.location}</p>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-emerald-500"></div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{meal.confidence}% confidence</span>
                    </div>
                  </div>
                </motion.div>
              </Link>
            ))}
          </AnimatePresence>
        </div>

        {!isLoading && meals.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20 bg-slate-50 rounded-[3rem] border-2 border-dashed border-slate-200"
          >
            <p className="text-slate-400 font-medium text-lg">No meals found under {budget} PKR. Try increasing your budget!</p>
          </motion.div>
        )}
      </div>

    </main>
  );
}
