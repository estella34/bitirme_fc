"""Veri modeli.

Depo düzeni:   Warehouse → Rack → Location (raf gözü)
Beklenen stok: ExpectedItem (WMS'ten içe aktarılan "bu gözde ne olmalı")
Tarama:        Scan → Capture (tek görüntü) → CodeRead (görüntüde okunan kod)
Sonuç:         Observation (bir taramada bir gözün mutabakat sonucu)
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ObservationStatus(str, Enum):
    VERIFIED = "verified"  # okunan kodlar beklenenle birebir aynı
    OBSERVED = "observed"  # kod okundu ama bu göz için beklenen stok tanımlı değil
    UNREADABLE = "unreadable"  # koli var / kimlik (tamamen ya da kısmen) okunamadı
    EMPTY = "empty"  # göz boş ve boş olması bekleniyordu
    CONFLICT = "conflict"  # beklenmeyen kod ya da eksik koli → manuel kontrol


class ReviewStatus(str, Enum):
    NONE = "none"  # inceleme gerekmiyor
    PENDING = "pending"  # inceleme kuyruğunda
    APPROVED = "approved"  # sistem sonucu onaylandı
    CORRECTED = "corrected"  # operatör düzeltti


class ScanStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanMode(str, Enum):
    ROBOT = "robot"
    MANUAL = "manual"
    DEMO = "demo"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    # Zemin planı ölçüsü (m). Dünya koordinatları: x doğu, y kuzey, z yukarı; köken bir köşe.
    width_m: Mapped[float] = mapped_column(Float, default=20.0)
    length_m: Mapped[float] = mapped_column(Float, default=12.0)

    racks: Mapped[list[Rack]] = relationship(
        back_populates="warehouse", order_by="Rack.code", cascade="all, delete-orphan"
    )


class Rack(Base):
    """Raf. Yerel eksen: pozisyonlar +x boyunca dizilir, derinlik +y, ön yüz yerel y=0'dadır.

    (x, y) ön-sol alt köşenin dünya konumu, yaw_deg z ekseni etrafında dönüş. yaw=0 iken
    rafın ön yüzü -y yönüne (koridora) bakar.
    """

    __tablename__ = "racks"
    __table_args__ = (UniqueConstraint("warehouse_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(32))
    aisle: Mapped[str | None] = mapped_column(String(32))
    levels: Mapped[int] = mapped_column(Integer)
    positions: Mapped[int] = mapped_column(Integer)
    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)
    yaw_deg: Mapped[float] = mapped_column(Float, default=0.0)
    bay_width_m: Mapped[float] = mapped_column(Float, default=1.2)
    depth_m: Mapped[float] = mapped_column(Float, default=0.8)
    level_height_m: Mapped[float] = mapped_column(Float, default=0.5)

    warehouse: Mapped[Warehouse] = relationship(back_populates="racks")
    locations: Mapped[list[Location]] = relationship(
        back_populates="rack",
        order_by="(Location.level.desc(), Location.position)",
        cascade="all, delete-orphan",
    )


class Location(Base):
    """Raf gözü. Kod biçimi: <raf>-<seviye>-<pozisyon>, ör. A01-2-3 (seviye 1 en alttadır)."""

    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("rack_id", "level", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rack_id: Mapped[int] = mapped_column(ForeignKey("racks.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    level: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)
    # Kamera merkezinin bu göz için dikey eksendeki hedef konumu (mekanizma kalibrasyonu).
    camera_height_mm: Mapped[float | None] = mapped_column(Float)

    # En son mutabakat sonucu: raf görünümünü tek sorguyla çizmek için tutulur.
    last_observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("observations.id", ondelete="SET NULL", use_alter=True)
    )

    rack: Mapped[Rack] = relationship(back_populates="locations")
    expected_items: Mapped[list[ExpectedItem]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    last_observation: Mapped[Observation | None] = relationship(
        foreign_keys=[last_observation_id], post_update=True
    )


class ExpectedItem(Base):
    __tablename__ = "expected_items"
    __table_args__ = (UniqueConstraint("location_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[str | None] = mapped_column(String(256))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(32), default="import")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    location: Mapped[Location] = relationship(back_populates="expected_items")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    status: Mapped[ScanStatus] = mapped_column(String(16), default=ScanStatus.RUNNING)
    mode: Mapped[ScanMode] = mapped_column(String(16), default=ScanMode.MANUAL)
    note: Mapped[str | None] = mapped_column(String(512))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    captures: Mapped[list[Capture]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", order_by="Capture.id"
    )
    observations: Mapped[list[Observation]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


class Capture(Base):
    """Tek bir kamera görüntüsü ve meta verisi."""

    __tablename__ = "captures"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), index=True
    )
    camera_id: Mapped[str] = mapped_column(String(32), default="cam0")
    vertical_position_mm: Mapped[float | None] = mapped_column(Float)
    image_path: Mapped[str] = mapped_column(String(512))  # data_dir'e göreli
    thumb_path: Mapped[str] = mapped_column(String(512))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sharpness: Mapped[float | None] = mapped_column(Float)
    decode_ms: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    scan: Mapped[Scan] = relationship(back_populates="captures")
    reads: Mapped[list[CodeRead]] = relationship(
        back_populates="capture", cascade="all, delete-orphan"
    )


class CodeRead(Base):
    __tablename__ = "code_reads"

    id: Mapped[int] = mapped_column(primary_key=True)
    capture_id: Mapped[int] = mapped_column(
        ForeignKey("captures.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(String(1024))
    symbology: Mapped[str] = mapped_column(String(32))
    # B0: tam görüntü, B1: klasik ön işleme, A1: AI tespit + kırpma, OCR: metin yedeği
    method: Mapped[str] = mapped_column(String(8))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    polygon: Mapped[list[list[float]]] = mapped_column(JSON)  # 4 köşe, orijinal piksel

    capture: Mapped[Capture] = relationship(back_populates="reads")


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("scan_id", "location_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))
    status: Mapped[ObservationStatus] = mapped_column(String(16), index=True)
    reason: Mapped[str] = mapped_column(String(256), default="")
    box_count: Mapped[int | None] = mapped_column(Integer)
    codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    expected: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing: Mapped[list[str]] = mapped_column(JSON, default=list)
    unexpected: Mapped[list[str]] = mapped_column(JSON, default=list)
    review_status: Mapped[ReviewStatus] = mapped_column(String(16), default=ReviewStatus.NONE)
    review_note: Mapped[str | None] = mapped_column(String(512))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    scan: Mapped[Scan] = relationship(back_populates="observations")
    location: Mapped[Location] = relationship(foreign_keys=[location_id])
