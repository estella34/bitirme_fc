import { Line } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef, useState } from "react";
import { type Group, type Mesh, MeshBasicMaterial, MeshStandardMaterial } from "three";
import { robotLive, trailBuf } from "../buffers";
import { BEAM } from "../format";
import { w } from "./coords";

const body = new MeshStandardMaterial({ color: "#2a3646", metalness: 0.3, roughness: 0.55 });
const dark = new MeshStandardMaterial({ color: "#121821", roughness: 0.9 });
const steel = new MeshStandardMaterial({ color: "#8fa2b8", metalness: 0.7, roughness: 0.3 });
const accent = new MeshStandardMaterial({ color: BEAM, emissive: BEAM, emissiveIntensity: 0.25 });
const lens = new MeshStandardMaterial({ color: "#0b0f14", metalness: 0.2, roughness: 0.1 });
const flash = new MeshBasicMaterial({ color: "#fff1dc", transparent: true, opacity: 0, depthWrite: false });

/**
 * Robot: yürüyen şasi + dikey mast + 4 kameralı taşıyıcı + LiDAR.
 * Robot ekseni: +x ileri, +y sol. Kameralar sol tarafa (rafa) bakar.
 */
export function Robot() {
  const group = useRef<Group>(null);
  const carriage = useRef<Group>(null);
  const ring = useRef<Mesh>(null);
  const reduced = useMemo(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches, []);
  const mast = useRef(robotLive.mast_mm);

  useFrame((_, dt) => {
    const g = group.current;
    if (!g) return;
    g.visible = robotLive.seen;
    const [tx, , tz] = w(robotLive.x, robotLive.y, 0);
    const k = reduced ? 1 : 1 - Math.exp(-dt * 14);
    g.position.x += (tx - g.position.x) * k;
    g.position.z += (tz - g.position.z) * k;
    let dy = robotLive.yaw - g.rotation.y;
    dy = Math.atan2(Math.sin(dy), Math.cos(dy));
    g.rotation.y += dy * k;
    mast.current += (robotLive.mast_mm - mast.current) * k;
    if (carriage.current) carriage.current.position.y = mast.current / 1000;
    if (ring.current && !reduced) ring.current.rotation.y += dt * 9;
    const age = performance.now() - robotLive.flashAt;
    flash.opacity = age < 450 ? 0.32 * (1 - age / 450) : 0;
  });

  return (
    <group ref={group}>
      {/* şasi */}
      <mesh material={body} position={[0, 0.2, 0]}>
        <boxGeometry args={[0.72, 0.24, 0.54]} />
      </mesh>
      <mesh material={accent} position={[0, 0.2, 0.272]}>
        <boxGeometry args={[0.72, 0.035, 0.005]} />
      </mesh>
      <mesh material={accent} position={[0, 0.2, -0.272]}>
        <boxGeometry args={[0.72, 0.035, 0.005]} />
      </mesh>
      {[-0.25, 0.25].map((x) =>
        [-0.29, 0.29].map((z) => (
          <mesh key={`${x}${z}`} material={dark} position={[x, 0.08, z]} rotation-x={Math.PI / 2}>
            <cylinderGeometry args={[0.08, 0.08, 0.05, 20]} />
          </mesh>
        )),
      )}
      {/* LiDAR (ön üstte) */}
      <mesh material={dark} position={[0.12, 0.36, 0]}>
        <cylinderGeometry args={[0.06, 0.065, 0.08, 24]} />
      </mesh>
      <mesh ref={ring} material={accent} position={[0.12, 0.41, 0]}>
        <cylinderGeometry args={[0.045, 0.045, 0.012, 6]} />
      </mesh>
      {/* yön oku */}
      <mesh material={accent} position={[0.52, 0.02, 0]} rotation-z={-Math.PI / 2}>
        <coneGeometry args={[0.07, 0.16, 3]} />
      </mesh>
      {/* mast rayları (sol kenarda) */}
      {[-0.2, 0.06].map((x) => (
        <mesh key={x} material={steel} position={[x, 1.16, -0.2]}>
          <boxGeometry args={[0.035, 1.72, 0.035]} />
        </mesh>
      ))}
      <mesh material={steel} position={[-0.07, 2.03, -0.2]}>
        <boxGeometry args={[0.32, 0.03, 0.05]} />
      </mesh>
      {/* kamera taşıyıcısı: mast_mm yüksekliğinde */}
      <group ref={carriage} position={[0, 0.15, 0]}>
        <mesh material={body} position={[-0.07, 0, -0.25]}>
          <boxGeometry args={[0.36, 0.11, 0.07]} />
        </mesh>
        {[-0.2, -0.11, -0.03, 0.06].map((x) => (
          <mesh key={x} material={lens} position={[x, 0, -0.29]} rotation-x={Math.PI / 2}>
            <cylinderGeometry args={[0.018, 0.018, 0.02, 16]} />
          </mesh>
        ))}
        {/* çekim anı: rafa doğru açılan görüş konisi */}
        <mesh material={flash} position={[-0.07, 0, -0.85]} rotation-x={Math.PI / 2}>
          <coneGeometry args={[0.55, 1.1, 4, 1, true]} />
        </mesh>
      </group>
    </group>
  );
}

/** Robotun geçtiği yol (zeminde ince turuncu iz). */
export function Trail({ visible }: { visible: boolean }) {
  const [version, setVersion] = useState(trailBuf.version);
  const last = useRef(0);
  useFrame(({ clock }) => {
    if (trailBuf.version !== version && clock.elapsedTime - last.current > 0.25) {
      last.current = clock.elapsedTime;
      setVersion(trailBuf.version);
    }
  });
  // trailBuf değişken bir tampon; `version` değişince yeniden okunur.
  const points = useMemo(() => trailBuf.points.map(([x, y]) => w(x, y, 0.015)), [version]);
  if (!visible || points.length < 2) return null;
  return <Line points={points} color={BEAM} lineWidth={2} transparent opacity={0.55} />;
}
