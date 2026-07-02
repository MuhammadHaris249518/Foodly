// ── Shared TypeScript types for the Foodly frontend ──────────

export interface Meal {
  id: number;
  name: string;
  price: number;
  location: string;
  confidence: number;
  image_url: string;
  description?: string;
  latitude?: number;
  longitude?: number;
}

export interface MealDetail extends Meal {
  ai_insight?: string;
  price_history?: PriceHistoryEntry[];
}

export interface PriceHistoryEntry {
  month: string;
  price: number;
}

export interface ProfileStats {
  email: string;
  saved_count: number;
  report_count: number;
}

export interface LivePriceData {
  restaurant: string;
  meal: string;
  price_pkr: number;
  confidence: number;
}

export type LiveSearchStatus =
  | "idle"
  | "starting"
  | "searching"
  | "extracting"
  | "complete"
  | "failed";

export type BackendStatus = "starting" | "db_error" | "ready";
