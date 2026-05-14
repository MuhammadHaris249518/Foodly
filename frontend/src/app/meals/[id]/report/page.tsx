"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function ReportPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const router = useRouter();

  const [reportedPrice, setReportedPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [reporter, setReporter] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      setPhoto(e.target.files[0]);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!reportedPrice) {
      setError("Please enter the reported price.");
      return;
    }

    setLoading(true);
    try {
      const form = new FormData();
      form.append("meal_id", id);
      form.append("reported_price", reportedPrice);
      if (notes) form.append("notes", notes);
      if (reporter) form.append("reporter_name", reporter);
      if (photo) form.append("photo", photo);

      const res = await fetch("http://localhost:8000/api/v1/reports", {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Failed to submit report");
      }

      setSuccess(true);
      setTimeout(() => router.push(`/meals/${id}`), 1000);
    } catch (err: unknown) {
      setError(err.message || "Submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <Link href={`/meals/${id}`} className="text-emerald-500 font-medium mb-6 inline-block">
          ← Back to meal
        </Link>

        <form onSubmit={handleSubmit} className="bg-white shadow-lg rounded-2xl p-6">
          <h2 className="text-2xl font-bold mb-4">Report Price Change</h2>

          <label className="block mb-3">
            <span className="text-sm font-medium">Reported Price (PKR)</span>
            <input
              type="number"
              step="1"
              min="0"
              value={reportedPrice}
              onChange={(e) => setReportedPrice(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2"
              required
            />
          </label>

          <label className="block mb-3">
            <span className="text-sm font-medium">Your Name (optional)</span>
            <input
              type="text"
              value={reporter}
              onChange={(e) => setReporter(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2"
            />
          </label>

          <label className="block mb-3">
            <span className="text-sm font-medium">Notes (optional)</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2"
              rows={3}
            />
          </label>

          <label className="block mb-4">
            <span className="text-sm font-medium">Photo (optional, .jpg/.png, ≤5MB)</span>
            <input type="file" accept="image/*" onChange={handleFileChange} className="mt-2" />
            {photo && <p className="text-xs mt-2">Selected: {photo.name}</p>}
          </label>

          {error && <div className="text-red-600 mb-3">{error}</div>}
          {success && <div className="text-green-600 mb-3">Report submitted — thank you!</div>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="bg-emerald-600 text-white px-4 py-2 rounded-full font-bold hover:bg-emerald-700 disabled:opacity-60"
            >
              {loading ? "Submitting..." : "Submit Report"}
            </button>

            <Link href={`/meals/${id}`} className="px-4 py-2 rounded-full border">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
}
