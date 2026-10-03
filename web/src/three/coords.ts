/**
 * Dünya ekseni (API): x doğu, y kuzey, z yukarı (m).
 * three.js ekseni: x sağ, y yukarı, z izleyiciye doğru.
 * Eşleme (sağ el kuralını korur): dünya (x, y, z) → three (x, z, −y).
 * Dünyada z etrafında yaw dönüşü, three'de y etrafında aynı açıya karşılık gelir.
 */
export const w = (x: number, y: number, z = 0): [number, number, number] => [x, z, -y];

export const deg = (d: number) => (d * Math.PI) / 180;
