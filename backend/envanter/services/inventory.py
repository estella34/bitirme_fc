"""Tarama hattı: görüntüyü kaydet → kodları çöz → gözün mutabakatını güncelle → yayınla."""

from __future__ import annotations

import io
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..db import SessionLocal
from ..models import (
    Capture,
    CodeRead,
    ExpectedItem,
    Location,
    Observation,
    ObservationStatus,
    Rack,
    Scan,
    ScanMode,
    ScanStatus,
)
from .decoder import decode_image
from .live import broker
from .reconcile import reconcile

STATUS_TR = {
    ObservationStatus.VERIFIED: "doğrulandı",
    ObservationStatus.OBSERVED: "okundu",
    ObservationStatus.UNREADABLE: "okunamadı",
    ObservationStatus.EMPTY: "boş",
    ObservationStatus.CONFLICT: "çelişki",
}


def new_scan_id() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("S%y%m%d-%H%M%S-") + secrets.token_hex(
        2
    )


def iso(dt: datetime | None) -> str | None:
    """SQLite saat dilimini saklamaz; okunan saf zamanlar UTC kabul edilir."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def media_url(rel: str | None) -> str | None:
    return f"/media/{rel}" if rel else None


# --- serileştirme ----------------------------------------------------------


def location_state(loc: Location, obs: Observation | None, expected: list[str]) -> dict:
    return {
        "id": loc.id,
        "code": loc.code,
        "rack_id": loc.rack_id,
        "level": loc.level,
        "position": loc.position,
        "expected": expected,
        "status": obs.status if obs else None,
        "reason": obs.reason if obs else None,
        "codes": obs.codes if obs else [],
        "missing": obs.missing if obs else [],
        "unexpected": obs.unexpected if obs else [],
        "box_count": obs.box_count if obs else None,
        "review_status": obs.review_status if obs else None,
        "observation_id": obs.id if obs else None,
        "scan_id": obs.scan_id if obs else None,
        "updated_at": iso(obs.updated_at) if obs else None,
    }


def capture_dict(c: Capture, location_code: str | None = None) -> dict:
    return {
        "id": c.id,
        "scan_id": c.scan_id,
        "location_id": c.location_id,
        "location_code": location_code,
        "camera_id": c.camera_id,
        "vertical_position_mm": c.vertical_position_mm,
        "image_url": media_url(c.image_path),
        "thumb_url": media_url(c.thumb_path),
        "width": c.width,
        "height": c.height,
        "sharpness": round(c.sharpness or 0, 1),
        "decode_ms": round(c.decode_ms or 0, 1),
        "captured_at": iso(c.captured_at),
        "reads": [
            {
                "text": r.text,
                "symbology": r.symbology,
                "method": r.method,
                "confidence": r.confidence,
                "polygon": r.polygon,
            }
            for r in c.reads
        ],
    }


def scan_dict(s: Scan, counts: dict[str, int] | None = None) -> dict:
    return {
        "id": s.id,
        "warehouse_id": s.warehouse_id,
        "status": s.status,
        "mode": s.mode,
        "note": s.note,
        "started_at": iso(s.started_at),
        "finished_at": iso(s.finished_at),
        "counts": counts or {},
    }


# --- yardımcılar -----------------------------------------------------------


def warehouse_has_stock(session: Session, warehouse_id: int) -> bool:
    """Depo için stok listesi içe aktarıldıysa, listede olmayan göz 'boş olmalı' sayılır."""
    q = (
        select(ExpectedItem.id)
        .join(Location, ExpectedItem.location_id == Location.id)
        .join(Rack, Location.rack_id == Rack.id)
        .where(Rack.warehouse_id == warehouse_id)
        .limit(1)
    )
    return session.execute(select(exists(q))).scalar_one()


def expected_codes(loc: Location) -> list[str]:
    return sorted(e.code for e in loc.expected_items)


def start_scan(
    session: Session, warehouse_id: int, mode: ScanMode, note: str | None = None
) -> Scan:
    scan = Scan(id=new_scan_id(), warehouse_id=warehouse_id, mode=mode, note=note)
    session.add(scan)
    session.commit()
    broker.publish(warehouse_id, {"type": "scan", "scan": scan_dict(scan)})
    broker.event(warehouse_id, f"Tarama başladı: {scan.id}")
    return scan


def finish_scan(session: Session, scan: Scan, status: ScanStatus = ScanStatus.COMPLETED) -> Scan:
    scan.status = status
    scan.finished_at = datetime.now(timezone.utc)
    session.commit()
    counts = scan_counts(session, scan.id)
    broker.publish(scan.warehouse_id, {"type": "scan", "scan": scan_dict(scan, counts)})
    issues = counts.get("conflict", 0) + counts.get("unreadable", 0)
    level = "warn" if issues else "ok"
    broker.event(scan.warehouse_id, f"Tarama bitti: {scan.id} · {issues} sorunlu göz", level)
    return scan


def scan_counts(session: Session, scan_id: str) -> dict[str, int]:
    rows = session.execute(select(Observation.status).where(Observation.scan_id == scan_id))
    counts: dict[str, int] = {}
    for (st,) in rows:
        counts[st] = counts.get(st, 0) + 1
    return counts


# --- görüntü kaydı ---------------------------------------------------------


def _store_image(scan_id: str, data: bytes) -> tuple[str, str, Image.Image]:
    s = get_settings()
    img = Image.open(io.BytesIO(data))
    img.load()
    img = ImageOps.exif_transpose(img)
    folder = Path("captures") / scan_id
    (s.data_dir / folder).mkdir(parents=True, exist_ok=True)
    stem = uuid.uuid4().hex[:12]

    fmt = (img.format or "").upper()
    ext = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}.get(fmt)
    if ext:  # özgün baytları aynen sakla (kanıt görüntüsü yeniden sıkıştırılmasın)
        rel = folder / f"{stem}.{ext}"
        (s.data_dir / rel).write_bytes(data)
    else:
        rel = folder / f"{stem}.png"
        img.save(s.data_dir / rel)

    thumb = img.convert("RGB")
    thumb.thumbnail((s.thumbnail_px, s.thumbnail_px))
    thumb_rel = folder / f"{stem}.thumb.jpg"
    thumb.save(s.data_dir / thumb_rel, quality=82)
    return rel.as_posix(), thumb_rel.as_posix(), img


# --- ana giriş noktası -----------------------------------------------------


def ingest_capture(
    scan_id: str,
    image_bytes: bytes,
    *,
    location_code: str | None = None,
    camera_id: str = "cam0",
    vertical_position_mm: float | None = None,
    box_count: int | None = None,
) -> dict:
    """Bir kamera görüntüsünü işler. İş parçacığında çağrılabilir (kendi oturumunu açar)."""
    settings = get_settings()
    with SessionLocal() as session:
        scan = session.get(Scan, scan_id)
        if scan is None:
            raise LookupError(f"Tarama bulunamadı: {scan_id}")

        loc = None
        if location_code:
            loc = session.scalar(
                select(Location)
                .where(Location.code == location_code)
                .options(selectinload(Location.expected_items))
            )
            if loc is None:
                raise LookupError(f"Raf gözü bulunamadı: {location_code}")

        rel, thumb_rel, img = _store_image(scan_id, image_bytes)
        outcome = decode_image(img, fallback=settings.decode_fallback)

        cap = Capture(
            scan_id=scan_id,
            location_id=loc.id if loc else None,
            camera_id=camera_id,
            vertical_position_mm=vertical_position_mm,
            image_path=rel,
            thumb_path=thumb_rel,
            width=outcome.width,
            height=outcome.height,
            sharpness=outcome.sharpness,
            decode_ms=outcome.elapsed_ms,
        )
        cap.reads = [
            CodeRead(
                text=c.text,
                symbology=c.symbology,
                method=c.method,
                confidence=c.confidence,
                polygon=c.polygon,
            )
            for c in outcome.codes
        ]
        session.add(cap)
        session.flush()

        state = None
        if loc is not None:
            state = _update_observation(session, scan, loc, box_count)
        session.commit()

        result = {"capture": capture_dict(cap, loc.code if loc else None), "location": state}

    wid = scan.warehouse_id
    broker.publish(wid, {"type": "capture", "capture": result["capture"]})
    if state is not None:
        broker.publish(wid, {"type": "location", "location": state})
        st = state["status"]
        level = {"conflict": "error", "unreadable": "warn"}.get(st, "ok")
        broker.event(
            wid,
            f"{state['code']} · {STATUS_TR[ObservationStatus(st)]} — {state['reason']}",
            level,
            location_id=state["id"],
        )
    return result


def _update_observation(session: Session, scan: Scan, loc: Location, box_count: int | None) -> dict:
    # Aynı taramada aynı göze ait bütün görüntülerin (kameralar, tekrarlar) kodları birleştirilir.
    caps = session.scalars(
        select(Capture)
        .where(Capture.scan_id == scan.id, Capture.location_id == loc.id)
        .options(selectinload(Capture.reads))
    ).all()
    codes = {r.text for c in caps for r in c.reads}

    obs = session.scalar(
        select(Observation).where(Observation.scan_id == scan.id, Observation.location_id == loc.id)
    )
    if box_count is None and obs is not None:
        box_count = obs.box_count
    elif box_count is not None and obs is not None and obs.box_count is not None:
        box_count = max(box_count, obs.box_count)

    exp_list = expected_codes(loc)
    has_stock = bool(exp_list) or warehouse_has_stock(session, scan.warehouse_id)
    verdict = reconcile(codes, set(exp_list) if has_stock else None, box_count)

    if obs is None:
        obs = Observation(scan_id=scan.id, location_id=loc.id)
        session.add(obs)
    obs.status = verdict.status
    obs.reason = verdict.reason
    obs.box_count = box_count
    obs.codes = sorted(codes)
    obs.expected = exp_list
    obs.missing = verdict.missing
    obs.unexpected = verdict.unexpected
    obs.review_status = verdict.review
    obs.review_note = None
    obs.reviewed_at = None
    obs.updated_at = datetime.now(timezone.utc)
    session.flush()
    loc.last_observation_id = obs.id
    return location_state(loc, obs, exp_list)
