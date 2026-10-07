import { useState } from "react";
import { ROBOT_STATE } from "../format";
import { useStore, type View } from "../store";

const TABS: { id: View; label: string }[] = [
  { id: "depo", label: "Depo" },
  { id: "kameralar", label: "Kameralar" },
  { id: "inceleme", label: "İnceleme" },
  { id: "taramalar", label: "Taramalar" },
  { id: "okuma", label: "Okuma testi" },
];

const SPEEDS = [1, 2, 4, 8];

export function TopBar() {
  const view = useStore((s) => s.view);
  const setView = useStore((s) => s.setView);
  const warehouse = useStore((s) => s.twin?.warehouse);
  const pending = useStore((s) => s.summary?.pending_review ?? 0);
  const conn = useStore((s) => s.conn);
  const robot = useStore((s) => s.robot);
  const demo = useStore((s) => s.demo);
  const startDemo = useStore((s) => s.startDemo);
  const stopDemo = useStore((s) => s.stopDemo);
  const theme = useStore((s) => s.theme);
  const toggleTheme = useStore((s) => s.toggleTheme);
  const [speed, setSpeed] = useState(4);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setErr(null);
    try {
      await fn();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const robotText = !robot?.online
    ? "Robot çevrimdışı"
    : `Robot: ${ROBOT_STATE[robot.state] ?? robot.state}`;

  return (
    <header className="topbar">
      <div className="brand">
        {/* "Göz": hem raf gözü (dikmeler + kirişler) hem de bakan göz. */}
        <svg viewBox="0 0 32 32" aria-hidden="true">
          <path className="upright" d="M6 4v24M26 4v24" />
          <path className="beam" d="M6 8.5h20M6 23.5h20" />
          <path className="eye" d="M9.5 16c2.8-4 10.2-4 13 0-2.8 4-10.2 4-13 0z" />
          <circle className="pupil" cx="16" cy="16" r="2.3" />
        </svg>
        <div>
          <strong>DepoGöz</strong>
          {warehouse && <span>{warehouse.name}</span>}
        </div>
      </div>

      <nav className="tabs" aria-label="Bölümler">
        {TABS.map((t) => (
          <button
            key={t.id}
            className="tab"
            aria-current={view === t.id ? "page" : undefined}
            onClick={() => setView(t.id)}
          >
            {t.label}
            {t.id === "inceleme" && pending > 0 && <span className="count">{pending}</span>}
          </button>
        ))}
      </nav>

      <div className="status-cluster">
        <span className={`conn conn-${conn}`} title={conn === "open" ? "Canlı bağlantı açık" : "Bağlantı kuruluyor"}>
          {conn === "open" ? "Canlı" : conn === "connecting" ? "Bağlanıyor" : "Bağlantı koptu"}
        </span>
        <span className="robot-state">{robotText}</span>
        <button
          className="icon-btn"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Aydınlık temaya geç" : "Karanlık temaya geç"}
          title={theme === "dark" ? "Aydınlık tema" : "Karanlık tema"}
        >
          {theme === "dark" ? (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="4.2" />
              <path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6z" />
            </svg>
          )}
        </button>
        <div className="demo-ctl">
          {demo.running ? (
            <button className="btn btn-stop" disabled={busy} onClick={() => run(stopDemo)}>
              Taramayı durdur
            </button>
          ) : (
            <>
              <label className="sr-only" htmlFor="demo-speed">
                Simülasyon hızı
              </label>
              <select id="demo-speed" value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
                {SPEEDS.map((s) => (
                  <option key={s} value={s}>
                    {s}×
                  </option>
                ))}
              </select>
              <button className="btn btn-primary" disabled={busy} onClick={() => run(() => startDemo(speed))}>
                Demo taramayı başlat
              </button>
            </>
          )}
        </div>
      </div>
      {err && (
        <p className="topbar-error" role="alert">
          {err}
        </p>
      )}
      {demo.running && (
        <div
          className="progress"
          role="progressbar"
          aria-label="Tarama ilerlemesi"
          aria-valuenow={Math.round((demo.progress ?? 0) * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <i style={{ width: `${(demo.progress ?? 0) * 100}%` }} />
        </div>
      )}
    </header>
  );
}
