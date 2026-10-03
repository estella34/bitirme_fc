import type { CodeRead } from "../types";

/**
 * Kanıt görüntüsü + okunan kodların konumu. Çokgenler özgün görüntü pikselindedir;
 * SVG viewBox özgün boyutta olduğu için küçük resim üzerinde de doğru yere oturur.
 */
export function Evidence({
  src,
  width,
  height,
  reads,
  highlight,
  alt,
}: {
  src: string;
  width: number;
  height: number;
  reads: CodeRead[];
  highlight?: (text: string) => string | undefined;
  alt: string;
}) {
  const stroke = Math.max(2, width / 260);
  return (
    <figure className="evidence" style={{ aspectRatio: `${width} / ${height}` }}>
      <img src={src} alt={alt} loading="lazy" />
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
        {reads.map((r) => {
          const color = highlight?.(r.text) ?? "var(--st-verified)";
          const pts = r.polygon.map((p) => p.join(",")).join(" ");
          const [lx, ly] = r.polygon.reduce((a, p) => (p[1] < a[1] ? p : a), r.polygon[0]);
          return (
            <g key={r.text + r.polygon[0].join()}>
              <polygon
                points={pts}
                style={{ fill: color, fillOpacity: 0.14, stroke: color }}
                strokeWidth={stroke}
              />
              <text
                x={lx}
                y={ly - stroke * 3}
                style={{ fill: color }}
                fontSize={Math.max(14, width / 48)}
                fontFamily="IBM Plex Mono, monospace"
                fontWeight={500}
              >
                {r.text}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
