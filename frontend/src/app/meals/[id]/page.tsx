import React from 'react';
import Link from 'next/link';

export default async function MealDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  // Fetch real data from our new FastAPI endpoint
  const res = await fetch(`http://localhost:8000/api/v1/meals/${id}`, {
    cache: 'no-store' // We want live data
  });
  
  if (!res.ok) {
    return (
      <main className="min-h-screen bg-linear-to-br from-slate-900 to-slate-800 flex items-center justify-center p-6 text-white font-[family-name:var(--font-outfit)]">
        <h1>Meal not found</h1>
        <Link href="/" className="ml-4 text-emerald-400">Go back</Link>
      </main>
    );
  }
  
  const data = await res.json();
  const meal = data.meal;
  const priceHistory = data.price_history;
  
  return (
    <main className="min-h-screen bg-linear-to-br from-slate-900 to-slate-800 flex items-center justify-center p-6 font-[family-name:var(--font-outfit)]">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Dynamic Background elements for Glassmorphism contrast */}
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/20 blur-[100px] rounded-full"></div>
        <div className="absolute top-1/2 left-10 w-72 h-72 bg-blue-500/20 blur-[100px] rounded-full"></div>
      </div>

      <div className="relative w-full max-w-4xl">
        <Link href="/" className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium mb-8 transition-colors">
          <span>&larr;</span> Back to Search
        </Link>
        
        {/* GLASSMORPHISM CARD */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl rounded-[3rem] p-8 md:p-12 overflow-hidden relative">
          
          <div className="flex flex-col md:flex-row gap-10 relative z-10">
            {/* Image */}
            <div className="w-full md:w-1/2 h-64 md:h-auto bg-white/5 border border-white/10 rounded-4xl flex items-center justify-center overflow-hidden">
               {meal.image_url ? (
                 <img src={meal.image_url} alt={meal.name} className="w-full h-full object-cover" />
               ) : (
                 <div className="text-6xl">🍽️</div>
               )}
            </div>

            {/* Content Area */}
            <div className="w-full md:w-1/2 flex flex-col justify-center">
              <div className="mb-2">
                <span className="inline-block px-3 py-1 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-bold tracking-widest uppercase rounded-full">
                  Meal #{id}
                </span>
              </div>
              
              <h1 className="text-4xl md:text-5xl font-black text-white mb-4 tracking-tight">
                {meal.name}
              </h1>
              
              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-5xl font-black text-emerald-400">{meal.price}</span>
                <span className="text-lg font-bold text-emerald-500/70 uppercase">PKR</span>
              </div>

              <div className="space-y-4 mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center border border-white/10 shrink-0">
                     📍
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Location</p>
                    <p className="text-white font-medium">{meal.location}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center border border-white/10 shrink-0">
                     ✨
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Confidence Score</p>
                    <p className="text-white font-medium">{meal.confidence}%</p>
                  </div>
                </div>
              </div>
              
              {/* Simulated Price History Display */}
              <div className="bg-slate-900/50 rounded-2xl p-4 border border-white/5 mb-6">
                <h3 className="text-emerald-400 text-sm font-bold uppercase tracking-wider mb-3">Price History (6 Months)</h3>
                <div className="flex justify-between items-end h-16 gap-1">
                  {priceHistory.map((hist: { month: string; price: number }, index: number) => {
                    // Calculate height percentage based on max price to make a tiny bar chart
                    const maxPrice = Math.max(...priceHistory.map((h: { price: number }) => h.price));
                    const heightPercent = (hist.price / maxPrice) * 100;
                    
                    return (
                      <div key={index} className="flex flex-col items-center flex-1 group relative">
                        {/* Tooltip on hover */}
                        <div className="opacity-0 group-hover:opacity-100 absolute -top-8 text-xs bg-white text-slate-900 px-2 py-1 rounded font-bold transition-opacity whitespace-nowrap z-20 pointer-events-none">
                          {hist.price} PKR
                        </div>
                        <div 
                          className={`w-full max-w-6 rounded-t-sm transition-all duration-300 ${index === priceHistory.length - 1 ? 'bg-emerald-400' : 'bg-slate-600 hover:bg-slate-500'}`}
                          style={{ height: `${heightPercent}%` }}
                        ></div>
                        <span className="text-[8px] text-slate-400 mt-1 uppercase rotate-0">{hist.month.split(' ')[0]}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* AI Insight Display */}
              {data.ai_insight && (
                <div className="relative overflow-hidden rounded-2xl p-[1px] group">
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500 rounded-2xl opacity-75 animate-gradient-xy group-hover:opacity-100 transition-opacity duration-1000"></div>
                  <div className="relative bg-slate-900 rounded-2xl p-5 border border-white/5">
                    <div className="flex items-start gap-4 text-emerald-100 relative">
                      {/* Sparkle icon */}
                      <span className="text-xl animate-pulse whitespace-nowrap drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]">✨</span>
                      <p className="text-sm font-medium leading-relaxed">
                        {data.ai_insight}
                      </p>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </main>
  );
}