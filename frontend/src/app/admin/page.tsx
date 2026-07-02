"use client";

import { useEffect, useMemo, useState } from "react";
import { API_BASE, ADMIN_SECRET, apiUrl, adminHeaders } from "../../lib/api";

const STATUS_TABS = [
  { key: "pending", label: "Pending", color: "text-amber-700 bg-amber-50 border-amber-200" },
  { key: "approved", label: "Approved", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  { key: "rejected", label: "Rejected", color: "text-rose-700 bg-rose-50 border-rose-200" },
] as const;

type ReportStatus = (typeof STATUS_TABS)[number]["key"];

type AdminStats = {
  meals_total: number;
  reports_total: number;
  reports_pending: number;
  reports_approved: number;
  reports_rejected: number;
};

type AdminReport = {
  id: number;
  meal_id: number;
  meal_name?: string | null;
  meal_price?: number | null;
  meal_location?: string | null;
  reported_price: number;
  notes?: string | null;
  reporter_name?: string | null;
  photo_url?: string | null;
  status: string;
  created_at: string;
};

function formatDate(value: string) {
  try { return new Date(value).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" }); }
  catch { return value; }
}

function StatusChip({ status }: { status: string }) {
  const cls =
    status === "approved" ? "text-emerald-700 bg-emerald-50 border-emerald-200"
    : status === "rejected" ? "text-rose-700 bg-rose-50 border-rose-200"
    : "text-amber-700 bg-amber-50 border-amber-200";
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border ${cls}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

const STAT_ITEMS = (s: AdminStats) => [
  { label: "Total Meals", value: s.meals_total, color: "text-slate-900", bg: "bg-white border-slate-100" },
  { label: "Total Reports", value: s.reports_total, color: "text-slate-900", bg: "bg-white border-slate-100" },
  { label: "Pending", value: s.reports_pending, color: "text-amber-600", bg: "bg-amber-50 border-amber-100" },
  { label: "Approved", value: s.reports_approved, color: "text-emerald-600", bg: "bg-emerald-50 border-emerald-100" },
  { label: "Rejected", value: s.reports_rejected, color: "text-rose-500", bg: "bg-rose-50 border-rose-100" },
];

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [status, setStatus] = useState<ReportStatus>("pending");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState<number | null>(null);

  const headers = useMemo(() => {
    const h: Record<string, string> = {};
    if (ADMIN_SECRET) h["x-admin-secret"] = ADMIN_SECRET;
    return h;
  }, []);

  useEffect(() => {
    if (!ADMIN_SECRET) return;
    let ignore = false;
    fetch(`${API_BASE}/api/v1/admin/stats`, { headers })
      .then((r) => r.ok ? r.json() : Promise.reject(r))
      .then((d) => { if (!ignore) setStats(d as AdminStats); })
      .catch((e) => { if (!ignore) setError(String(e)); });
    return () => { ignore = true; };
  }, [headers]);

  useEffect(() => {
    if (!ADMIN_SECRET) return;
    let ignore = false;
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/v1/admin/reports?status=${status}`, { headers })
      .then((r) => r.ok ? r.json() : Promise.reject(r))
      .then((d) => { if (!ignore) setReports(d as AdminReport[]); })
      .catch((e) => { if (!ignore) setError(String(e)); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [headers, status]);

  async function handleAction(reportId: number, action: "approve" | "reject") {
    setActionBusy(reportId);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/reports/${reportId}/${action}`, { method: "POST", headers });
      if (!res.ok) throw new Error(await res.text());
      setReports((prev) => prev.filter((r) => r.id !== reportId));
      if (stats) {
        setStats({
          ...stats,
          reports_pending: Math.max(0, stats.reports_pending - 1),
          reports_approved: action === "approve" ? stats.reports_approved + 1 : stats.reports_approved,
          reports_rejected: action === "reject" ? stats.reports_rejected + 1 : stats.reports_rejected,
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionBusy(null);
    }
  }

  return (
    <main className="min-h-screen bg-[#FAFAF9] font-(family-name:--font-outfit)">
      <div className="mx-auto max-w-6xl px-6 py-10">
        {/* Header */}
        <div className="mb-8">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Admin Control Room</p>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Price Report Verification</h1>
          <p className="text-slate-500 text-sm mt-1 max-w-xl">
            Review community-submitted price reports. Approve to update the live meal price immediately.
          </p>
        </div>

        {/* No secret warning */}
        {!ADMIN_SECRET && (
          <div className="mb-6 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
            <span className="text-amber-500 text-lg shrink-0">⚠</span>
            <p className="text-sm text-amber-800 font-medium">
              <code className="font-mono bg-amber-100 px-1 rounded">NEXT_PUBLIC_ADMIN_SECRET</code> is not set.
              Add it to your frontend <code className="font-mono bg-amber-100 px-1 rounded">.env.local</code> to load live data.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-3 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
            <span className="text-rose-500">⚠</span>
            <p className="text-sm text-rose-700 font-medium">{error}</p>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
          {stats
            ? STAT_ITEMS(stats).map((s) => (
                <div key={s.label} className={`border rounded-2xl px-4 py-4 shadow-sm ${s.bg}`}>
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">{s.label}</p>
                  <p className={`text-2xl font-black ${s.color}`}>{s.value}</p>
                </div>
              ))
            : Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="border border-slate-100 rounded-2xl h-20 bg-white animate-pulse" />
              ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-5">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatus(tab.key)}
              className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider border transition-all ${
                status === tab.key ? tab.color : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {tab.label}
              {tab.key === "pending" && stats?.reports_pending ? (
                <span className="ml-1.5 bg-amber-400 text-white text-[9px] font-black px-1.5 py-0.5 rounded-full">
                  {stats.reports_pending}
                </span>
              ) : null}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white border border-slate-100 rounded-2xl shadow-sm overflow-hidden">
          {/* Table header */}
          <div className="hidden md:grid md:grid-cols-[1.6fr_0.9fr_1.1fr_0.7fr_0.8fr] gap-4 px-6 py-3 border-b border-slate-100 bg-slate-50/60">
            {["Meal", "Price Change", "Reporter", "Status", "Actions"].map((h) => (
              <span key={h} className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{h}</span>
            ))}
          </div>

          {loading && (
            <div className="space-y-px">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 bg-slate-50 animate-pulse" />
              ))}
            </div>
          )}

          {!loading && reports.length === 0 && (
            <div className="py-16 text-center">
              <div className="text-3xl mb-3">📋</div>
              <p className="text-slate-600 font-semibold">No {status} reports</p>
              <p className="text-slate-400 text-sm mt-1">Check another tab or wait for new submissions</p>
            </div>
          )}

          <div className="divide-y divide-slate-50">
            {reports.map((report) => (
              <div
                key={report.id}
                className="grid md:grid-cols-[1.6fr_0.9fr_1.1fr_0.7fr_0.8fr] gap-4 px-6 py-4 items-center hover:bg-slate-50/50 transition-colors"
              >
                {/* Meal */}
                <div className="min-w-0">
                  <p className="font-bold text-slate-900 text-sm truncate">
                    {report.meal_name || `Meal #${report.meal_id}`}
                  </p>
                  <p className="text-xs text-slate-400 truncate">{report.meal_location || "Unknown location"}</p>
                  <p className="text-[10px] text-slate-300 mt-0.5">{formatDate(report.created_at)}</p>
                </div>

                {/* Price change */}
                <div>
                  <p className="font-black text-slate-900 text-sm">PKR {report.reported_price.toLocaleString()}</p>
                  <p className="text-xs text-slate-400">was {report.meal_price != null ? `PKR ${report.meal_price.toLocaleString()}` : "—"}</p>
                  {report.meal_price != null && (
                    <p className={`text-[10px] font-bold mt-0.5 ${report.reported_price > report.meal_price ? "text-rose-500" : "text-emerald-600"}`}>
                      {report.reported_price > report.meal_price ? "▲" : "▼"}{" "}
                      {Math.abs(report.reported_price - report.meal_price).toLocaleString()} PKR
                    </p>
                  )}
                </div>

                {/* Reporter */}
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-700">{report.reporter_name || "Anonymous"}</p>
                  <p className="text-xs text-slate-400 line-clamp-2 mt-0.5">{report.notes || "No notes"}</p>
                </div>

                {/* Status */}
                <div>
                  <StatusChip status={report.status} />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {status === "pending" ? (
                    <>
                      <button
                        onClick={() => handleAction(report.id, "approve")}
                        disabled={actionBusy === report.id}
                        className="rounded-xl bg-emerald-600 text-white px-3 py-1.5 text-xs font-bold hover:bg-emerald-700 disabled:opacity-50 transition-all active:scale-95"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleAction(report.id, "reject")}
                        disabled={actionBusy === report.id}
                        className="rounded-xl bg-rose-50 border border-rose-200 text-rose-700 px-3 py-1.5 text-xs font-bold hover:bg-rose-100 disabled:opacity-50 transition-all"
                      >
                        Reject
                      </button>
                    </>
                  ) : (
                    <span className="text-xs text-slate-300 font-medium">No actions</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
