/**
 * Aydınlık / karanlık tema.
 *
 * Arayüz (DOM) renkleri styles.css içindeki CSS değişkenlerindedir; burada yalnız 3B sahnenin
 * renkleri tutulur, çünkü three.js malzemeleri CSS değişkeni okuyamaz.
 * Karanlık: gece vardiyası kontrol odası. Aydınlık: gündüz, beton zeminli depo.
 */
import type { Status } from "./types";

export type ThemeName = "dark" | "light";

export interface ScenePalette {
  bg: string;
  floor: string;
  gridCell: string;
  gridSection: string;
  outline: string;
  aisle: string;
  hemiSky: string;
  hemiGround: string;
  hemi: number;
  sun: number;
  ambient: number;
  kraft: string;
  kraftEdge: string;
  ghostOpacity: number;
  ghostEdge: string;
  upright: string;
  beam: string;
  deck: string;
  deckOpacity: number;
  hover: string;
  status: Record<Status, string>;
  /** LiDAR noktaları: yüksekliğe göre renk geçişi (0 = zemin, 1 = ~3,2 m). */
  lidar: [number, string][];
  lidarOpacity: number;
  scanBeam: string;
}

export const SCENE: Record<ThemeName, ScenePalette> = {
  dark: {
    bg: "#0a111b",
    floor: "#0e1725",
    gridCell: "#18283b",
    gridSection: "#23405f",
    outline: "#35557a",
    aisle: "#f5c625",
    hemiSky: "#a9c1e0",
    hemiGround: "#0b121c",
    hemi: 0.75,
    sun: 1.3,
    ambient: 0.18,
    kraft: "#c39060",
    kraftEdge: "#8a6438",
    ghostOpacity: 0.13,
    ghostEdge: "#7d6a52",
    upright: "#2f6be4",
    beam: "#f2791c",
    deck: "#22344a",
    deckOpacity: 0.55,
    hover: "#9db4d3",
    status: {
      verified: "#35d49a",
      conflict: "#ff4757",
      unreadable: "#f5c625",
      empty: "#5f7189",
      observed: "#5cc8ff",
    },
    lidar: [
      [0.0, "#1b3a8f"],
      [0.25, "#2f6be4"],
      [0.55, "#2cc6e8"],
      [0.8, "#9fe7f5"],
      [1.0, "#eaf6ff"],
    ],
    lidarOpacity: 0.8,
    scanBeam: "#ffd7a8",
  },
  light: {
    bg: "#e6eaef",
    floor: "#d9dee5",
    gridCell: "#c6ceda",
    gridSection: "#a7b4c4",
    outline: "#7f93ab",
    aisle: "#e0a800",
    hemiSky: "#ffffff",
    hemiGround: "#9aa6b5",
    hemi: 1.05,
    sun: 1.25,
    ambient: 0.35,
    kraft: "#c08c58",
    kraftEdge: "#7d5a33",
    ghostOpacity: 0.24,
    ghostEdge: "#9c8466",
    upright: "#2457c5",
    beam: "#e2660b",
    deck: "#b9c3cf",
    deckOpacity: 0.6,
    hover: "#4f6580",
    status: {
      verified: "#11a06d",
      conflict: "#e2283b",
      unreadable: "#e0a800",
      empty: "#8292a6",
      observed: "#1e88d0",
    },
    lidar: [
      [0.0, "#0b2a6b"],
      [0.3, "#1c4fb8"],
      [0.6, "#0e86a8"],
      [0.85, "#2e9f95"],
      [1.0, "#5f7389"],
    ],
    lidarOpacity: 0.6,
    scanBeam: "#e2660b",
  },
};

const KEY = "depogoz-tema";

/** index.html içindeki betik temayı ilk boyamadan önce ayarlar; burada onu okuruz. */
export function currentTheme(): ThemeName {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

export function savedTheme(): ThemeName | null {
  try {
    const t = localStorage.getItem(KEY);
    return t === "light" || t === "dark" ? t : null;
  } catch {
    return null;
  }
}

export function applyTheme(t: ThemeName, persist: boolean): void {
  document.documentElement.dataset.theme = t;
  if (!persist) return;
  try {
    localStorage.setItem(KEY, t);
  } catch {
    /* gizli pencere vb.: tercih yalnız bu oturumda geçerli */
  }
}
