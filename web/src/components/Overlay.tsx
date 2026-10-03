import { useMemo } from "react";
import { STATUS, STATUS_ORDER } from "../format";
import { useStore, type CameraMode } from "../store";
import type { Status } from "../types";

export function useStatusCounts() {
  const locations = useStore((s) => s.locations);
  return useMemo(() => {
    const counts: Record<Status | "pending", number> = {
      verified: 0,
      conflict: 0,
      unreadable: 0,
      empty: 0,
      observed: 0,
      pending: 0,
    };
    for (const l of Object.values(locations)) counts[l.status ?? "pending"]++;
    return counts;
  }, [locations]);
}

const CAMERAS: { id: CameraMode; label: string }[] = [
  { id: "perspektif", label: "Perspektif" },
  { id: "ust", label: "Üstten" },
  { id: "takip", label: "Robotu izle" },
];

export function Overlay() {
  const counts = useStatusCounts();
  const layers = useStore((s) => s.layers);
  const toggle = useStore((s) => s.toggleLayer);
  const camera = useStore((s) => s.camera.mode);
  const setCamera = useStore((s) => s.setCamera);
  const robot = useStore((s) => s.robot);

  return (
    <>
      <ul className="legend" aria-label="Göz durumları">
        {STATUS_ORDER.filter((k) => counts[k] > 0 || k === "conflict" || k === "verified").map((k) => (
          <li key={k}>
            <i className={`swatch swatch-${k}`} style={{ background: STATUS[k].color }} />
            <span>{STATUS[k].label}</span>
            <b>{counts[k]}</b>
          </li>
        ))}
      </ul>

      {robot?.online && (
        <dl className="readout" aria-label="Robot konumu">
          <div>
            <dt>x</dt>
            <dd>{robot.x.toFixed(2)} m</dd>
          </div>
          <div>
            <dt>y</dt>
            <dd>{robot.y.toFixed(2)} m</dd>
          </div>
          <div>
            <dt>kamera</dt>
            <dd>{Math.round(robot.mast_mm)} mm</dd>
          </div>
        </dl>
      )}

      <div className="scene-tools">
        <div className="seg" role="group" aria-label="Kamera">
          {CAMERAS.map((c) => (
            <button key={c.id} aria-pressed={camera === c.id} onClick={() => setCamera(c.id)}>
              {c.label}
            </button>
          ))}
        </div>
        <div className="seg" role="group" aria-label="Katmanlar">
          <button aria-pressed={layers.map} onClick={() => toggle("map")}>
            LiDAR haritası
          </button>
          <button aria-pressed={layers.beam} onClick={() => toggle("beam")}>
            Anlık tarama
          </button>
          <button aria-pressed={layers.trail} onClick={() => toggle("trail")}>
            Robot izi
          </button>
        </div>
      </div>
    </>
  );
}
