"""Robot telemetrisi (konum + LiDAR)."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from ..schemas import Scan2D, Telemetry
from ..services.mapping import get_map_store
from ..services.telemetry import ingest_telemetry

router = APIRouter(tags=["robot"])


def _scan2d_points(s: Scan2D) -> np.ndarray:
    r = np.asarray(s.ranges, dtype=np.float64)
    a = s.angle_min + np.arange(len(r)) * s.angle_increment
    ok = np.isfinite(r) & (r > 0.05) & (r < s.range_max)
    return np.column_stack(
        [r[ok] * np.cos(a[ok]), r[ok] * np.sin(a[ok]), np.full(ok.sum(), s.sensor_z)]
    )


@router.post("/robot/telemetry")
async def telemetry(body: Telemetry) -> dict:
    parts = []
    if body.points:
        parts.append(np.asarray(body.points, dtype=np.float64).reshape(-1, 3))
    if body.scan2d:
        parts.append(_scan2d_points(body.scan2d))
    points = np.vstack(parts) if parts else None
    return await run_in_threadpool(
        lambda: ingest_telemetry(
            body.warehouse_id,
            x=body.pose.x,
            y=body.pose.y,
            yaw=body.pose.yaw,
            mast_mm=body.mast_mm,
            state=body.state,
            points=points,
        )
    )


@router.get("/robot")
def robot_state(warehouse_id: int) -> dict:
    r = get_map_store().robot(warehouse_id)
    return {**r.as_dict(), "trail": [list(p) for p in r.trail]}
