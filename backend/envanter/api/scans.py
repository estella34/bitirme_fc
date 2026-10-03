"""Taramalar ve görüntü alımı (robot bu uçları kullanır)."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Location, Observation, Scan, ScanMode, ScanStatus, Warehouse
from ..schemas import ScanCreate
from ..services.inventory import (
    STATUS_TR,
    finish_scan,
    ingest_capture,
    scan_counts,
    scan_dict,
    start_scan,
)

router = APIRouter(tags=["tarama"])

MAX_IMAGE_BYTES = 40 * 1024 * 1024


def _scan(session: Session, scan_id: str) -> Scan:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(404, "Tarama bulunamadı")
    return scan


@router.get("/scans")
def list_scans(warehouse_id: int, limit: int = 50, session: Session = Depends(get_session)):
    scans = session.scalars(
        select(Scan)
        .where(Scan.warehouse_id == warehouse_id)
        .order_by(Scan.started_at.desc())
        .limit(min(limit, 500))
    ).all()
    return [scan_dict(s, scan_counts(session, s.id)) for s in scans]


@router.post("/scans", status_code=201)
def create_scan(body: ScanCreate, session: Session = Depends(get_session)) -> dict:
    if session.get(Warehouse, body.warehouse_id) is None:
        raise HTTPException(404, "Depo bulunamadı")
    scan = start_scan(session, body.warehouse_id, ScanMode(body.mode), body.note)
    return scan_dict(scan)


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str, session: Session = Depends(get_session)) -> dict:
    scan = _scan(session, scan_id)
    return scan_dict(scan, scan_counts(session, scan.id))


@router.post("/scans/{scan_id}/finish")
def finish(scan_id: str, session: Session = Depends(get_session)) -> dict:
    scan = _scan(session, scan_id)
    if scan.status != ScanStatus.RUNNING:
        raise HTTPException(409, "Tarama zaten bitmiş")
    finish_scan(session, scan)
    return scan_dict(scan, scan_counts(session, scan.id))


@router.post("/scans/{scan_id}/captures", status_code=201)
async def add_capture(
    scan_id: str,
    image: UploadFile = File(...),
    location_code: str | None = Form(None),
    camera_id: str = Form("cam0"),
    vertical_position_mm: float | None = Form(None),
    box_count: int | None = Form(None),
) -> dict:
    """Robotun her çekimde çağırdığı uç: görüntü + meta veri → kod çözme + mutabakat."""
    data = await image.read()
    if not data:
        raise HTTPException(400, "Boş görüntü")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Görüntü çok büyük")
    try:
        return await run_in_threadpool(
            ingest_capture,
            scan_id,
            data,
            location_code=location_code or None,
            camera_id=camera_id,
            vertical_position_mm=vertical_position_mm,
            box_count=box_count,
        )
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except OSError as e:  # PIL: tanınmayan görüntü
        raise HTTPException(400, f"Görüntü okunamadı: {e}") from e


@router.get("/scans/{scan_id}/export.csv")
def export_csv(scan_id: str, session: Session = Depends(get_session)) -> StreamingResponse:
    """Tarama sonucunu Excel'de açılabilir CSV olarak indirir (UTF-8 BOM, ; ayraç)."""
    _scan(session, scan_id)
    rows = session.execute(
        select(Location.code, Observation)
        .join(Location, Observation.location_id == Location.id)
        .where(Observation.scan_id == scan_id)
        .order_by(Location.code)
    ).all()
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(
        [
            "göz",
            "durum",
            "açıklama",
            "görünen_koli",
            "okunan",
            "beklenen",
            "eksik",
            "beklenmeyen",
            "inceleme",
        ]
    )
    for code, o in rows:
        w.writerow(
            [
                code,
                STATUS_TR.get(o.status, o.status),
                o.reason,
                "" if o.box_count is None else o.box_count,
                " ".join(o.codes),
                " ".join(o.expected),
                " ".join(o.missing),
                " ".join(o.unexpected),
                o.review_status,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{scan_id}.csv"'},
    )
