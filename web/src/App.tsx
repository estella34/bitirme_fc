import { Suspense, lazy, useEffect } from "react";
import { Overlay } from "./components/Overlay";
import { SidePanel } from "./components/SidePanel";
import { TopBar } from "./components/TopBar";
import { DecodePage } from "./pages/DecodePage";
import { ReviewPage } from "./pages/ReviewPage";
import { ScansPage } from "./pages/ScansPage";
import { useStore } from "./store";

// 3B sahne (three.js) ayrı paket: diğer sayfalar hızlı açılsın.
const Scene = lazy(() => import("./three/Scene").then((m) => ({ default: m.Scene })));

export function App() {
  const init = useStore((s) => s.init);
  const view = useStore((s) => s.view);
  const error = useStore((s) => s.error);
  const hasTwin = useStore((s) => s.twin != null);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <div className="app">
      <TopBar />
      {error && (
        <p className="banner" role="alert">
          {error}. Sunucu açılınca sayfa kendiliğinden bağlanır.
        </p>
      )}
      {view === "depo" && (
        <div className="twin">
          <div className="stage">
            {hasTwin ? (
              <Suspense fallback={<p className="stage-msg">3B sahne yükleniyor…</p>}>
                <Scene />
              </Suspense>
            ) : (
              <p className="stage-msg">Depo verisi bekleniyor…</p>
            )}
            {hasTwin && <Overlay />}
          </div>
          <SidePanel />
        </div>
      )}
      {view === "inceleme" && <ReviewPage />}
      {view === "taramalar" && <ScansPage />}
      {view === "okuma" && <DecodePage />}
    </div>
  );
}
