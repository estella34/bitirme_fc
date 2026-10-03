/**
 * Yüksek frekanslı canlı veri (LiDAR haritası, tarama ışını, robot konumu).
 * React durumunun dışında tutulur; 3B bileşenler her karede buradan okur.
 * Böylece saniyede onlarca telemetri mesajı arayüzü yeniden çizdirmez.
 */

export const MAP_CAPACITY = 800_000;
export const SCAN_CAPACITY = 2_000;

export const mapBuf = {
  positions: new Float32Array(MAP_CAPACITY * 3),
  colors: new Float32Array(MAP_CAPACITY * 3),
  count: 0,
  /** Harita sıfırlandığında artar; GPU tamponu baştan yüklenir. */
  epoch: 0,
  /** Renkler (tema) değiştiğinde artar; renk tamponu baştan yüklenir. */
  colorEpoch: 0,
};

export const scanBuf = {
  positions: new Float32Array(SCAN_CAPACITY * 3),
  count: 0,
  version: 0,
};

export const robotLive = {
  x: 0,
  y: 0,
  yaw: 0,
  mast_mm: 150,
  state: "idle",
  seen: false,
  /** Son fotoğrafın zamanı (performance.now), kamera "flaşı" için. */
  flashAt: -1e9,
};

export const trailBuf: { points: [number, number][]; version: number } = {
  points: [],
  version: 0,
};

// Yüksekliğe göre renk tablosu. Tema değişince setLidarPalette() ile yeniden kurulur.
const LUT_SIZE = 64;
const LUT = new Float32Array(LUT_SIZE * 3);
const MAX_Z = 3.2; // renk ölçeğinin üst sınırı (m)

function buildLut(stops: [number, string][]): void {
  // three.js tepe renklerini doğrusal uzayda bekler: sRGB → doğrusal dönüşümü burada yapılır
  // (three'yi ana pakete çekmemek için elle).
  const lin = (c: number) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const rgb = (hex: string) => [1, 3, 5].map((i) => lin(parseInt(hex.slice(i, i + 2), 16) / 255));
  for (let i = 0; i < LUT_SIZE; i++) {
    const t = i / (LUT_SIZE - 1);
    let k = 0;
    while (k < stops.length - 2 && t > stops[k + 1][0]) k++;
    const [t0, c0] = stops[k];
    const [t1, c1] = stops[k + 1];
    const f = Math.min(1, Math.max(0, (t - t0) / (t1 - t0)));
    const a = rgb(c0);
    const b = rgb(c1);
    LUT.set([0, 1, 2].map((j) => a[j] + (b[j] - a[j]) * f), i * 3);
  }
}

function lutIndex(z: number): number {
  return Math.min(LUT_SIZE - 1, Math.max(0, Math.round((z / MAX_Z) * (LUT_SIZE - 1)))) * 3;
}

/** Tema değişti: renk tablosunu kur ve mevcut bütün noktaları yeniden boya. */
export function setLidarPalette(stops: [number, string][]): void {
  buildLut(stops);
  const { positions, colors } = mapBuf;
  for (let i = 0; i < mapBuf.count; i++) {
    const li = lutIndex(positions[i * 3 + 1]);
    colors[i * 3] = LUT[li];
    colors[i * 3 + 1] = LUT[li + 1];
    colors[i * 3 + 2] = LUT[li + 2];
  }
  mapBuf.colorEpoch++;
}

/** Voksel indekslerini [ix,iy,iz,...] dünya→three koordinatına çevirip haritaya ekler. */
export function appendCells(cells: number[], resolution: number): void {
  const n = Math.min(cells.length / 3, MAP_CAPACITY - mapBuf.count);
  const { positions, colors } = mapBuf;
  let o = mapBuf.count * 3;
  for (let i = 0; i < n; i++) {
    const x = (cells[i * 3] + 0.5) * resolution;
    const y = (cells[i * 3 + 1] + 0.5) * resolution;
    const z = (cells[i * 3 + 2] + 0.5) * resolution;
    positions[o] = x;
    positions[o + 1] = z;
    positions[o + 2] = -y;
    const li = lutIndex(z);
    colors[o] = LUT[li];
    colors[o + 1] = LUT[li + 1];
    colors[o + 2] = LUT[li + 2];
    o += 3;
  }
  mapBuf.count += n;
}

export function clearLive(): void {
  mapBuf.count = 0;
  mapBuf.epoch++;
  scanBuf.count = 0;
  scanBuf.version++;
  trailBuf.points = [];
  trailBuf.version++;
}

export function setScan(flat: number[]): void {
  const n = Math.min(flat.length / 3, SCAN_CAPACITY);
  const p = scanBuf.positions;
  for (let i = 0; i < n; i++) {
    p[i * 3] = flat[i * 3];
    p[i * 3 + 1] = flat[i * 3 + 2];
    p[i * 3 + 2] = -flat[i * 3 + 1];
  }
  scanBuf.count = n;
  scanBuf.version++;
}
