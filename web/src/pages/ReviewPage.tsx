import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { STATUS } from "../format";
import { useStore } from "../store";
import type { ReviewItem } from "../types";

export function ReviewPage() {
  const warehouseId = useStore((s) => s.warehouseId);
  const summaryPending = useStore((s) => s.summary?.pending_review);
  const focus = useStore((s) => s.focus);
  const setView = useStore((s) => s.setView);
  const applyLocation = useStore((s) => s.applyLocation);
  const [items, setItems] = useState<ReviewItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (warehouseId == null) return;
    api
      .review(warehouseId)
      .then((r) => (setItems(r), setError(null)))
      .catch((e) => setError((e as Error).message));
  }, [warehouseId]);

  // Kuyruk canlı değişir (yeni tarama, başka operatörün onayı): özet sayısı değişince tazele.
  useEffect(load, [load, summaryPending]);

  const act = async (item: ReviewItem, action: "approve" | "correct") => {
    if (!item.observation_id) return;
    const state = await api.reviewAction(item.observation_id, action);
    applyLocation(state);
    setItems((cur) => cur?.filter((i) => i.id !== item.id) ?? null);
  };

  const show = (id: number) => {
    focus(id);
    setView("depo");
  };

  return (
    <main className="page">
      <header className="page-head">
        <h1>İnceleme</h1>
        <p>
          Robotun emin olamadığı gözler. Sahada kontrol edip sonucu onaylayın ya da düzeltildi olarak
          işaretleyin; onaylanan kayıt stok raporuna kesin bilgi olarak geçer.
        </p>
      </header>
      {error && <p className="error">Kuyruk alınamadı: {error}</p>}
      {items && items.length === 0 && (
        <div className="empty-state">
          <p>İncelenecek göz yok.</p>
          <p className="muted">Robot bir çelişki ya da okunamayan koli bulduğunda burada görünür.</p>
        </div>
      )}
      <div className="cards">
        {items?.map((it) => (
          <article key={it.id} className="card" style={{ ["--c" as string]: STATUS[it.status ?? "conflict"].color }}>
            {it.thumb_url && <img src={it.thumb_url} alt={`${it.code} kamera görüntüsü`} loading="lazy" />}
            <div className="card-body">
              <h2 className="loc-code sm">{it.code}</h2>
              <p className="loc-status">
                <span className="chip" style={{ ["--c" as string]: STATUS[it.status ?? "conflict"].color }}>
                  {STATUS[it.status ?? "conflict"].label}
                </span>
                <span>{it.reason}</span>
              </p>
              <dl className="diff">
                {it.missing.length > 0 && (
                  <div>
                    <dt>Bulunamayan</dt>
                    <dd>{it.missing.map((c) => <code key={c}>{c}</code>)}</dd>
                  </div>
                )}
                {it.unexpected.length > 0 && (
                  <div>
                    <dt>Beklenmeyen</dt>
                    <dd>{it.unexpected.map((c) => <code key={c}>{c}</code>)}</dd>
                  </div>
                )}
                <div>
                  <dt>Görünen koli</dt>
                  <dd>{it.box_count ?? "bilinmiyor"}</dd>
                </div>
              </dl>
              <div className="actions">
                <button className="btn btn-ghost" onClick={() => show(it.id)}>
                  3B'de göster
                </button>
                <button className="btn" onClick={() => act(it, "approve")}>
                  Sonucu onayla
                </button>
                <button className="btn btn-primary" onClick={() => act(it, "correct")}>
                  Sahada düzeltildi
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
