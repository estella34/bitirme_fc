"""Çek-ve-oku: dört kameralı kareden kodları çözer, isterse taramaya işler.

Göz bulunurken önce verilen `location_code`, yoksa okunan kodların stok listesinde (ExpectedItem)
kayıtlı olduğu göz kullanılır. Kodu stok listesinde olmayan görüntüler taramaya işlenmez,
yalnız sonuç olarak döner (elle denemede "bu kod depoda kayıtlı değil" diye görünür).
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from PIL import Image
from sqlalchemy import select

from ..config import get_settings
from ..db import SessionLocal
from ..models import ExpectedItem, Location, Rack, Scan, ScanMode, ScanStatus, Warehouse
from .camera import split_views
from .decoder import decode_image
from .inventory import ingest_capture, start_scan


def _to_pil(bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.ascontiguousarray(bgr[:, :, ::-1]))


def _jpeg(img: Image.Image) -> bytes:
    import io

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _locations_by_code(warehouse_id: int, codes: set[str]) -> dict[str, str]:
    if not codes:
        return {}
    with SessionLocal() as session:
        rows = session.execute(
            select(ExpectedItem.code, Location.code)
            .join(Location, ExpectedItem.location_id == Location.id)
            .join(Rack, Location.rack_id == Rack.id)
            .where(Rack.warehouse_id == warehouse_id, ExpectedItem.code.in_(codes))
        ).all()
    return dict(rows)


def _manual_scan(warehouse_id: int, scan_id: str | None) -> str:
    """Verilen taramayı ya da deponun açık elle taramasını kullanır; yoksa yenisini açar."""
    with SessionLocal() as session:
        if session.get(Warehouse, warehouse_id) is None:
            raise LookupError(f"Depo bulunamadı: {warehouse_id}")
        if scan_id:
            scan = session.get(Scan, scan_id)
            if scan is None:
                raise LookupError(f"Tarama bulunamadı: {scan_id}")
            return scan.id
        scan = session.scalar(
            select(Scan)
            .where(
                Scan.warehouse_id == warehouse_id,
                Scan.mode == ScanMode.MANUAL,
                Scan.status == ScanStatus.RUNNING,
            )
            .order_by(Scan.started_at.desc())
            .limit(1)
        )
        if scan is None:
            scan = start_scan(session, warehouse_id, ScanMode.MANUAL, "Kamerayla elle okuma")
        return scan.id


def read_codes(
    frame: np.ndarray,
    *,
    warehouse_id: int | None = None,
    location_code: str | None = None,
    scan_id: str | None = None,
) -> dict:
    settings = get_settings()
    views = []
    if settings.camera_channel == 0:
        tiles = list(enumerate(split_views(frame), start=1))
    else:
        # Tek kamera modu: seçilen kanala tüm kareyi ata, diğerlerine boş kare
        tiles = []
        for ch in range(1, 5):
            if ch == settings.camera_channel:
                tiles.append((ch, frame))
            else:
                tiles.append(
                    (ch, np.zeros((frame.shape[0] // 2, frame.shape[1] // 2, 3), dtype=np.uint8))
                )

    for i, tile in tiles:
        img = _to_pil(tile)
        out = decode_image(
            img, fallback=settings.decode_fallback, robust_fallback=True
        )
        views.append(
            {
                "camera": i,
                "image": img,
                "width": out.width,
                "height": out.height,
                "sharpness": round(out.sharpness, 1),
                "elapsed_ms": round(out.elapsed_ms, 1),
                "codes": [
                    {
                        "text": c.text,
                        "symbology": c.symbology,
                        "method": c.method,
                        "polygon": c.polygon,
                    }
                    for c in out.codes
                ],
                "location_code": None,
                "location": None,
                "capture_id": None,
            }
        )

    used_scan = None
    if warehouse_id is not None:
        all_codes = {c["text"] for v in views for c in v["codes"]}
        known = _locations_by_code(warehouse_id, all_codes)
        for v in views:
            if not v["codes"]:
                continue
            loc = location_code
            if loc is None:
                votes = Counter(known[c["text"]] for c in v["codes"] if c["text"] in known)
                loc = votes.most_common(1)[0][0] if votes else None
            if loc is None:
                continue
            used_scan = used_scan or _manual_scan(warehouse_id, scan_id)
            res = ingest_capture(
                used_scan, _jpeg(v["image"]), location_code=loc, camera_id=f"cam{v['camera']}"
            )
            v["location_code"] = loc
            v["location"] = res["location"]
            v["capture_id"] = res["capture"]["id"]

    for v in views:
        del v["image"]
    return {
        "scan_id": used_scan,
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
        "views": views,
        "total_codes": sum(len(v["codes"]) for v in views),
    }
