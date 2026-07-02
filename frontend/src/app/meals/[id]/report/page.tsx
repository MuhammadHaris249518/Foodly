"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { apiUrl } from "../../../../lib/api";

export default function ReportPage() {
  const params = useParams();
  const id = params?.id as string | undefined;
  const router = useRouter();

  const [reportedPrice, setReportedPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [reporter, setReporter] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function handleFileChange(e: { target: HTMLInputElement }) {
    const f = e.target.files?.[0];
    if (!f) return;
    setPhoto(f);
    try { setPreviewUrl(URL.createObjectURL(f)); } catch { setPreviewUrl(null); }
  }

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault();
    setError(null);
    if (!id) { setError("Invalid meal ID."); return; }
    if (!reportedPrice) { setError("Please enter the reported price."); return; }

    setLoading(true);
    try {
      const form = new FormData();
      form.append("meal_id", String(id));
      form.append("reported_price", reportedPrice);
      if (notes) form.append("notes", notes);
      if (reporter) form.append("reporter_name", reporter);
      if (photo) form.append("photo", photo);

      const res = await fetch(apiUrl("/api/v1/reports"), { method: "POST", body: form });
      if (!res.ok) throw new Error((await res.text()) || "Failed to submit report");

      setSuccess(true);
      setTimeout(() => router.push(`/meals/${id}`), 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#FAFAF9] font-(family-name:--font-outfit)">
      <div className="mx-auto max-w-lg px-6 py-12">
        {/* Back link */}
        <Link
          href={`/meals/${id}`}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-emerald-600 transition-colors mb-8"
        >
          ← Back to meal
        </Link>

        {/* Card */}
        <div className="bg-white border border-slate-100 rounded-2xl shadow-sm overflow-hidden">
          {/* Header */}
          <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50">
            <h1 className="text-xl font-black text-slate-900">Report a Price Change</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Help keep prices accurate. Your report goes to admin review.
            </p>
          </div>

          {/* Success state */}
          {success && (
            <div className="mx-6 mt-5 flex items-center gap-3 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-3">
              <span className="text-emerald-600 text-lg">✓</span>
              <p className="text-sm font-semibold text-emerald-700">Report submitted — thank you! Redirecting…</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Reported Price */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-1.5">
                Reported Price (PKR) <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-bold">PKR</span>
                <input
                  type="number"
                  step="1"
                  min="0"
                  value={reportedPrice}
                  onChange={(e) => setReportedPrice(e.target.value)}
                  placeholder="e.g. 450"
                  required
                  className="w-full pl-14 pr-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400 transition-all placeholder:text-slate-300"
                />
              </div>
            </div>

            {/* Reporter name */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-1.5">
                Your Name <span className="text-slate-300 font-normal normal-case tracking-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={reporter}
                onChange={(e) => setReporter(e.target.value)}
                placeholder="e.g. Ali Hassan"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400 transition-all placeholder:text-slate-300"
              />
            </div>

            {/* Notes */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-1.5">
                Notes <span className="text-slate-300 font-normal normal-case tracking-normal">(optional)</span>
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any context about the price change…"
                rows={3}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400 transition-all placeholder:text-slate-300"
              />
            </div>

            {/* Photo upload */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-1.5">
                Photo <span className="text-slate-300 font-normal normal-case tracking-normal">(optional · jpg/png · max 5 MB)</span>
              </label>
              <label className="flex items-center gap-3 border-2 border-dashed border-slate-200 rounded-xl px-4 py-4 cursor-pointer hover:border-emerald-300 hover:bg-emerald-50/30 transition-all">
                <span className="text-2xl">📷</span>
                <div>
                  <p className="text-sm font-semibold text-slate-700">
                    {photo ? photo.name : "Click to upload a photo"}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">{photo ? `${(photo.size / 1024).toFixed(0)} KB` : "Helps verify the price change"}</p>
                </div>
                <input type="file" accept="image/*" onChange={handleFileChange} className="sr-only" />
              </label>
              {previewUrl && (
                <div className="mt-3 relative inline-block">
                  <img src={previewUrl} alt="preview" className="h-28 w-40 object-cover rounded-xl border border-slate-100" />
                  <button
                    type="button"
                    onClick={() => { setPhoto(null); setPreviewUrl(null); }}
                    className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center hover:bg-rose-600 transition-colors"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 bg-rose-50 border border-rose-100 rounded-xl px-4 py-3">
                <span className="text-rose-500">⚠</span>
                <p className="text-sm text-rose-700 font-medium">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button
                type="submit"
                disabled={loading || success}
                className="flex-1 bg-emerald-600 text-white py-3 rounded-xl text-sm font-bold hover:bg-emerald-700 disabled:opacity-60 transition-all active:scale-95"
              >
                {loading ? "Submitting…" : "Submit Report"}
              </button>
              <Link
                href={`/meals/${id}`}
                className="px-5 py-3 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold hover:bg-slate-50 transition-colors"
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
