import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import {
  BufferAttribute,
  BufferGeometry,
  CanvasTexture,
  DynamicDrawUsage,
  SRGBColorSpace,
} from "three";
import { mapBuf, scanBuf } from "../buffers";

/** Yumuşak kenarlı yuvarlak nokta dokusu (kare noktalar yerine). */
function useDotTexture() {
  return useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const g = c.getContext("2d")!;
    const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, "rgba(255,255,255,1)");
    grad.addColorStop(0.55, "rgba(255,255,255,0.9)");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, 64, 64);
    const t = new CanvasTexture(c);
    t.colorSpace = SRGBColorSpace;
    return t;
  }, []);
}

/** Birikmiş LiDAR haritası. Yalnız yeni eklenen noktalar GPU'ya yüklenir. */
export function MapCloud({ visible }: { visible: boolean }) {
  const dot = useDotTexture();
  const geom = useMemo(() => {
    const g = new BufferGeometry();
    const pos = new BufferAttribute(mapBuf.positions, 3).setUsage(DynamicDrawUsage);
    const col = new BufferAttribute(mapBuf.colors, 3).setUsage(DynamicDrawUsage);
    g.setAttribute("position", pos);
    g.setAttribute("color", col);
    g.setDrawRange(0, 0);
    return g;
  }, []);
  const synced = useRef({ epoch: -1, count: 0 });

  useFrame(() => {
    const s = synced.current;
    if (s.epoch !== mapBuf.epoch) {
      s.epoch = mapBuf.epoch;
      s.count = 0;
      geom.setDrawRange(0, 0);
    }
    if (mapBuf.count > s.count) {
      for (const name of ["position", "color"] as const) {
        const attr = geom.getAttribute(name) as BufferAttribute;
        attr.clearUpdateRanges();
        attr.addUpdateRange(s.count * 3, (mapBuf.count - s.count) * 3);
        attr.needsUpdate = true;
      }
      s.count = mapBuf.count;
      geom.setDrawRange(0, s.count);
    }
  });

  return (
    <points geometry={geom} frustumCulled={false} visible={visible}>
      <pointsMaterial
        size={0.065}
        sizeAttenuation
        vertexColors
        map={dot}
        transparent
        alphaTest={0.25}
        opacity={0.8}
      />
    </points>
  );
}

/** Son LiDAR taraması: robotun "şu an gördüğü" parlak noktalar. */
export function ScanBeam({ visible }: { visible: boolean }) {
  const dot = useDotTexture();
  const geom = useMemo(() => {
    const g = new BufferGeometry();
    g.setAttribute("position", new BufferAttribute(scanBuf.positions, 3).setUsage(DynamicDrawUsage));
    g.setDrawRange(0, 0);
    return g;
  }, []);
  const seen = useRef(-1);

  useFrame(() => {
    if (seen.current === scanBuf.version) return;
    seen.current = scanBuf.version;
    const attr = geom.getAttribute("position") as BufferAttribute;
    attr.clearUpdateRanges();
    attr.addUpdateRange(0, scanBuf.count * 3);
    attr.needsUpdate = true;
    geom.setDrawRange(0, scanBuf.count);
  });

  return (
    <points geometry={geom} frustumCulled={false} visible={visible}>
      <pointsMaterial
        size={0.11}
        sizeAttenuation
        color="#ffd7a8"
        map={dot}
        transparent
        alphaTest={0.2}
        opacity={0.95}
        depthWrite={false}
      />
    </points>
  );
}
