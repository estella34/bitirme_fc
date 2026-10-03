"""Robot telemetrisi: konum + LiDAR noktaları → harita güncellemesi → canlı yayın."""

from __future__ import annotations

import numpy as np

from .live import broker
from .mapping import RESOLUTION_M, get_map_store, robot_to_world

# Canlı "tarama ışını" görüntüsü için arayüze gönderilecek en fazla nokta.
_PREVIEW_POINTS = 700


def ingest_telemetry(
    warehouse_id: int,
    *,
    x: float,
    y: float,
    yaw: float,
    mast_mm: float | None = None,
    state: str | None = None,
    points: np.ndarray | None = None,
) -> dict:
    """points: robot eksenindeki (N,3) LiDAR noktaları (m). None → yalnız konum güncellemesi."""
    store = get_map_store()
    robot = store.update_robot(warehouse_id, x, y, yaw, mast_mm, state)
    msg: dict = {
        "type": "robot",
        "robot": robot.as_dict(),
        "trail_point": [round(x, 2), round(y, 2)],
    }

    new_cells = 0
    if points is not None and len(points):
        world = robot_to_world(np.asarray(points, dtype=np.float64), x, y, yaw)
        cells = store.add_world_points(warehouse_id, world)
        new_cells = len(cells)
        if new_cells:
            broker.publish(
                warehouse_id,
                {"type": "map", "resolution": RESOLUTION_M, "cells": cells.ravel().tolist()},
            )
        step = max(1, len(world) // _PREVIEW_POINTS)
        preview = world[::step]
        preview = preview[preview[:, 2] >= 0.05]
        msg["scan"] = np.round(preview, 2).ravel().tolist()

    broker.publish(warehouse_id, msg)
    return {"new_cells": new_cells}
