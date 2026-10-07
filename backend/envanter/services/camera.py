"""Jetson CSI kameraları: Arducam CamArray HAT (UC-512) üzerinde 4×IMX519.

Donanım (Jetson Orin Nano, JetPack 6.2.1 / L4T 36.4.7, Arducam imx519 sürücüsü):
- Görüntü Argus'tan (nvarguscamerasrc) gelir. HAT dört kamerayı 2×2 tek karede birleştirir:
  sol üst = kamera 1, sağ üst = 2, sol alt = 3, sağ alt = 4.
- HAT ve odak motoru kamera kablosundaki I2C hattındadır: HAT 0x24 (0x24 yazmacı = mod,
  0x00 dörtlü), AK7375 odak motoru 0x0c (0..4095; yazma HAT üzerinden dört kameraya birden gider).
- Kamera aynı anda tek süreçte açılabilir. Akış yalnız biri izlerken ya da çekim yaparken açık
  tutulur; `idle_s` saniye kullanılmazsa kapanır (Jetson'daki kamera_izle.sh da çalışabilsin).
- Sensörler akış kapanınca güçten kesilir ve odak motoru sıfırlanır; akış açılınca son odak
  yeniden yazılır.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import numpy as np

from ..config import get_settings

HAT_ADDR = 0x24
VCM_ADDR = 0x0C
FOCUS_MAX = 4095
VIEWS = 4  # 2×2 birleşik karedeki kamera sayısı


class CameraError(RuntimeError):
    """Kamera açılamadı / kullanılamıyor (API 503 döner)."""


class FrameSource(Protocol):
    def open(self) -> None: ...
    def read(self) -> np.ndarray | None: ...
    def close(self) -> None: ...


class GstSource:
    """Argus → nvvidconv → BGR. OpenCV'nin GStreamer arka ucu gerekir (Jetson'daki cv2'de var)."""

    def __init__(self, width: int, height: int, fps: int) -> None:
        self.pipeline = (
            f"nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM),width={width},"
            f"height={height},framerate={fps}/1 ! nvvidconv ! video/x-raw,format=BGRx ! "
            "videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1 sync=false"
        )
        self._cap = None

    def open(self) -> None:
        if cv2 is None:
            raise CameraError("OpenCV (GStreamer destekli) bulunamadı.")
        cap = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            raise CameraError(
                "Kamera açılamadı. Başka bir program (ör. kamera_izle.sh) kullanıyor olabilir."
            )
        self._cap = cap

    def read(self) -> np.ndarray | None:
        ok, frame = self._cap.read() if self._cap is not None else (False, None)
        return frame if ok else None

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class I2CBus:
    def __init__(self, bus: int) -> None:
        self.bus = bus

    def write(self, addr: int, *data: int) -> None:
        cmd = ["i2ctransfer", "-y", str(self.bus), f"w{len(data)}@0x{addr:02x}"]
        cmd += [f"0x{b:02x}" for b in data]
        subprocess.run(cmd, check=True, capture_output=True, timeout=2)


def split_views(frame: np.ndarray) -> list[np.ndarray]:
    """2×2 birleşik kareyi kamera 1..4 sırasıyla dört parçaya ayırır."""
    h, w = frame.shape[:2]
    return [
        frame[: h // 2, : w // 2],
        frame[: h // 2, w // 2 :],
        frame[h // 2 :, : w // 2],
        frame[h // 2 :, w // 2 :],
    ]


def view_of(frame: np.ndarray, view: int) -> np.ndarray:
    """view 0: birleşik kare, 1..4: tek kamera."""
    if view == 0:
        return frame
    if not 1 <= view <= VIEWS:
        raise ValueError(f"Geçersiz kamera: {view}")
    return split_views(frame)[view - 1]


try:  # Jetson'daki sistem OpenCV'si (GStreamer destekli); Mac'te yok, PIL/numpy'a düşülür.
    import cv2
except ImportError:  # pragma: no cover - ortama bağlı
    cv2 = None


def sharpness(img: np.ndarray) -> float:
    """Laplace varyansı (küçültülmüş gri görüntüde); büyük değer = keskin."""
    g = img.mean(axis=2) if img.ndim == 3 else img.astype(np.float32)
    step = max(1, int(np.ceil(g.shape[1] / 960)))
    g = np.asarray(g[::step, ::step], dtype=np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


def encode_jpeg(bgr: np.ndarray, max_w: int, quality: int) -> bytes:
    if cv2 is not None:
        if bgr.shape[1] > max_w:
            s = max_w / bgr.shape[1]
            bgr = cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            raise CameraError("JPEG kodlanamadı.")
        return buf.tobytes()
    import io

    from PIL import Image

    img = Image.fromarray(np.ascontiguousarray(bgr[:, :, ::-1]))
    if img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.Resampling.BILINEAR)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality)
    return out.getvalue()


def hardware_present() -> bool:
    return Path("/dev/video0").exists() and shutil.which("i2ctransfer") is not None


class CameraService:
    def __init__(
        self,
        source_factory: Callable[[], FrameSource],
        i2c: I2CBus | None,
        idle_s: float = 20.0,
    ) -> None:
        self._factory = source_factory
        self._i2c = i2c
        self.idle_s = idle_s
        self._cond = threading.Condition()
        self._thread: threading.Thread | None = None
        self._frame: np.ndarray | None = None
        self._seq = 0
        self._error: str | None = None
        self._stop = False
        self._last_use = 0.0
        self._fps = 0.0
        self.focus = 2048
        self._jpeg_cache: dict[tuple[int, int, int], tuple[int, bytes]] = {}
        self._af_lock = threading.Lock()

    # --- yaşam döngüsü ---------------------------------------------------

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def touch(self) -> None:
        self._last_use = time.monotonic()

    def start(self, timeout: float = 10.0) -> None:
        """Akışı açar (açıksa bir şey yapmaz) ve ilk kare gelene kadar bekler."""
        self.touch()
        with self._cond:
            if not self.running:
                self._error = None
                self._frame = None
                self._stop = False
                self._thread = threading.Thread(target=self._loop, name="kamera", daemon=True)
                self._thread.start()
            ok = self._cond.wait_for(
                lambda: self._frame is not None or self._error is not None, timeout
            )
        if self._error:
            raise CameraError(self._error)
        if not ok:
            raise CameraError("Kameradan görüntü gelmedi (zaman aşımı).")

    def stop(self) -> None:
        with self._cond:
            self._stop = True
            self._cond.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        src: FrameSource | None = None
        try:
            self._set_quad_mode()
            src = self._factory()
            src.open()
            first = True
            t0, n = time.monotonic(), 0
            while not self._stop and time.monotonic() - self._last_use < self.idle_s:
                frame = src.read()
                if frame is None:
                    raise CameraError("Kamera akışı kesildi.")
                if first:  # sensörler artık güçte: odağı yeniden yaz
                    self._write_focus(self.focus)
                    first = False
                with self._cond:
                    self._frame = frame
                    self._seq += 1
                    self._cond.notify_all()
                n += 1
                if n == 30:
                    now = time.monotonic()
                    self._fps = n / (now - t0)
                    t0, n = now, 0
        except Exception as e:
            with self._cond:
                self._error = str(e) if isinstance(e, CameraError) else f"Kamera hatası: {e}"
                self._cond.notify_all()
        finally:
            if src is not None:
                src.close()
            with self._cond:
                self._frame = None
                self._jpeg_cache.clear()
                self._cond.notify_all()

    # --- kareler ---------------------------------------------------------

    def wait_frame(self, after_seq: int = 0, timeout: float = 3.0) -> tuple[np.ndarray, int]:
        """`after_seq`'ten yeni bir kare gelene kadar bekler."""
        self.touch()
        with self._cond:
            ok = self._cond.wait_for(
                lambda: (
                    (self._frame is not None and self._seq > after_seq)
                    or self._error is not None
                    or not self.running
                ),
                timeout,
            )
            if self._error:
                raise CameraError(self._error)
            if not ok or self._frame is None:
                raise CameraError("Kameradan görüntü gelmedi.")
            return self._frame, self._seq

    def capture(self) -> np.ndarray:
        """Taze bir tam kare (çağrıdan sonra yakalanmış)."""
        self.start()
        _, seq = self.wait_frame()
        frame, _ = self.wait_frame(seq)
        return frame.copy()

    def jpeg(
        self, view: int, max_w: int, after_seq: int = 0, quality: int = 75
    ) -> tuple[bytes, int]:
        """Canlı yayın için küçültülmüş JPEG. Aynı kare birden çok izleyiciye bir kez kodlanır."""
        frame, seq = self.wait_frame(after_seq)
        key = (view, max_w, quality)
        hit = self._jpeg_cache.get(key)
        if hit and hit[0] == seq:
            return hit[1], seq
        data = encode_jpeg(view_of(frame, view), max_w, quality)
        self._jpeg_cache[key] = (seq, data)
        return data, seq

    # --- odak ------------------------------------------------------------

    def _set_quad_mode(self) -> None:
        if self._i2c is not None:
            self._i2c.write(HAT_ADDR, 0x24, 0x00)

    def _write_focus(self, pos: int) -> None:
        if self._i2c is None:
            return
        v = (pos << 4) & 0xFFF0
        self._i2c.write(VCM_ADDR, 0x02, 0x00)  # motoru beklemeden çıkar
        self._i2c.write(VCM_ADDR, 0x00, v >> 8, v & 0xFF)

    def set_focus(self, pos: int) -> int:
        self.focus = max(0, min(FOCUS_MAX, int(pos)))
        if self.running:
            self._write_focus(self.focus)
        return self.focus

    def autofocus(self, view: int = 0) -> dict:
        """Kontrast ile odak: kaba (256) sonra ince (32) tarama; en keskin konumda bırakır."""
        with self._af_lock:
            self.start()
            t0 = time.monotonic()
            scores: list[list[float]] = []

            def measure(pos: int) -> float:
                self.set_focus(pos)
                _, seq = self.wait_frame()
                # Ardışık düzen birkaç kare geriden gelir; motorun oturduğu kareyi bekle.
                frame, _ = self.wait_frame(seq + 2)
                s = sharpness(view_of(frame, view))
                scores.append([pos, round(s, 1)])
                return s

            coarse = {p: measure(p) for p in range(0, FOCUS_MAX + 1, 256)}
            best = max(coarse, key=coarse.__getitem__)
            fine = {
                p: measure(p) for p in range(max(0, best - 224), min(FOCUS_MAX, best + 224) + 1, 32)
            }
            fine[best] = coarse[best]
            best = max(fine, key=fine.__getitem__)
            self.set_focus(best)
            return {
                "position": best,
                "view": view,
                "sharpness": round(fine[best], 1),
                "elapsed_ms": round((time.monotonic() - t0) * 1000),
                "scores": scores,
            }

    def status(self) -> dict:
        frame = self._frame
        return {
            "available": True,
            "running": self.running,
            "error": self._error,
            "focus": self.focus,
            "focus_max": FOCUS_MAX,
            "fps": round(self._fps, 1) if self.running else 0.0,
            "width": int(frame.shape[1]) if frame is not None else None,
            "height": int(frame.shape[0]) if frame is not None else None,
            "views": VIEWS,
        }


_camera: CameraService | None = None
_camera_lock = threading.Lock()


def get_camera() -> CameraService | None:
    """Donanım yoksa (ör. Mac'te geliştirme) None döner; testler `set_camera` ile sahte verir."""
    global _camera
    with _camera_lock:
        if _camera is None:
            s = get_settings()
            enabled = s.camera_enabled if s.camera_enabled is not None else hardware_present()
            if not enabled:
                return None
            _camera = CameraService(
                lambda: GstSource(s.camera_width, s.camera_height, s.camera_fps),
                I2CBus(s.camera_i2c_bus),
                idle_s=s.camera_idle_s,
            )
        return _camera


def set_camera(cam: CameraService | None) -> None:
    global _camera
    with _camera_lock:
        if _camera is not None and _camera is not cam:
            _camera.stop()
        _camera = cam
