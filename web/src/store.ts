import { create } from "zustand";
import { api } from "./api";
import { appendCells, clearLive, robotLive, setLidarPalette, setScan, trailBuf } from "./buffers";
import { SCENE, applyTheme, currentTheme, savedTheme, type ThemeName } from "./theme";
import type {
  Capture,
  DemoStatus,
  FeedEvent,
  LocationState,
  RobotState,
  Scan,
  Summary,
  Twin,
  Warehouse,
} from "./types";

export type View = "depo" | "inceleme" | "taramalar" | "okuma";
export type CameraMode = "perspektif" | "ust" | "takip" | "odak";

interface State {
  view: View;
  warehouses: Warehouse[];
  warehouseId: number | null;
  twin: Twin | null;
  locations: Record<number, LocationState>;
  summary: Summary | null;
  demo: DemoStatus;
  events: FeedEvent[];
  selectedId: number | null;
  hoverId: number | null;
  conn: "connecting" | "open" | "closed";
  robot: RobotState | null;
  lastCapture: Capture | null;
  layers: { map: boolean; beam: boolean; trail: boolean };
  camera: { mode: CameraMode; nonce: number };
  /** Bir gözün ayrıntısı yeniden çekilmeli (canlı güncelleme geldi). */
  locationVersion: Record<number, number>;
  error: string | null;
  theme: ThemeName;

  setView: (v: View) => void;
  toggleTheme: () => void;
  select: (id: number | null) => void;
  /** Gözü seçer ve kamerayı ona çevirir (panelden, listeden yapılan seçimler için). */
  focus: (id: number) => void;
  hover: (id: number | null) => void;
  toggleLayer: (k: keyof State["layers"]) => void;
  setCamera: (mode: CameraMode) => void;
  init: () => Promise<void>;
  loadWarehouse: (id: number) => Promise<void>;
  refreshSummary: () => void;
  startDemo: (speed: number) => Promise<void>;
  stopDemo: () => Promise<void>;
  applyLocation: (loc: LocationState) => void;
}

let eventSeq = 0;
let socket: WebSocket | null = null;
let socketFor: number | null = null;
let reconnectTimer: number | undefined;
let pingTimer: number | undefined;
let summaryTimer: number | undefined;
let lastRobotUi = 0;

export const useStore = create<State>((set, get) => ({
  view: viewFromHash(),
  warehouses: [],
  warehouseId: null,
  twin: null,
  locations: {},
  summary: null,
  demo: { running: false },
  events: [],
  selectedId: null,
  hoverId: null,
  conn: "connecting",
  robot: null,
  lastCapture: null,
  layers: { map: true, beam: true, trail: true },
  camera: { mode: "perspektif", nonce: 0 },
  locationVersion: {},
  error: null,
  theme: currentTheme(),

  setView: (view) => {
    if (location.hash !== `#/${view}`) location.hash = `#/${view}`;
    set({ view });
  },
  toggleTheme: () => {
    const theme: ThemeName = get().theme === "dark" ? "light" : "dark";
    applyTheme(theme, true);
    setLidarPalette(SCENE[theme].lidar);
    set({ theme });
  },
  select: (selectedId) => set({ selectedId }),
  focus: (id) => set((s) => ({ selectedId: id, camera: { mode: "odak", nonce: s.camera.nonce + 1 } })),
  hover: (hoverId) => set({ hoverId }),
  toggleLayer: (k) => set((s) => ({ layers: { ...s.layers, [k]: !s.layers[k] } })),
  setCamera: (mode) => set((s) => ({ camera: { mode, nonce: s.camera.nonce + 1 } })),

  init: async () => {
    try {
      const warehouses = await api.warehouses();
      set({ warehouses, error: null });
      if (warehouses.length) await get().loadWarehouse(warehouses[0].id);
    } catch (e) {
      set({ error: `Sunucuya ulaşılamadı: ${(e as Error).message}` });
      window.setTimeout(() => get().init(), 3000);
    }
  },

  loadWarehouse: async (id) => {
    const [twin, map, summary, demo] = await Promise.all([
      api.twin(id),
      api.map(id),
      api.summary(id),
      api.demo(),
    ]);
    clearLive();
    appendCells(map.cells, map.resolution);
    trailBuf.points = twin.trail;
    trailBuf.version++;
    Object.assign(robotLive, twin.robot, { seen: twin.trail.length > 0 || twin.robot.online });
    set({
      warehouseId: id,
      twin,
      locations: indexLocations(twin),
      summary,
      demo,
      robot: twin.robot,
    });
    connect(id);
  },

  refreshSummary: () => {
    window.clearTimeout(summaryTimer);
    summaryTimer = window.setTimeout(async () => {
      const id = get().warehouseId;
      if (id != null) set({ summary: await api.summary(id) });
    }, 400);
  },

  startDemo: async (speed) => {
    const demo = await api.demoStart(speed);
    set({ demo, selectedId: null });
  },
  stopDemo: async () => set({ demo: await api.demoStop() }),

  applyLocation: (loc) =>
    set((s) => ({
      locations: { ...s.locations, [loc.id]: loc },
      locationVersion: { ...s.locationVersion, [loc.id]: (s.locationVersion[loc.id] ?? 0) + 1 },
    })),
}));

function indexLocations(twin: Twin): Record<number, LocationState> {
  const out: Record<number, LocationState> = {};
  for (const r of twin.racks) for (const l of r.locations) out[l.id] = l;
  return out;
}

function viewFromHash(): View {
  const v = location.hash.replace("#/", "");
  return (["depo", "inceleme", "taramalar", "okuma"] as View[]).includes(v as View)
    ? (v as View)
    : "depo";
}
window.addEventListener("hashchange", () => useStore.setState({ view: viewFromHash() }));

// LiDAR renkleri ilk temaya göre; kullanıcı tema seçmediyse sistem tercihini izle.
setLidarPalette(SCENE[currentTheme()].lidar);
window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
  if (savedTheme()) return;
  const theme: ThemeName = e.matches ? "light" : "dark";
  applyTheme(theme, false);
  setLidarPalette(SCENE[theme].lidar);
  useStore.setState({ theme });
});

// --- canlı bağlantı -----------------------------------------------------------

type Message =
  | { type: "robot"; robot: RobotState; trail_point?: [number, number]; scan?: number[] }
  | { type: "map"; resolution: number; cells: number[] }
  | { type: "location"; location: LocationState }
  | { type: "capture"; capture: Capture }
  | { type: "scan"; scan: Scan }
  | { type: "event"; level: FeedEvent["level"]; text: string; ts: string; location_id?: number }
  | { type: "reset" }
  | { type: "twin_changed" };

function connect(warehouseId: number) {
  if (socket && socketFor === warehouseId && socket.readyState <= WebSocket.OPEN) return;
  socket?.close();
  window.clearTimeout(reconnectTimer);
  window.clearInterval(pingTimer);
  socketFor = warehouseId;
  useStore.setState({ conn: "connecting" });

  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/ws?warehouse_id=${warehouseId}`);
  socket = ws;
  ws.onopen = () => {
    useStore.setState({ conn: "open" });
    pingTimer = window.setInterval(() => ws.readyState === WebSocket.OPEN && ws.send("p"), 20000);
  };
  ws.onclose = () => {
    if (socket !== ws) return;
    useStore.setState({ conn: "closed" });
    window.clearInterval(pingTimer);
    reconnectTimer = window.setTimeout(async () => {
      // Kopukluk sırasında kaçan güncellemeler için durumu baştan yükle.
      const id = useStore.getState().warehouseId;
      if (id != null) await useStore.getState().loadWarehouse(id).catch(() => connect(id));
    }, 2000);
  };
  ws.onmessage = (ev) => handle(JSON.parse(ev.data) as Message);
}

function handle(msg: Message) {
  const st = useStore.getState();
  switch (msg.type) {
    case "robot": {
      Object.assign(robotLive, msg.robot, { seen: true });
      if (msg.scan) setScan(msg.scan);
      if (msg.trail_point) {
        const pts = trailBuf.points;
        const last = pts[pts.length - 1];
        if (!last || Math.hypot(last[0] - msg.trail_point[0], last[1] - msg.trail_point[1]) > 0.1) {
          pts.push(msg.trail_point);
          trailBuf.version++;
        }
      }
      const now = performance.now();
      if (now - lastRobotUi > 200) {
        lastRobotUi = now;
        useStore.setState({ robot: msg.robot });
      }
      break;
    }
    case "map":
      appendCells(msg.cells, msg.resolution);
      break;
    case "location":
      st.applyLocation(msg.location);
      st.refreshSummary();
      break;
    case "capture":
      robotLive.flashAt = performance.now();
      useStore.setState({ lastCapture: msg.capture });
      break;
    case "scan":
      st.refreshSummary();
      api.demo().then((demo) => useStore.setState({ demo }));
      break;
    case "event":
      useStore.setState((s) => ({
        events: [
          { id: ++eventSeq, ts: msg.ts, level: msg.level, text: msg.text, location_id: msg.location_id },
          ...s.events,
        ].slice(0, 80),
      }));
      break;
    case "reset":
      clearLive();
      if (st.warehouseId != null) {
        api.twin(st.warehouseId).then((twin) =>
          useStore.setState({ twin, locations: indexLocations(twin), lastCapture: null }),
        );
        api.demo().then((demo) => useStore.setState({ demo }));
      }
      st.refreshSummary();
      break;
    case "twin_changed":
      if (st.warehouseId != null) {
        api.twin(st.warehouseId).then((twin) =>
          useStore.setState({ twin, locations: indexLocations(twin) }),
        );
      }
      st.refreshSummary();
      break;
  }
}

// Demo ilerlemesini (yüzde) arada bir tazele.
window.setInterval(() => {
  if (useStore.getState().demo.running) api.demo().then((demo) => useStore.setState({ demo }));
}, 1500);
