"use client";

import React, { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";

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

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setPhoto(f);
      try {
        setPreviewUrl(URL.createObjectURL(f));
      } catch (e) {
        setPreviewUrl(null);
      }
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!id) {
      setError("Invalid meal id");
      return;
    }
    if (!reportedPrice) {
      setError("Please enter the reported price.");
      return;
    }

    setLoading(true);
    try {
      const form = new FormData();
      form.append("meal_id", String(id));
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
    <main className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <div className="w-full max-w-lg">
        <Link href={`/meals/${id}`} className="text-indigo-600 font-medium mb-6 inline-block">
          ← Back to meal
        </Link>

        <form onSubmit={handleSubmit} className="bg-white shadow-xl rounded-2xl p-6 border border-gray-100">
          <div className="mb-4">
            <h2 className="text-2xl font-bold">Report Price Change</h2>
            <p className="text-sm text-gray-500">Help us keep prices accurate — optional photo helps verification.</p>
          </div>

          <label className="block mb-3">
            <span className="text-sm font-semibold text-gray-700">Reported Price (PKR)</span>
            <input
              type="number"
              step="1"
              min="0"
              value={reportedPrice}
              onChange={(e) => setReportedPrice(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 text-black"
              required
            />
          </label>

          <label className="block mb-3">
            <span className="text-sm font-semibold text-gray-700">Your Name (optional)</span>
            <input
              type="text"
              value={reporter}
              onChange={(e) => setReporter(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 text-black"
            />
          </label>

          <label className="block mb-3">
            <span className="text-sm font-semibold text-gray-700">Notes (optional)</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200 text-black"
              rows={3}
            />
          </label>

          <label className="block mb-4">
            <span className="text-sm font-semibold text-gray-700">Photo (optional, .jpg/.png, ≤5MB)</span>
            <input type="file" accept="image/*" onChange={handleFileChange} className="mt-2 text-black" />
            {photo && <p className="text-xs mt-2 text-black">Selected: {photo.name}</p>}
            {previewUrl && (
              <div className="mt-3">
                <img src={previewUrl} alt="preview" className="w-36 h-24 object-cover rounded-md border" />
              </div>
            )}
          </label>

          {error && <div className="text-red-600 mb-3">{error}</div>}
          {success && <div className="text-green-600 mb-3">Report submitted — thank you!</div>}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-60 flex items-center gap-2"
            >
              {loading ? "Submitting..." : "Submit Report"}
            </button>

            <Link href={`/meals/${id}`} className="px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
}
