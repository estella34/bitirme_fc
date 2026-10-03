"""Depo düzeni: raf oluşturma ve raf/göz geometrisi."""

from __future__ import annotations

import math

from sqlalchemy.orm import Session

from ..models import Location, Rack, Warehouse


def location_code(rack_code: str, level: int, position: int) -> str:
    return f"{rack_code}-{level}-{position}"


def create_rack(
    session: Session,
    warehouse: Warehouse,
    code: str,
    *,
    x: float,
    y: float,
    yaw_deg: float = 0.0,
    levels: int = 3,
    positions: int = 4,
    bay_width_m: float = 1.2,
    depth_m: float = 0.8,
    level_height_m: float = 0.5,
    aisle: str | None = None,
) -> Rack:
    rack = Rack(
        warehouse=warehouse,
        code=code,
        aisle=aisle,
        levels=levels,
        positions=positions,
        x=x,
        y=y,
        yaw_deg=yaw_deg,
        bay_width_m=bay_width_m,
        depth_m=depth_m,
        level_height_m=level_height_m,
    )
    for level in range(1, levels + 1):
        for pos in range(1, positions + 1):
            rack.locations.append(
                Location(
                    code=location_code(code, level, pos),
                    level=level,
                    position=pos,
                    camera_height_mm=round(((level - 1) + 0.5) * level_height_m * 1000),
                )
            )
    session.add(rack)
    return rack


def rack_local_to_world(rack: Rack, lx: float, ly: float) -> tuple[float, float]:
    yaw = math.radians(rack.yaw_deg)
    c, s = math.cos(yaw), math.sin(yaw)
    return rack.x + c * lx - s * ly, rack.y + s * lx + c * ly


def bay_front_center(rack: Rack, position: int) -> tuple[float, float]:
    """Gözün ön yüzünün ortası (dünya, m)."""
    return rack_local_to_world(rack, (position - 0.5) * rack.bay_width_m, 0.0)


def rack_footprint(rack: Rack) -> list[tuple[float, float]]:
    length = rack.positions * rack.bay_width_m
    corners = [(0, 0), (length, 0), (length, rack.depth_m), (0, rack.depth_m)]
    return [rack_local_to_world(rack, cx, cy) for cx, cy in corners]


def rack_dict(rack: Rack) -> dict:
    return {
        "id": rack.id,
        "code": rack.code,
        "aisle": rack.aisle,
        "levels": rack.levels,
        "positions": rack.positions,
        "x": rack.x,
        "y": rack.y,
        "yaw_deg": rack.yaw_deg,
        "bay_width_m": rack.bay_width_m,
        "depth_m": rack.depth_m,
        "level_height_m": rack.level_height_m,
    }
