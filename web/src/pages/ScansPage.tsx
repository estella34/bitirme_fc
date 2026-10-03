import { useEffect, useState } from "react";
import { api } from "../api";
import { STATUS, fmtDateTime, fmtDuration } from "../format";
import { useStore } from "../store";
import type { Scan, Status } from "../types";

const MODE: Record<Scan["mode"], string> = { robot: "Robot", manual: "Elle", demo: "Demo" };
const STATE: Record<Scan["status"], string> = {
  running: "Sürüyor",
  completed: "Tamamlandı",
  failed: "Hata",
  cancelled: "Durduruldu",
};

export function ScansPage() {
  const warehouseId = useStore((s) => s.warehouseId);
  const lastScanId = useStore((s) => s.summary?.last_scan?.id);
  const lastScanStatus = useStore((s) => s.summary?.last_scan?.status);
  const [scans, setScans] = useState<Scan[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (warehouseId == null) return;
    api
      .scans(warehouseId)
      .then((s) => (setScans(s), setError(null)))
      .catch((e) => setError((e as Error).message));
  }, [warehouseId, lastScanId, lastScanStatus]);

  return (
    <main className="page">
      <header className="page-head">
        <h1>Taramalar</h1>
        <p>Her tarama, robotun bir tur boyunca topladığı görüntü ve sonuçların kaydıdır. Sonuçları Excel'de açmak için CSV indirin.</p>
      </header>
      {error && <p className="error">Taramalar alınamadı: {error}</p>}
      {scans && scans.length === 0 && (
        <div className="empty-state">
          <p>Henüz tarama yok.</p>
          <p className="muted">Sistemi denemek için üstteki “Demo taramayı başlat” düğmesini kullanın.</p>
        </div>
      )}
      {scans && scans.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Tarama</th>
                <th scope="col">Tür</th>
                <th scope="col">Başlangıç</th>
                <th scope="col">Süre</th>
                <th scope="col">Durum</th>
                <th scope="col">Sonuç</th>
                <th scope="col">
                  <span className="sr-only">İndir</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => {
                const total = Object.values(s.counts).reduce((a, b) => a + (b ?? 0), 0);
                const issues = (s.counts.conflict ?? 0) + (s.counts.unreadable ?? 0);
                return (
                  <tr key={s.id}>
                    <td>
                      <code>{s.id}</code>
                    </td>
                    <td>{MODE[s.mode]}</td>
                    <td>{fmtDateTime(s.started_at)}</td>
                    <td>{fmtDuration(s.started_at, s.finished_at)}</td>
                    <td>{STATE[s.status]}</td>
                    <td>
                      <div className="result-cell">
                        <div className="statusbar slim" aria-hidden="true">
                          {(Object.keys(s.counts) as Status[]).map((k) => (
                            <i key={k} style={{ flexGrow: s.counts[k], background: STATUS[k].color }} />
                          ))}
                        </div>
                        <span>
                          {total} göz{issues > 0 && <> · <b className="bad">{issues} sorunlu</b></>}
                        </span>
                      </div>
                    </td>
                    <td>
                      {total > 0 && (
                        <a className="btn btn-ghost sm" href={api.exportUrl(s.id)} download>
                          CSV indir
                        </a>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
