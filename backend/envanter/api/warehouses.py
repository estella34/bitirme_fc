"""Depo, dijital ikiz, raf gözü ayrıntısı ve inceleme kuyruğu."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_session
from ..models import (
    Capture,
    Location,
    Observation,
    Rack,
    ReviewStatus,
    Scan,
    Warehouse,
)
from ..schemas import RackCreate, ReviewAction, WarehouseCreate
from ..services.inventory import capture_dict, expected_codes, iso, location_state, scan_dict
from ..services.layout import create_rack, rack_dict
from ..services.live import broker
from ..services.mapping import RESOLUTION_M, get_map_store

router = APIRouter(tags=["depo"])


def _warehouse(session: Session, warehouse_id: int) -> Warehouse:
    wh = session.get(Warehouse, warehouse_id)
    if wh is None:
        raise HTTPException(404, "Depo bulunamadı")
    return wh


def _warehouse_dict(wh: Warehouse) -> dict:
    return {
        "id": wh.id,
        "code": wh.code,
        "name": wh.name,
        "width_m": wh.width_m,
        "length_m": wh.length_m,
    }


@router.get("/warehouses")
def list_warehouses(session: Session = Depends(get_session)) -> list[dict]:
    return [_warehouse_dict(w) for w in session.scalars(select(Warehouse).order_by(Warehouse.id))]


@router.post("/warehouses", status_code=201)
def create_warehouse(body: WarehouseCreate, session: Session = Depends(get_session)) -> dict:
    wh = Warehouse(**body.model_dump())
    session.add(wh)
    session.commit()
    return _warehouse_dict(wh)


@router.post("/racks", status_code=201)
def add_rack(body: RackCreate, session: Session = Depends(get_session)) -> dict:
    wh = _warehouse(session, body.warehouse_id)
    data = body.model_dump(exclude={"warehouse_id", "code"})
    rack = create_rack(session, wh, body.code, **data)
    session.commit()
    broker.publish(wh.id, {"type": "twin_changed"})
    return rack_dict(rack)


@router.get("/warehouses/{warehouse_id}/twin")
def twin(warehouse_id: int, session: Session = Depends(get_session)) -> dict:
    """Dijital ikizin bütün statik + son durum verisi (raflar, gözler, beklenen ve okunan)."""
    wh = _warehouse(session, warehouse_id)
    racks = session.scalars(
        select(Rack)
        .where(Rack.warehouse_id == wh.id)
        .options(
            selectinload(Rack.locations).selectinload(Location.expected_items),
            selectinload(Rack.locations).selectinload(Location.last_observation),
        )
        .order_by(Rack.code)
    ).all()
    robot = get_map_store().robot(wh.id)
    return {
        "warehouse": _warehouse_dict(wh),
        "racks": [
            {
                **rack_dict(r),
                "locations": [
                    location_state(loc, loc.last_observation, expected_codes(loc))
                    for loc in r.locations
                ],
            }
            for r in racks
        ],
        "robot": robot.as_dict(),
        "trail": [list(p) for p in robot.trail],
    }


@router.get("/warehouses/{warehouse_id}/map")
def lidar_map(warehouse_id: int) -> dict:
    """Birikmiş LiDAR haritası: voksel indeksleri [ix, iy, iz, ...] düz liste."""
    cells = get_map_store().cells(warehouse_id)
    return {"resolution": RESOLUTION_M, "cells": cells.ravel().tolist()}


@router.get("/warehouses/{warehouse_id}/summary")
def summary(warehouse_id: int, session: Session = Depends(get_session)) -> dict:
    _warehouse(session, warehouse_id)
    total = session.scalar(
        select(func.count(Location.id)).join(Rack).where(Rack.warehouse_id == warehouse_id)
    )
    rows = session.execute(
        select(Observation.status, func.count())
        .join(Location, Location.last_observation_id == Observation.id)
        .join(Rack, Location.rack_id == Rack.id)
        .where(Rack.warehouse_id == warehouse_id)
        .group_by(Observation.status)
    ).all()
    by_status = {st: n for st, n in rows}
    pending = session.scalar(
        select(func.count(Observation.id))
        .join(Location, Location.last_observation_id == Observation.id)
        .join(Rack, Location.rack_id == Rack.id)
        .where(Rack.warehouse_id == warehouse_id, Observation.review_status == ReviewStatus.PENDING)
    )
    last = session.scalar(
        select(Scan).where(Scan.warehouse_id == warehouse_id).order_by(Scan.started_at.desc())
    )
    scanned = sum(by_status.values())
    return {
        "locations": total,
        "scanned": scanned,
        "by_status": by_status,
        "pending_review": pending,
        "verified_ratio": round(by_status.get("verified", 0) / scanned, 4) if scanned else None,
        "last_scan": scan_dict(last) if last else None,
    }


@router.get("/locations/{location_id}")
def location_detail(location_id: int, session: Session = Depends(get_session)) -> dict:
    loc = session.scalar(
        select(Location)
        .where(Location.id == location_id)
        .options(
            selectinload(Location.expected_items),
            selectinload(Location.last_observation),
            selectinload(Location.rack),
        )
    )
    if loc is None:
        raise HTTPException(404, "Raf gözü bulunamadı")
    obs = loc.last_observation
    captures = []
    if obs is not None:
        captures = [
            capture_dict(c, loc.code)
            for c in session.scalars(
                select(Capture)
                .where(Capture.scan_id == obs.scan_id, Capture.location_id == loc.id)
                .options(selectinload(Capture.reads))
                .order_by(Capture.id.desc())
            )
        ]
    history = session.execute(
        select(Observation.scan_id, Observation.status, Observation.updated_at)
        .where(Observation.location_id == loc.id)
        .order_by(Observation.updated_at.desc())
        .limit(10)
    ).all()
    return {
        **location_state(loc, obs, expected_codes(loc)),
        "rack_code": loc.rack.code,
        "camera_height_mm": loc.camera_height_mm,
        "expected_items": [
            {"code": e.code, "description": e.description, "quantity": e.quantity}
            for e in sorted(loc.expected_items, key=lambda e: e.code)
        ],
        "review_note": obs.review_note if obs else None,
        "captures": captures,
        "history": [{"scan_id": s, "status": st, "updated_at": iso(t)} for s, st, t in history],
    }


@router.get("/review")
def review_queue(warehouse_id: int, session: Session = Depends(get_session)) -> list[dict]:
    """Manuel kontrol bekleyen gözler (her gözün en son sonucu)."""
    rows = session.execute(
        select(Location, Observation)
        .join(Observation, Location.last_observation_id == Observation.id)
        .join(Rack, Location.rack_id == Rack.id)
        .where(Rack.warehouse_id == warehouse_id, Observation.review_status == ReviewStatus.PENDING)
        .options(selectinload(Location.expected_items))
        .order_by(Observation.status, Location.code)
    ).all()
    out = []
    for loc, obs in rows:
        cap = session.scalar(
            select(Capture)
            .where(Capture.scan_id == obs.scan_id, Capture.location_id == loc.id)
            .order_by(Capture.id.desc())
        )
        out.append(
            {
                **location_state(loc, obs, expected_codes(loc)),
                "thumb_url": f"/media/{cap.thumb_path}" if cap else None,
            }
        )
    return out


@router.post("/observations/{observation_id}/review")
def review(
    observation_id: int, body: ReviewAction, session: Session = Depends(get_session)
) -> dict:
    obs = session.get(Observation, observation_id)
    if obs is None:
        raise HTTPException(404, "Gözlem bulunamadı")
    obs.review_status = (
        ReviewStatus.APPROVED if body.action == "approve" else ReviewStatus.CORRECTED
    )
    obs.review_note = body.note
    obs.reviewed_at = datetime.now(timezone.utc)
    session.commit()
    loc = session.scalar(
        select(Location)
        .where(Location.id == obs.location_id)
        .options(selectinload(Location.expected_items), selectinload(Location.rack))
    )
    state = location_state(loc, obs, expected_codes(loc))
    broker.publish(loc.rack.warehouse_id, {"type": "location", "location": state})
    verb = "onaylandı" if body.action == "approve" else "düzeltildi olarak işaretlendi"
    broker.event(loc.rack.warehouse_id, f"{loc.code} {verb}", "ok", location_id=loc.id)
    return state
