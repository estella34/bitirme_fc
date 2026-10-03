import type { Status } from "./types";

/**
 * Durum adları ve renkleri. Renkler CSS değişkenidir (styles.css), böylece temaya uyar.
 * 3B sahnedeki karşılıkları theme.ts → SCENE[tema].status içindedir.
 */
export const STATUS: Record<Status | "pending", { label: string; color: string }> = {
  verified: { label: "Doğrulandı", color: "var(--st-verified)" },
  conflict: { label: "Çelişki", color: "var(--st-conflict)" },
  unreadable: { label: "Okunamadı", color: "var(--st-unreadable)" },
  empty: { label: "Boş", color: "var(--st-empty)" },
  observed: { label: "Stok bilgisi yok", color: "var(--st-observed)" },
  pending: { label: "Taranmadı", color: "var(--st-pending)" },
};

export const STATUS_ORDER: (Status | "pending")[] = [
  "conflict",
  "unreadable",
  "verified",
  "empty",
  "observed",
  "pending",
];

export const ROBOT_STATE: Record<string, string> = {
  idle: "Beklemede",
  starting: "Başlıyor",
  moving: "İlerliyor",
  turning: "Dönüyor",
  mast: "Kamerayı konumluyor",
  settling: "Titreşim yatışıyor",
  capturing: "Fotoğraf çekiyor",
};

/** Robotun turuncu vurgusu: iki temada da aynı (robot sahnedeki bir nesne, tema değil). */
export const BEAM = "#f2791c";

const timeFmt = new Intl.DateTimeFormat("tr-TR", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
});
const dateTimeFmt = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export const fmtTime = (iso: string) => timeFmt.format(new Date(iso));
export const fmtDateTime = (iso: string) => dateTimeFmt.format(new Date(iso));

export function fmtDuration(startIso: string, endIso: string | null): string {
  const ms = (endIso ? new Date(endIso) : new Date()).getTime() - new Date(startIso).getTime();
  const s = Math.max(0, Math.round(ms / 1000));
  return s < 60 ? `${s} sn` : `${Math.floor(s / 60)} dk ${s % 60} sn`;
}

/** Kod metninden kararlı küçük sayı: kolilere tutarlı boy farkı vermek için. */
export function hash01(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 1000) / 1000;
}
