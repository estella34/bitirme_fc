import { Component, type ReactNode } from "react";

/**
 * 3B sahne çökerse (ör. tarayıcıda WebGL yok ya da GPU bağlamı kayboldu) bütün sayfa beyaza
 * dönmesin: yalnız sahnenin yerinde açıklama ve yeniden deneme düğmesi görünür.
 */
export class SceneBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="stage-msg" role="alert">
        <p>3B sahne bu tarayıcıda açılamadı (WebGL kullanılamıyor).</p>
        <p className="muted">Diğer sekmeler çalışır. Jetson'daki Chromium'u menüdeki kısayoldan açın.</p>
        <button className="btn" onClick={() => this.setState({ error: null })}>
          Yeniden dene
        </button>
      </div>
    );
  }
}
