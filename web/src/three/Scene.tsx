import { Grid, Line, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import { Vector3 } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { robotLive } from "../buffers";
import { useStore } from "../store";
import type { Rack, Warehouse } from "../types";
import { w } from "./coords";
import { MapCloud, ScanBeam } from "./MapCloud";
import { Racks, usePalette } from "./Racks";
import { Robot, Trail } from "./Robot";

export function Scene() {
  const twin = useStore((s) => s.twin);
  const layers = useStore((s) => s.layers);
  const select = useStore((s) => s.select);
  const palette = usePalette();
  if (!twin) return null;
  const { warehouse } = twin;
  const span = Math.max(warehouse.width_m, warehouse.length_m);

  return (
    <Canvas
      dpr={[1, 2]}
      gl={{ antialias: true }}
      camera={{ fov: 40, near: 0.1, far: span * 8, position: presetFor("perspektif", warehouse)[0] }}
      onCreated={({ camera }) => camera.lookAt(...presetFor("perspektif", warehouse)[1])}
      onPointerMissed={() => select(null)}
    >
      <color attach="background" args={[palette.bg]} />
      <fog attach="fog" args={[palette.bg, span * 1.6, span * 4]} />
      <hemisphereLight args={[palette.hemiSky, palette.hemiGround, palette.hemi]} />
      <directionalLight
        position={[warehouse.width_m * 0.7, 14, warehouse.length_m * 0.4]}
        intensity={palette.sun}
      />
      <ambientLight intensity={palette.ambient} />

      <Floor warehouse={warehouse} racks={twin.racks} />
      <MapCloud visible={layers.map} />
      <ScanBeam visible={layers.beam} />
      <Racks />
      <Robot />
      <Trail visible={layers.trail} />
      <CameraRig warehouse={warehouse} />
    </Canvas>
  );
}

function Floor({ warehouse, racks }: { warehouse: Warehouse; racks: Rack[] }) {
  const palette = usePalette();
  const W = warehouse.width_m;
  const L = warehouse.length_m;
  const outline = useMemo(
    () => [w(0, 0, 0.01), w(W, 0, 0.01), w(W, L, 0.01), w(0, L, 0.01), w(0, 0, 0.01)],
    [W, L],
  );
  // Raf önlerindeki sarı zemin şeridi (gerçek depolardaki koridor işareti).
  const aisleLines = useMemo(
    () =>
      racks.map((r) => {
        const yaw = (r.yaw_deg * Math.PI) / 180;
        const c = Math.cos(yaw);
        const s = Math.sin(yaw);
        const len = r.positions * r.bay_width_m;
        const at = (lx: number, ly: number) => w(r.x + c * lx - s * ly, r.y + s * lx + c * ly, 0.012);
        return { id: r.id, points: [at(-0.1, -0.35), at(len + 0.1, -0.35)] };
      }),
    [racks],
  );

  return (
    <group>
      <mesh rotation-x={-Math.PI / 2} position={[W / 2, -0.002, -L / 2]}>
        <planeGeometry args={[W + 8, L + 8]} />
        <meshStandardMaterial color={palette.floor} roughness={0.95} />
      </mesh>
      <Grid
        position={[W / 2, 0, -L / 2]}
        args={[W + 8, L + 8]}
        cellSize={1}
        cellThickness={0.6}
        cellColor={palette.gridCell}
        sectionSize={5}
        sectionThickness={1}
        sectionColor={palette.gridSection}
        fadeDistance={Math.max(W, L) * 2.2}
        fadeStrength={1.5}
      />
      <Line points={outline} color={palette.outline} lineWidth={1} dashed dashSize={0.5} gapSize={0.3} />
      {aisleLines.map((a) => (
        <Line key={a.id} points={a.points} color={palette.aisle} lineWidth={2.2} transparent opacity={0.7} />
      ))}
    </group>
  );
}

type Preset = [pos: [number, number, number], target: [number, number, number]];

function presetFor(mode: "perspektif" | "ust", wh: Warehouse): Preset {
  const W = wh.width_m;
  const L = wh.length_m;
  const span = Math.max(W, L);
  const center: [number, number, number] = [W / 2, 0, -L / 2];
  if (mode === "ust") return [[W / 2, span * 1.25, -L / 2 + 0.01], center];
  return [[W * 0.9, span * 0.72, L * 0.72], [W / 2, 0, -L / 2 + 0.8]];
}

/** Seçilen gözün önüne, hafif yandan ve yukarıdan bakan kamera konumu. */
function focusPreset(rack: Rack, level: number, position: number): Preset {
  const yaw = (rack.yaw_deg * Math.PI) / 180;
  const c = Math.cos(yaw);
  const s = Math.sin(yaw);
  const lx = (position - 0.5) * rack.bay_width_m;
  const ly = rack.depth_m / 2;
  const z = (level - 0.5) * rack.level_height_m;
  const cx = rack.x + c * lx - s * ly;
  const cy = rack.y + s * lx + c * ly;
  // Ön yüz normali (koridora doğru) ve raf ekseni, dünya koordinatında.
  const [nx, ny] = [s, -c];
  const [ax, ay] = [c, s];
  const eye = w(cx + nx * 3.4 + ax * 1.3, cy + ny * 3.4 + ay * 1.3, z + 1.7);
  return [eye, w(cx, cy, z)];
}

/** Kamera önayarları arasında yumuşak geçiş ve robot takibi. */
function CameraRig({ warehouse }: { warehouse: Warehouse }) {
  const controls = useRef<OrbitControlsImpl>(null);
  const camera = useThree((s) => s.camera);
  const mode = useStore((s) => s.camera.mode);
  const nonce = useStore((s) => s.camera.nonce);
  // Raflar ve depo nesnesi her canlı tazelemede yenilenir; kamerayı sarsmamak için
  // efekt bağımlılığı yapılmaz, güncel değer ref'ten okunur.
  const racks = useRef<Rack[] | undefined>(undefined);
  racks.current = useStore((s) => s.twin?.racks);
  const whRef = useRef(warehouse);
  whRef.current = warehouse;
  const goal = useRef<{ pos: Vector3; target: Vector3; until: number } | null>(null);
  const reduced = useMemo(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches, []);

  useEffect(() => {
    const c = controls.current;
    if (!c) return;
    if (mode === "takip") {
      goal.current = null;
      return;
    }
    let preset: Preset | null = null;
    if (mode === "odak") {
      const id = useStore.getState().selectedId;
      const loc = id != null ? useStore.getState().locations[id] : undefined;
      const rack = loc && racks.current?.find((r) => r.id === loc.rack_id);
      if (loc && rack) preset = focusPreset(rack, loc.level, loc.position);
    } else {
      preset = presetFor(mode, whRef.current);
    }
    if (!preset) return;
    const [p, t] = preset;
    goal.current = { pos: new Vector3(...p), target: new Vector3(...t), until: performance.now() + 1400 };
    if (nonce === 0) {
      camera.position.set(...p);
      c.target.set(...t);
      c.update();
      goal.current = null;
    }
  }, [mode, nonce, warehouse.id, camera]);

  useFrame((_, dt) => {
    const c = controls.current;
    if (!c) return;
    const k = reduced ? 1 : 1 - Math.exp(-dt * 4.5);
    if (mode === "takip" && robotLive.seen) {
      const [rx, , rz] = w(robotLive.x, robotLive.y, 0);
      const target = new Vector3(rx, 0.8, rz);
      const offset = camera.position.clone().sub(c.target);
      if (offset.length() > 9 || offset.y < 1.5) offset.set(3.2, 3.6, 4.6);
      c.target.lerp(target, k);
      camera.position.copy(c.target).add(offset);
      c.update();
      return;
    }
    const g = goal.current;
    if (!g) return;
    camera.position.lerp(g.pos, k);
    c.target.lerp(g.target, k);
    c.update();
    if (performance.now() > g.until) goal.current = null;
  });

  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enableDamping
      dampingFactor={0.08}
      maxPolarAngle={Math.PI / 2.05}
      minDistance={1.5}
      maxDistance={Math.max(warehouse.width_m, warehouse.length_m) * 2.5}
      onStart={() => {
        goal.current = null;
      }}
    />
  );
}
