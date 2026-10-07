import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { STATUS } from "../format";
import { useStore } from "../store";
import type { CameraRead, CameraStatus } from "../types";

const LABELS = ["Kamera 1", "Kamera 2", "Kamera 3", "Kamera 4"];

/** Robotun dört kamerası: canlı görüntü, odak ve çek-ve-oku (Jetson'da çalışır). */
export function CameraPage() {
  const warehouseId = useStore((s) => s.warehouseId);
  const [status, setStatus] = useState<CameraStatus | null>(null);
  const [view, setView] = useState(0); // 0: dördü birden, 1..4: tek kamera büyük
  const [focus, setFocus] = useState(2048);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [read, setRead] = useState<CameraRead | null>(null);
  const [toTwin, setToTwin] = useState(true);
  const [streamKey, setStreamKey] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const st = await api.camera();
      setStatus(st);
      if (!busy) setFocus(st.focus);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [busy]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [refresh]);

  const run = async (label: string, fn: () => Promise<void>) => {
    setBusy(label);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
      setStreamKey((k) => k + 1); // akış koptuysa yeniden bağlan
    } finally {
      setBusy(null);
    }
  };

  if (status && !status.available) {
    return (
      <main className="page">
        <header className="page-head">
          <h1>Kameralar</h1>
          <p>
            Bu sunucuda kamera yok. Kameralar Jetson'a bağlı; arayüzü Jetson'dan açın:
            <code> http://&lt;jetson-ip&gt;:8000</code>
          </p>
        </header>
      </main>
    );
  }

  const w = view === 0 ? 1920 : 1280;
  const src = `/api/camera/stream?view=${view}&w=${w}&fps=8&k=${streamKey}`;
  const overlay = read && read.views.filter((v) => view === 0 || v.camera === view);

  return (
    <main className="page page-wide">
      <header className="page-head cam-head">
        <div>
          <h1>Kameralar</h1>
          <p>
            Dört kamera adaptörde tek karede birleşiyor. Bir kameraya tıklayınca büyür. Okunan kodlar
            görüntüde işaretlenir; stok listesindeki kodlar raf gözüne işlenir ve dijital ikiz güncellenir.
          </p>
        </div>
        <dl className="cam-stats">
          <div>
            <dt>Durum</dt>
            <dd>{status?.running ? "Açık" : "Beklemede"}</dd>
          </div>
          <div>
            <dt>Hız</dt>
            <dd>{status?.running ? `${status.fps} kare/s` : "—"}</dd>
          </div>
          <div>
            <dt>Odak</dt>
            <dd>{status?.focus ?? "—"}</dd>
          </div>
        </dl>
      </header>

      <div className="cam-layout">
        <div>
          <div className="cam-view-tabs" role="tablist" aria-label="Görünüm">
            {["Dördü", ...LABELS].map((l, i) => (
              <button
                key={l}
                role="tab"
                aria-selected={view === i}
                className="tab"
                onClick={() => setView(i)}
              >
                {l}
              </button>
            ))}
          </div>
          <figure className={`cam-stage${view === 0 ? " is-quad" : ""}`}>
            <img src={src} alt={view === 0 ? "Dört kameranın canlı görüntüsü" : `${LABELS[view - 1]} canlı görüntüsü`} />
            {view === 0 &&
              LABELS.map((l, i) => (
                <button
                  key={l}
                  className={`cam-quad q${i + 1}`}
                  onClick={() => setView(i + 1)}
                  aria-label={`${l} büyüt`}
                >
                  <span>{l}</span>
                </button>
              ))}
            {overlay && read && (
              <svg
                viewBox={view === 0 ? `0 0 ${read.width} ${read.height}` : `0 0 ${read.width / 2} ${read.height / 2}`}
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                {overlay.map((v) => {
                  const dx = view === 0 ? ((v.camera - 1) % 2) * (read.width / 2) : 0;
                  const dy = view === 0 ? Math.floor((v.camera - 1) / 2) * (read.height / 2) : 0;
                  return v.codes.map((c) => (
                    <g key={`${v.camera}-${c.text}-${c.polygon[0].join()}`}>
                      <polygon
                        points={c.polygon.map(([x, y]) => `${x + dx},${y + dy}`).join(" ")}
                        className="cam-code"
                      />
                      <text x={c.polygon[0][0] + dx} y={c.polygon[0][1] + dy - 10} className="cam-code-text">
                        {c.text}
                      </text>
                    </g>
                  ));
                })}
              </svg>
            )}
          </figure>
        </div>

        <aside className="cam-panel">
          <section>
            <h2>Odak</h2>
            <button
              className="btn btn-primary"
              disabled={!!busy}
              onClick={() =>
                run("af", async () => {
                  const r = await api.cameraAutofocus(view);
                  setFocus(r.position);
                  await refresh();
                })
              }
            >
              {busy === "af" ? "Odaklanıyor…" : view === 0 ? "Otomatik odakla" : `${LABELS[view - 1]} için odakla`}
            </button>
            <label className="cam-slider">
              <span>
                Elle odak <b>{focus}</b>
              </span>
              <input
                type="range"
                min={0}
                max={status?.focus_max ?? 4095}
                step={16}
                value={focus}
                disabled={!!busy}
                onChange={(e) => setFocus(Number(e.target.value))}
                onPointerUp={() => run("focus", async () => void (await api.cameraFocus(focus)))}
                onKeyUp={() => run("focus", async () => void (await api.cameraFocus(focus)))}
              />
              <small className="muted">Sol: yakın · sağ: uzak. Odak motoru dört kamerada birlikte hareket eder.</small>
            </label>
          </section>

          <section>
            <h2>Çek ve oku</h2>
            <label className="check">
              <input type="checkbox" checked={toTwin} onChange={(e) => setToTwin(e.target.checked)} />
              Okunanları depoya işle
            </label>
            <button
              className="btn btn-primary"
              disabled={!!busy}
              onClick={() =>
                run("read", async () => {
                  setRead(await api.cameraRead(toTwin && warehouseId != null ? { warehouse_id: warehouseId } : {}));
                })
              }
            >
              {busy === "read" ? "Okunuyor…" : "Çek ve oku"}
            </button>
            {read && (
              <div className="cam-results">
                <p className="headline">
                  {read.total_codes === 0 ? "Kod bulunamadı." : (
                    <>
                      <b className="ok">{read.total_codes}</b> kod okundu
                    </>
                  )}
                </p>
                {read.views.map((v) => (
                  <div key={v.camera} className="cam-result">
                    <h3>
                      {LABELS[v.camera - 1]} <span className="muted">· keskinlik {v.sharpness}</span>
                    </h3>
                    {v.codes.length === 0 ? (
                      <p className="muted">Kod yok</p>
                    ) : (
                      <ul className="codes">
                        {v.codes.map((c) => (
                          <li key={c.text} className="code-ok">
                            <span className="mark" aria-hidden="true">✓</span>
                            <code>{c.text}</code>
                            <span className="desc">{c.symbology}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                    {v.location ? (
                      <p className="cam-loc" style={{ color: STATUS[v.location.status ?? "pending"].color }}>
                        {v.location_code} → {STATUS[v.location.status ?? "pending"].label}
                      </p>
                    ) : (
                      v.codes.length > 0 && toTwin && <p className="muted">Bu kodlar stok listesinde yok.</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}
