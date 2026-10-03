import { useEffect, useState } from "react";
import { api } from "../api";
import { Evidence } from "../components/Evidence";
import type { DecodeResult } from "../types";

/** Okuma testi: telefonla çekilen bir koli fotoğrafında kod çözücünün ne bulduğunu gösterir. */
export function DecodePage() {
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [result, setResult] = useState<DecodeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);

  useEffect(() => () => void (url && URL.revokeObjectURL(url)), [url]);

  const pick = async (f: File | undefined) => {
    if (!f) return;
    setFile(f);
    setUrl(URL.createObjectURL(f));
    setResult(null);
    setError(null);
    setBusy(true);
    try {
      setResult(await api.decode(f));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page">
      <header className="page-head">
        <h1>Okuma testi</h1>
        <p>
          Bir koli etiketinin fotoğrafını yükleyin; sistem robotla aynı çözücüyü kullanarak QR ve
          barkodları bulur. Telefondan açarsanız doğrudan kamerayla çekebilirsiniz. Görüntü kaydedilmez.
        </p>
      </header>

      <label
        className={`dropzone${drag ? " is-drag" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          pick(e.dataTransfer.files[0]);
        }}
      >
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => pick(e.target.files?.[0])} />
        <strong>{file ? "Başka bir fotoğraf seçin" : "Fotoğraf seçin ya da buraya bırakın"}</strong>
        <span>JPEG, PNG veya WebP</span>
      </label>
      <label className="btn btn-ghost camera-btn">
        <input
          type="file"
          accept="image/*"
          capture="environment"
          className="sr-only"
          onChange={(e) => pick(e.target.files?.[0])}
        />
        Kamerayla çek
      </label>

      {busy && <p className="muted">Kodlar aranıyor…</p>}
      {error && <p className="error">Görüntü işlenemedi: {error}</p>}

      {result && url && (
        <div className="decode-result">
          <Evidence
            src={url}
            width={result.width}
            height={result.height}
            reads={result.codes}
            alt="Yüklenen fotoğraf ve bulunan kodlar"
          />
          <div>
            <p className="headline">
              {result.codes.length === 0 ? (
                <>Kod bulunamadı.</>
              ) : (
                <>
                  <b className="ok">{result.codes.length}</b> kod bulundu
                </>
              )}
            </p>
            <p className="meta">
              {result.width}×{result.height} px · keskinlik {result.sharpness} · {result.elapsed_ms} ms ·
              denenen: {result.methods_tried.join(" → ")}
            </p>
            {result.codes.length === 0 && (
              <p className="muted">
                Etikete daha yakından, düz açıyla ve iyi ışıkta çekmeyi deneyin. Keskinlik değeri
                düşükse fotoğraf bulanıktır.
              </p>
            )}
            <ul className="codes">
              {result.codes.map((c) => (
                <li key={c.text + c.polygon[0].join()} className="code-ok">
                  <span className="mark" aria-hidden="true">
                    ✓
                  </span>
                  <code>{c.text}</code>
                  <span className="desc">
                    {c.symbology} · {c.method}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </main>
  );
}
