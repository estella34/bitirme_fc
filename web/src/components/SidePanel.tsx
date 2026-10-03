import { useEffect, useState } from "react";
import { api } from "../api";
import { STATUS, fmtTime } from "../format";
import { useStore } from "../store";
import type { LocationDetail, Rack, Status } from "../types";
import { Evidence } from "./Evidence";
import { useStatusCounts } from "./Overlay";

export function SidePanel() {
  const selectedId = useStore((s) => s.selectedId);
  return (
    <aside className="side" aria-label={selectedId ? "Raf gözü ayrıntısı" : "Vardiya özeti"}>
      {selectedId ? <LocationPanel id={selectedId} /> : <SummaryPanel />}
    </aside>
  );
}

// --- özet -------------------------------------------------------------------

function SummaryPanel() {
  const twin = useStore((s) => s.twin);
  const counts = useStatusCounts();
  const demo = useStore((s) => s.demo);
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const issues = counts.conflict + counts.unreadable;
  const scanned = total - counts.pending;

  return (
    <div className="panel-scroll">
      <section className="panel-block">
        <h2 className="eyebrow">Vardiya özeti</h2>
        <p className="headline">
          {scanned === 0 ? (
            <>Bu depoda henüz tarama sonucu yok.</>
          ) : issues === 0 ? (
            <>
              Taranan <b>{scanned}</b> gözün hepsi stok kaydıyla uyumlu.
            </>
          ) : (
            <>
              <b className="bad">{issues}</b> göz kontrol bekliyor · {scanned}/{total} göz tarandı
            </>
          )}
        </p>
        <StatusBar counts={counts} total={total} />
      </section>

      {demo.result && (
        <section className="panel-block">
          <h2 className="eyebrow">Senaryo kontrolü</h2>
          <p className="headline">
            <b className={demo.result.detected === demo.result.anomalies ? "ok" : "bad"}>
              {demo.result.detected}/{demo.result.anomalies}
            </b>{" "}
            sorun yakalandı · {demo.result.false_alarms} yanlış alarm
          </p>
          <ScenarioList details={demo.result.details} />
        </section>
      )}

      {twin && (
        <section className="panel-block">
          <h2 className="eyebrow">Raf haritası</h2>
          <div className="minimap">
            {twin.racks.map((r) => (
              <MiniRack key={r.id} rack={r} />
            ))}
          </div>
        </section>
      )}

      <LastCapture />
      <EventFeed />
    </div>
  );
}

function StatusBar({ counts, total }: { counts: Record<Status | "pending", number>; total: number }) {
  const order: (Status | "pending")[] = ["verified", "observed", "empty", "unreadable", "conflict", "pending"];
  return (
    <div className="statusbar" role="img" aria-label="Göz durumlarının dağılımı">
      {order.map((k) =>
        counts[k] ? (
          <i
            key={k}
            style={{ flexGrow: counts[k], background: STATUS[k].color }}
            title={`${STATUS[k].label}: ${counts[k]} / ${total}`}
          />
        ) : null,
      )}
    </div>
  );
}

function ScenarioList({ details }: { details: Record<string, string> }) {
  const locations = useStore((s) => s.locations);
  const focus = useStore((s) => s.focus);
  const byCode = Object.values(locations);
  return (
    <ul className="scenario">
      {Object.entries(details).map(([code, text]) => {
        const loc = byCode.find((l) => l.code === code);
        const st = loc?.status ?? null;
        return (
          <li key={code}>
            <button onClick={() => loc && focus(loc.id)}>
              <i style={{ background: st ? STATUS[st].color : STATUS.pending.color }} />
              <code>{code}</code>
              <span>{text}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function MiniRack({ rack }: { rack: Rack }) {
  const locations = useStore((s) => s.locations);
  const focus = useStore((s) => s.focus);
  const hover = useStore((s) => s.hover);
  const levels = Array.from({ length: rack.levels }, (_, i) => rack.levels - i);
  const positions = Array.from({ length: rack.positions }, (_, i) => i + 1);
  const byPos = new Map(rack.locations.map((l) => [`${l.level}-${l.position}`, l.id]));
  return (
    <div className="minirack">
      <span className="minirack-code">{rack.code}</span>
      <div className="minirack-grid" style={{ gridTemplateColumns: `repeat(${rack.positions}, 1fr)` }}>
        {levels.flatMap((lv) =>
          positions.map((p) => {
            const id = byPos.get(`${lv}-${p}`);
            const loc = id != null ? locations[id] : undefined;
            const st = loc?.status ?? null;
            return (
              <button
                key={`${lv}-${p}`}
                className="cell"
                style={{ background: st ? STATUS[st].color : undefined }}
                aria-label={`${loc?.code ?? ""} — ${st ? STATUS[st].label : "Taranmadı"}`}
                title={loc?.code}
                onClick={() => id != null && focus(id)}
                onMouseEnter={() => id != null && hover(id)}
                onMouseLeave={() => hover(null)}
              />
            );
          }),
        )}
      </div>
    </div>
  );
}

function LastCapture() {
  const cap = useStore((s) => s.lastCapture);
  if (!cap) return null;
  return (
    <section className="panel-block">
      <h2 className="eyebrow">Son çekim</h2>
      <Evidence
        src={cap.thumb_url}
        width={cap.width}
        height={cap.height}
        reads={cap.reads}
        alt={`${cap.location_code ?? "Konumsuz"} gözünün son kamera görüntüsü`}
      />
      <p className="meta">
        <code>{cap.location_code}</code> · {cap.camera_id} · {cap.reads.length} kod ·{" "}
        {Math.round(cap.decode_ms)} ms
      </p>
    </section>
  );
}

function EventFeed() {
  const events = useStore((s) => s.events);
  const focus = useStore((s) => s.focus);
  return (
    <section className="panel-block">
      <h2 className="eyebrow">Olay akışı</h2>
      {events.length === 0 ? (
        <p className="muted">Robot tarama yaptıkça olaylar burada görünür.</p>
      ) : (
        <ol className="feed">
          {events.map((e) => (
            <li key={e.id} className={`feed-${e.level}`}>
              <time dateTime={e.ts}>{fmtTime(e.ts)}</time>
              {e.location_id ? (
                <button onClick={() => focus(e.location_id!)}>{e.text}</button>
              ) : (
                <span>{e.text}</span>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

// --- göz ayrıntısı -------------------------------------------------------------

function LocationPanel({ id }: { id: number }) {
  const version = useStore((s) => s.locationVersion[id] ?? 0);
  const select = useStore((s) => s.select);
  const applyLocation = useStore((s) => s.applyLocation);
  const [detail, setDetail] = useState<LocationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .location(id)
      .then((d) => alive && (setDetail(d), setError(null)))
      .catch((e) => alive && setError((e as Error).message));
    return () => {
      alive = false;
    };
  }, [id, version]);

  useEffect(() => setNote(""), [id]);

  const review = async (action: "approve" | "correct") => {
    if (!detail?.observation_id) return;
    setBusy(true);
    try {
      applyLocation(await api.reviewAction(detail.observation_id, action, note || undefined));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const back = (
    <button className="back" onClick={() => select(null)}>
      ← Özete dön
    </button>
  );
  if (error)
    return (
      <div className="panel-scroll">
        {back}
        <p className="error">Göz bilgisi alınamadı: {error}</p>
      </div>
    );
  if (!detail || detail.id !== id)
    return (
      <div className="panel-scroll">
        {back}
        <p className="muted">Yükleniyor…</p>
      </div>
    );

  const st = detail.status;
  const read = new Set(detail.codes);
  const cap = detail.captures[0];
  const colorFor = (code: string) =>
    detail.unexpected.includes(code) ? STATUS.conflict.color : STATUS.verified.color;

  return (
    <div className="panel-scroll">
      {back}
      <section className="panel-block loc-head">
        <h2 className="loc-code">{detail.code}</h2>
        <p className="loc-where">
          {detail.rack_code} rafı · {detail.level}. seviye · {detail.position}. göz
          {detail.camera_height_mm != null && <> · kamera {detail.camera_height_mm} mm</>}
        </p>
        <p className="loc-status">
          <span className="chip" style={{ ["--c" as string]: st ? STATUS[st].color : STATUS.pending.color }}>
            {st ? STATUS[st].label : "Taranmadı"}
          </span>
          {detail.reason && <span>{detail.reason}</span>}
        </p>
      </section>

      <section className="panel-block">
        <h3 className="eyebrow">Beklenen ({detail.expected_items.length})</h3>
        {detail.expected_items.length === 0 ? (
          <p className="muted">Stok kaydına göre bu göz boş olmalı.</p>
        ) : (
          <ul className="codes">
            {detail.expected_items.map((e) => {
              const mark = st == null ? "pending" : read.has(e.code) ? "ok" : st === "unreadable" ? "unknown" : "missing";
              return (
                <li key={e.code} className={`code-${mark}`}>
                  <span className="mark" aria-hidden="true">
                    {mark === "ok" ? "✓" : mark === "missing" ? "✕" : mark === "unknown" ? "?" : "·"}
                  </span>
                  <code>{e.code}</code>
                  <span className="desc">{e.description}</span>
                  <span className="sr-only">
                    {mark === "ok" ? "okundu" : mark === "missing" ? "bulunamadı" : mark === "unknown" ? "okunamadı" : "taranmadı"}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
        {detail.unexpected.length > 0 && (
          <>
            <h3 className="eyebrow">Beklenmeyen ({detail.unexpected.length})</h3>
            <ul className="codes">
              {detail.unexpected.map((c) => (
                <li key={c} className="code-unexpected">
                  <span className="mark" aria-hidden="true">!</span>
                  <code>{c}</code>
                  <span className="desc">Bu göze kayıtlı değil</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      {cap && (
        <section className="panel-block">
          <h3 className="eyebrow">Kanıt görüntüsü</h3>
          <a href={cap.image_url} target="_blank" rel="noreferrer" className="evidence-link">
            <Evidence
              src={cap.thumb_url}
              width={cap.width}
              height={cap.height}
              reads={cap.reads}
              highlight={colorFor}
              alt={`${detail.code} gözünün kamera görüntüsü`}
            />
          </a>
          <p className="meta">
            {cap.camera_id} · {cap.vertical_position_mm != null && <>{Math.round(cap.vertical_position_mm)} mm · </>}
            keskinlik {cap.sharpness} · çözme {Math.round(cap.decode_ms)} ms ·{" "}
            {cap.reads.map((r) => r.method).filter((m, i, a) => a.indexOf(m) === i).join("+") || "kod yok"}
          </p>
        </section>
      )}

      {detail.review_status === "pending" && (
        <section className="panel-block review-box">
          <h3 className="eyebrow">Manuel kontrol</h3>
          <label className="field">
            <span>Not (isteğe bağlı)</span>
            <textarea
              rows={2}
              value={note}
              maxLength={512}
              placeholder="Örn. koli B02-1-2 gözünden alınıp yerine kondu"
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <div className="actions">
            <button className="btn" disabled={busy} onClick={() => review("approve")}>
              Sonucu onayla
            </button>
            <button className="btn btn-primary" disabled={busy} onClick={() => review("correct")}>
              Sahada düzeltildi
            </button>
          </div>
        </section>
      )}
      {(detail.review_status === "approved" || detail.review_status === "corrected") && (
        <section className="panel-block">
          <p className="reviewed">
            {detail.review_status === "approved" ? "Sonuç onaylandı" : "Sahada düzeltildi"}
            {detail.review_note && <> — {detail.review_note}</>}
          </p>
        </section>
      )}

      {detail.history.length > 1 && (
        <section className="panel-block">
          <h3 className="eyebrow">Geçmiş</h3>
          <ol className="history">
            {detail.history.map((h) => (
              <li key={h.scan_id}>
                <i style={{ background: STATUS[h.status].color }} />
                <code>{h.scan_id}</code>
                <span>{STATUS[h.status].label}</span>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}
