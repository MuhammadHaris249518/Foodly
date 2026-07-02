import Link from "next/link";
import { apiUrl } from "../../../lib/api";

export default async function MealDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  const res = await fetch(apiUrl(`/api/v1/meals/${id}`), { cache: "no-store" });

  if (!res.ok) {
    return (
      <main className="min-h-screen bg-[#FAFAF9] flex items-center justify-center p-6">
        <div className="text-center">
          <div className="text-5xl mb-4">🍽️</div>
          <h1 className="text-2xl font-black text-slate-900 mb-2">Meal not found</h1>
          <p className="text-slate-500 mb-6">This meal may have been removed or the link is invalid.</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-emerald-600 text-white px-6 py-2.5 rounded-full font-bold hover:bg-emerald-700 transition-colors"
          >
            ← Back to search
          </Link>
        </div>
      </main>
    );
  }

  const data = await res.json();
  const meal = data.meal;
  const priceHistory: { month: string; price: number }[] = data.price_history ?? [];
  const maxPrice = priceHistory.length ? Math.max(...priceHistory.map((h) => h.price)) : 1;

  const confidenceColor =
    meal.confidence >= 80
      ? { bg: "bg-emerald-50", border: "border-emerald-100", text: "text-emerald-700", dot: "bg-emerald-500" }
      : meal.confidence >= 50
      ? { bg: "bg-amber-50", border: "border-amber-100", text: "text-amber-700", dot: "bg-amber-400" }
      : { bg: "bg-rose-50", border: "border-rose-100", text: "text-rose-700", dot: "bg-rose-500" };

  return (
    <main className="min-h-screen bg-[#FAFAF9] font-(family-name:--font-outfit)">
      <div className="mx-auto max-w-5xl px-6 py-10">
        {/* Breadcrumb */}
        <div className="flex items-center gap-3 mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-emerald-600 transition-colors"
          >
            ← Discover
          </Link>
          <span className="text-slate-300">/</span>
          <span className="text-sm text-slate-400 truncate max-w-50">{meal.name}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* LEFT: Image + Price History */}
          <div className="lg:col-span-3 space-y-5">
            {/* Image */}
            <div className="w-full aspect-4/3 bg-slate-100 rounded-2xl overflow-hidden border border-slate-100">
              {meal.image_url ? (
                <img src={meal.image_url} alt={meal.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-7xl">🍽️</div>
              )}
            </div>

            {/* Price History Chart */}
            {priceHistory.length > 0 && (
              <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">
                  Price History · 6 months
                </h3>
                <div className="flex items-end justify-between gap-2 h-20">
                  {priceHistory.map((hist, i) => {
                    const pct = (hist.price / maxPrice) * 100;
                    const isLatest = i === priceHistory.length - 1;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                        <div className="opacity-0 group-hover:opacity-100 absolute -top-7 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap pointer-events-none z-10">
                          {hist.price} PKR
                        </div>
                        <div
                          className={`w-full rounded-t-md transition-all ${isLatest ? "bg-emerald-500" : "bg-slate-200 group-hover:bg-slate-300"}`}
                          style={{ height: `${pct}%`, minHeight: "4px" }}
                        />
                        <span className="text-[9px] text-slate-400 font-medium">
                          {hist.month.split(" ")[0].substring(0, 3)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Info */}
          <div className="lg:col-span-2 space-y-5">
            {/* Meal ID badge */}
            <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
              Meal #{id}
            </span>

            {/* Name + Price */}
            <div>
              <h1 className="text-3xl font-black text-slate-900 tracking-tight leading-tight mb-3">
                {meal.name}
              </h1>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black text-emerald-600">
                  {meal.price.toLocaleString()}
                </span>
                <span className="text-sm font-bold text-emerald-500/70 uppercase">PKR</span>
              </div>
            </div>

            {/* Meta */}
            <div className="space-y-3">
              <div className="flex items-center gap-3 bg-white border border-slate-100 rounded-xl p-3 shadow-sm">
                <div className="w-9 h-9 rounded-xl bg-slate-50 flex items-center justify-center text-lg shrink-0">📍</div>
                <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Location</p>
                  <p className="text-sm font-semibold text-slate-800">{meal.location}</p>
                </div>
              </div>

              <div className={`flex items-center gap-3 border rounded-xl p-3 ${confidenceColor.bg} ${confidenceColor.border}`}>
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${confidenceColor.bg}`}>
                  <div className={`w-3 h-3 rounded-full ${confidenceColor.dot}`} />
                </div>
                <div>
                  <p className={`text-[10px] font-bold uppercase tracking-wider ${confidenceColor.text}`}>Confidence Score</p>
                  <p className={`text-sm font-bold ${confidenceColor.text}`}>{meal.confidence}% — community verified</p>
                </div>
              </div>
            </div>

            {/* AI Insight */}
            {data.ai_insight && (
              <div className="relative overflow-hidden rounded-xl p-px">
                <div className="absolute inset-0 bg-linear-to-r from-emerald-400 via-teal-400 to-emerald-500 opacity-70 animate-gradient-xy rounded-xl" />
                <div className="relative bg-white rounded-[11px] p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-lg shrink-0 animate-pulse">✨</span>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-600 mb-1">AI Insight</p>
                      <p className="text-sm text-slate-700 leading-relaxed">{data.ai_insight}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col gap-2 pt-1">
              <Link
                href={`/meals/${id}/report`}
                className="flex items-center justify-center gap-2 w-full bg-slate-900 text-white py-3 rounded-xl font-bold text-sm hover:bg-slate-800 transition-colors"
              >
                📝 Report Price Change
              </Link>
              <Link
                href="/"
                className="flex items-center justify-center gap-2 w-full bg-slate-50 border border-slate-200 text-slate-600 py-3 rounded-xl font-semibold text-sm hover:bg-slate-100 transition-colors"
              >
                ← Back to Search
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
