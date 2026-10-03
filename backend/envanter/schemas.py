from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    warehouse_id: int
    mode: Literal["robot", "manual"] = "manual"
    note: str | None = None


class ReviewAction(BaseModel):
    action: Literal["approve", "correct"]
    note: str | None = Field(default=None, max_length=512)


class Pose(BaseModel):
    x: float
    y: float
    yaw: float = Field(description="radyan, x ekseninden saat yönünün tersine")


class Scan2D(BaseModel):
    """sensor_msgs/LaserScan benzeri 2B tarama (robot ekseni)."""

    angle_min: float
    angle_increment: float
    ranges: list[float]
    range_max: float = 30.0
    sensor_z: float = 0.3


class Telemetry(BaseModel):
    """Robot → sunucu telemetri mesajı. `points` veya `scan2d` gönderilebilir (ikisi de isteğe bağlı)."""

    warehouse_id: int
    pose: Pose
    mast_mm: float | None = None
    state: str | None = None
    points: list[list[float]] | None = Field(
        default=None, description="Robot ekseninde [x, y, z] noktaları (m)"
    )
    scan2d: Scan2D | None = None


class DemoStart(BaseModel):
    speed: float = Field(default=4.0, ge=0.25, le=20)
    seed: int = 7


class RackCreate(BaseModel):
    warehouse_id: int
    code: str = Field(min_length=1, max_length=32)
    x: float
    y: float
    yaw_deg: float = 0.0
    levels: int = Field(default=3, ge=1, le=20)
    positions: int = Field(default=4, ge=1, le=50)
    bay_width_m: float = Field(default=1.2, gt=0)
    depth_m: float = Field(default=0.8, gt=0)
    level_height_m: float = Field(default=0.5, gt=0)
    aisle: str | None = None


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    width_m: float = Field(default=20.0, gt=0)
    length_m: float = Field(default=12.0, gt=0)
