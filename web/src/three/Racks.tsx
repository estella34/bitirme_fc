import { Edges, Html } from "@react-three/drei";
import { useFrame, type ThreeEvent } from "@react-three/fiber";
import { createContext, memo, useContext, useEffect, useMemo, useRef, type ReactElement, type RefObject } from "react";
import { type Group, MeshBasicMaterial, MeshStandardMaterial, type Object3D } from "three";
import { STATUS, hash01 } from "../format";
import { useStore } from "../store";
import { SCENE, type ScenePalette } from "../theme";
import type { LocationState, Rack } from "../types";
import { deg, w } from "./coords";

const BEAM_H = 0.07;
const DECK_Z = 0.09; // kolinin oturduğu yükseklik (göz tabanına göre)

type Kind = "ok" | "ghost" | "missing" | "unexpected" | "unknown" | "observed";

// Paylaşılan malzemeler: yüzlerce koli aynı birkaç malzemeyi kullanır.
// Renkleri temaya göre applyPalette() ile güncellenir.
const mat = {
  kraft: new MeshStandardMaterial({ roughness: 0.88 }),
  ghost: new MeshStandardMaterial({ roughness: 1, transparent: true, depthWrite: false }),
  missing: new MeshBasicMaterial({ transparent: true, opacity: 0.2, depthWrite: false }),
  unexpected: new MeshStandardMaterial({ emissiveIntensity: 0.35, roughness: 0.6 }),
  unknown: new MeshStandardMaterial({ emissiveIntensity: 0.25, roughness: 0.7 }),
  labelOk: new MeshBasicMaterial(),
  labelObserved: new MeshBasicMaterial(),
  upright: new MeshStandardMaterial({ metalness: 0.35, roughness: 0.45 }),
  beam: new MeshStandardMaterial({ metalness: 0.25, roughness: 0.5 }),
  deck: new MeshStandardMaterial({ transparent: true, roughness: 1 }),
  hit: new MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }),
  empty: new MeshBasicMaterial({ transparent: true, opacity: 0.35, depthWrite: false }),
};

function applyPalette(p: ScenePalette) {
  mat.kraft.color.set(p.kraft);
  mat.ghost.color.set(p.kraft);
  mat.ghost.opacity = p.ghostOpacity;
  mat.missing.color.set(p.status.conflict);
  mat.unexpected.color.set(p.status.conflict);
  mat.unexpected.emissive.set(p.status.conflict);
  mat.unknown.color.set(p.status.unreadable);
  mat.unknown.emissive.set(p.status.unreadable);
  mat.labelOk.color.set(p.status.verified);
  mat.labelObserved.color.set(p.status.observed);
  mat.upright.color.set(p.upright);
  mat.beam.color.set(p.beam);
  mat.deck.color.set(p.deck);
  mat.deck.opacity = p.deckOpacity;
  mat.empty.color.set(p.status.empty);
}
applyPalette(SCENE.dark);

/**
 * Etiket gizleme: raf tabelaları ve göz etiketleri HTML olduğu için derinlik testine girmez.
 * drei Html'in `occlude` özelliği, bu gruptaki raf/koli geometrisine ışın atıp arkada kalan
 * etiketi gizler. Kenar çizgileri (Edges) ışın hedefi değildir; aksi hâlde çizgi eşiği
 * yüzünden etiketler gereksiz yere kaybolur.
 */
const OccluderContext = createContext<RefObject<Group | null> | null>(null);
const noRaycast = () => null;

/** Etkin temanın 3B paleti. */
export function usePalette(): ScenePalette {
  return SCENE[useStore((s) => s.theme)];
}

/** Gözün son durumundan sahnede çizilecek kolileri çıkarır. */
export function boxItems(loc: LocationState): { code: string; kind: Kind }[] {
  if (loc.status == null) return loc.expected.map((code) => ({ code, kind: "ghost" }));
  const read = new Set(loc.codes);
  const items: { code: string; kind: Kind }[] = [];
  for (const code of loc.expected) {
    if (read.has(code)) items.push({ code, kind: "ok" });
    else if (loc.status === "unreadable") items.push({ code, kind: "unknown" });
    else items.push({ code, kind: "missing" });
  }
  for (const code of loc.unexpected) items.push({ code, kind: "unexpected" });
  if (loc.status === "observed")
    for (const code of loc.codes) if (!loc.expected.includes(code)) items.push({ code, kind: "observed" });
  // Görülen ama hiçbir koda bağlanamayan koliler (kod okunamadı).
  const physical = items.filter((i) => i.kind !== "missing").length;
  for (let i = physical; i < (loc.box_count ?? 0); i++) items.push({ code: `?${i}`, kind: "unknown" });
  return items;
}

export function Racks() {
  const racks = useStore((s) => s.twin?.racks);
  const palette = usePalette();
  const reduced = useMemo(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches, []);
  useEffect(() => applyPalette(palette), [palette]);

  // "Hayalet koli": kayıp kolinin dolgusu yavaşça nefes alır.
  useFrame(({ clock }) => {
    if (!reduced) mat.missing.opacity = 0.12 + 0.16 * (0.5 + 0.5 * Math.sin(clock.elapsedTime * 3.2));
  });

  const occluders = useRef<Group>(null);
  if (!racks) return null;
  return (
    <OccluderContext.Provider value={occluders}>
      <group ref={occluders}>
        {racks.map((r) => (
          <RackModel key={r.id} rack={r} />
        ))}
      </group>
    </OccluderContext.Provider>
  );
}

function useOccluders(): RefObject<Object3D>[] | undefined {
  const ref = useContext(OccluderContext);
  // Grup, etiketlerden önce bağlanır; ilk karede ref doludur.
  return ref ? [ref as RefObject<Object3D>] : undefined;
}

const RackModel = memo(function RackModel({ rack }: { rack: Rack }) {
  const length = rack.positions * rack.bay_width_m;
  const height = rack.levels * rack.level_height_m + 0.12;
  const d = rack.depth_m;
  const locIds = useMemo(() => rack.locations.map((l) => l.id), [rack.locations]);
  const occlude = useOccluders();

  const frame = useMemo(() => {
    const parts: ReactElement[] = [];
    for (let i = 0; i <= rack.positions; i++) {
      for (const ly of [0, d]) {
        parts.push(
          <mesh key={`u${i}-${ly}`} material={mat.upright} position={[i * rack.bay_width_m, height / 2, -ly]}>
            <boxGeometry args={[0.06, height, 0.06]} />
          </mesh>,
        );
      }
    }
    for (let l = 0; l <= rack.levels; l++) {
      const z = l * rack.level_height_m + 0.05;
      for (const ly of [0, d]) {
        parts.push(
          <mesh key={`b${l}-${ly}`} material={mat.beam} position={[length / 2, z, -ly]}>
            <boxGeometry args={[length, BEAM_H, 0.045]} />
          </mesh>,
        );
      }
      if (l < rack.levels) {
        parts.push(
          <mesh
            key={`d${l}`}
            material={mat.deck}
            position={[length / 2, z + 0.04, -d / 2]}
            rotation-x={-Math.PI / 2}
          >
            <planeGeometry args={[length, d]} />
          </mesh>,
        );
      }
    }
    return parts;
  }, [rack.positions, rack.levels, rack.bay_width_m, rack.level_height_m, d, length, height]);

  return (
    <group position={w(rack.x, rack.y, 0)} rotation-y={deg(rack.yaw_deg)}>
      {frame}
      <Html
        position={[0.05, height + 0.3, 0]}
        zIndexRange={[5, 0]}
        occlude={occlude}
        style={{ pointerEvents: "none" }}
      >
        <div className="rack-sign">{rack.code}</div>
      </Html>
      {locIds.map((id) => (
        <LocationCell key={id} id={id} rack={rack} />
      ))}
    </group>
  );
});

function LocationCell({ id, rack }: { id: number; rack: Rack }) {
  const loc = useStore((s) => s.locations[id]);
  const selected = useStore((s) => s.selectedId === id);
  const hovered = useStore((s) => s.hoverId === id);
  const select = useStore((s) => s.select);
  const hover = useStore((s) => s.hover);
  const palette = usePalette();
  const occlude = useOccluders();
  if (!loc) return null;

  const bay = rack.bay_width_m;
  const lh = rack.level_height_m;
  const d = rack.depth_m;
  const cx = (loc.position - 0.5) * bay;
  const base = (loc.level - 1) * lh + DECK_Z;
  const cellCenter: [number, number, number] = [cx, base + (lh - DECK_Z) / 2, -d / 2];

  const items = boxItems(loc);
  const n = items.length;
  const gap = 0.05;
  const bw = n ? Math.min(0.36, (bay - 0.16 - gap * (n - 1)) / n) : 0;
  const bd = Math.min(d * 0.78, 0.56);
  const x0 = cx - (n * bw + (n - 1) * gap) / 2 + bw / 2;

  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    select(selected ? null : id);
  };

  return (
    <group>
      {items.map((it, i) => {
        const bh = Math.min(lh - 0.15, 0.24 + 0.11 * hash01(it.code));
        const pos: [number, number, number] = [x0 + i * (bw + gap), base + bh / 2, -0.06 - bd / 2];
        return <BoxModel key={it.code} kind={it.kind} size={[bw, bh, bd]} position={pos} />;
      })}
      {loc.status === "empty" && (
        <mesh material={mat.empty} position={[cx, base + 0.004, -d / 2]} rotation-x={-Math.PI / 2}>
          <planeGeometry args={[bay - 0.2, d - 0.2]} />
        </mesh>
      )}
      <mesh
        material={mat.hit}
        position={cellCenter}
        onClick={onClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          hover(id);
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          hover(null);
          document.body.style.cursor = "";
        }}
      >
        <boxGeometry args={[bay - 0.04, lh - DECK_Z, d]} />
        {(selected || hovered) && (
          <Edges color={selected ? palette.beam : palette.hover} threshold={10} renderOrder={2} raycast={noRaycast} />
        )}
      </mesh>
      {(selected || hovered) && (
        <Html
          // Üstteki kirişin önünde ve biraz üstünde: kirişin içine düşerse ışın onu gizler.
          position={[cx, base + lh + 0.06, 0.14]}
          center
          zIndexRange={[6, 0]}
          occlude={occlude}
          style={{ pointerEvents: "none" }}
        >
          <div className={`cell-tag${selected ? " is-selected" : ""}`}>
            <b>{loc.code}</b>
            <i style={{ background: loc.status ? STATUS[loc.status].color : STATUS.pending.color }} />
          </div>
        </Html>
      )}
    </group>
  );
}

function BoxModel({
  kind,
  size,
  position,
}: {
  kind: Kind;
  size: [number, number, number];
  position: [number, number, number];
}) {
  const [bw, bh, bd] = size;
  const palette = usePalette();
  const material =
    kind === "ok" || kind === "observed"
      ? mat.kraft
      : kind === "ghost"
        ? mat.ghost
        : kind === "missing"
          ? mat.missing
          : kind === "unexpected"
            ? mat.unexpected
            : mat.unknown;
  return (
    <group position={position}>
      <mesh material={material} renderOrder={kind === "missing" || kind === "ghost" ? 1 : 0}>
        <boxGeometry args={size} />
        {kind === "missing" && <Edges color={palette.status.conflict} threshold={10} raycast={noRaycast} />}
        {kind === "ghost" && <Edges color={palette.ghostEdge} threshold={10} raycast={noRaycast} />}
        {(kind === "ok" || kind === "observed") && (
          <Edges color={palette.kraftEdge} threshold={10} raycast={noRaycast} />
        )}
      </mesh>
      {(kind === "ok" || kind === "observed") && (
        <mesh
          material={kind === "ok" ? mat.labelOk : mat.labelObserved}
          position={[0, bh * 0.08, bd / 2 + 0.002]}
        >
          <planeGeometry args={[Math.min(bw * 0.45, 0.12), Math.min(bh * 0.35, 0.09)]} />
        </mesh>
      )}
    </group>
  );
}
