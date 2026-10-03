"""LiDAR haritası ve robot durumu.

Robot (veya ileride SLAM düğümü) her telemetri mesajında konumunu ve robot
eksenindeki LiDAR noktalarını gönderir. Noktalar dünya eksenine çevrilip sabit
çözünürlüklü bir voksel kümesine eklenir; yalnız yeni dolan vokseller arayüze yayınlanır.

Eksenler: robot ekseni x ileri, y sol, z yukarı. Dünya ekseni models.Warehouse ile aynı.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..config import get_settings

RESOLUTION_M = 0.08
_OFFSET = 1 << 19  # negatif indeksleri desteklemek için
_MASK = (1 << 20) - 1
_MIN_Z = 0.05  # zemin noktalarını at (zemin ayrıştırma)
_PERSIST_EVERY_S = 3.0


def _pack(idx: np.ndarray) -> np.ndarray:
    i = idx.astype(np.int64) + _OFFSET
    return i[:, 0] | (i[:, 1] << 20) | (i[:, 2] << 40)


def unpack(keys: np.ndarray) -> np.ndarray:
    k = keys.astype(np.int64)
    out = np.stack([k & _MASK, (k >> 20) & _MASK, (k >> 40) & _MASK], axis=1)
    return out - _OFFSET


def robot_to_world(points: np.ndarray, x: float, y: float, yaw: float) -> np.ndarray:
    c, s = np.cos(yaw), np.sin(yaw)
    out = np.empty_like(points, dtype=np.float64)
    out[:, 0] = c * points[:, 0] - s * points[:, 1] + x
    out[:, 1] = s * points[:, 0] + c * points[:, 1] + y
    out[:, 2] = points[:, 2]
    return out


@dataclass
class RobotState:
    x: float = 0.0
    y: float = 0.0
    yaw: float = 0.0
    mast_mm: float = 0.0
    state: str = "idle"
    updated_at: float = 0.0
    trail: deque = field(default_factory=lambda: deque(maxlen=3000))

    def as_dict(self) -> dict:
        return {
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "yaw": round(self.yaw, 4),
            "mast_mm": round(self.mast_mm, 1),
            "state": self.state,
            "online": (time.time() - self.updated_at) < 5.0,
        }


class MapStore:
    def __init__(self, directory: Path) -> None:
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)
        self._cells: dict[int, set[int]] = {}
        self._dirty_since: dict[int, float] = {}
        self._robots: dict[int, RobotState] = {}
        self._lock = threading.Lock()

    # --- voksel haritası -------------------------------------------------
    def _path(self, warehouse_id: int) -> Path:
        return self._dir / f"map-{warehouse_id}.npy"

    def _cells_for(self, warehouse_id: int) -> set[int]:
        cells = self._cells.get(warehouse_id)
        if cells is None:
            p = self._path(warehouse_id)
            cells = set(np.load(p).tolist()) if p.exists() else set()
            self._cells[warehouse_id] = cells
        return cells

    def add_world_points(self, warehouse_id: int, world: np.ndarray) -> np.ndarray:
        """Noktaları haritaya ekler; yeni dolan voksellerin (N,3) indekslerini döndürür."""
        if world.size == 0:
            return np.empty((0, 3), dtype=np.int64)
        world = world[world[:, 2] >= _MIN_Z]
        keys = np.unique(_pack(np.floor(world / RESOLUTION_M)))
        with self._lock:
            cells = self._cells_for(warehouse_id)
            new = [k for k in keys.tolist() if k not in cells]
            cells.update(new)
            if new:
                self._dirty_since.setdefault(warehouse_id, time.time())
            self._maybe_persist(warehouse_id)
        return unpack(np.asarray(new, dtype=np.int64)) if new else np.empty((0, 3), np.int64)

    def cells(self, warehouse_id: int) -> np.ndarray:
        with self._lock:
            keys = np.fromiter(self._cells_for(warehouse_id), dtype=np.int64)
        return unpack(keys) if keys.size else np.empty((0, 3), np.int64)

    def reset(self, warehouse_id: int) -> None:
        with self._lock:
            self._cells[warehouse_id] = set()
            self._path(warehouse_id).unlink(missing_ok=True)
            self._dirty_since.pop(warehouse_id, None)
            self._robots.pop(warehouse_id, None)

    def _maybe_persist(self, warehouse_id: int, force: bool = False) -> None:
        since = self._dirty_since.get(warehouse_id)
        if since is None or (not force and time.time() - since < _PERSIST_EVERY_S):
            return
        arr = np.fromiter(self._cells_for(warehouse_id), dtype=np.int64)
        tmp = self._path(warehouse_id).with_suffix(".tmp.npy")
        np.save(tmp, arr)
        tmp.replace(self._path(warehouse_id))
        self._dirty_since.pop(warehouse_id, None)

    def flush(self) -> None:
        with self._lock:
            for wid in list(self._dirty_since):
                self._maybe_persist(wid, force=True)

    # --- robot durumu ----------------------------------------------------
    def robot(self, warehouse_id: int) -> RobotState:
        return self._robots.setdefault(warehouse_id, RobotState())

    def update_robot(
        self,
        warehouse_id: int,
        x: float,
        y: float,
        yaw: float,
        mast_mm: float | None = None,
        state: str | None = None,
    ) -> RobotState:
        r = self.robot(warehouse_id)
        if not r.trail or np.hypot(x - r.trail[-1][0], y - r.trail[-1][1]) > 0.1:
            r.trail.append((round(x, 2), round(y, 2)))
        r.x, r.y, r.yaw = x, y, yaw
        if mast_mm is not None:
            r.mast_mm = mast_mm
        if state is not None:
            r.state = state
        r.updated_at = time.time()
        return r


_store: MapStore | None = None


def get_map_store() -> MapStore:
    global _store
    if _store is None:
        _store = MapStore(get_settings().data_dir / "maps")
    return _store
