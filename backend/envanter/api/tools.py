"""Araçlar: kod okuma testi, stok içe aktarma, demo kontrolü."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, UnidentifiedImageError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import ExpectedItem, Location, Rack
from ..schemas import DemoStart
from ..services.decoder import decode_image
from ..services.demo import runner
from ..services.live import broker

router = APIRouter(tags=["araçlar"])


@router.post("/decode")
async def decode(image: UploadFile = File(...), robust: bool = True) -> dict:
    """Bir görüntüdeki QR/barkodları çözer; hiçbir şey kaydetmez (okuma testi)."""
    data = await image.read()
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(400, "Görüntü okunamadı") from e
    out = await run_in_threadpool(decode_image, img, robust_fallback=robust)
    return {
        "width": out.width,
        "height": out.height,
        "sharpness": round(out.sharpness, 1),
        "elapsed_ms": round(out.elapsed_ms, 1),
        "methods_tried": out.methods_tried,
        "codes": [
            {"text": c.text, "symbology": c.symbology, "method": c.method, "polygon": c.polygon}
            for c in out.codes
        ],
    }


@router.get("/test-sheet")
async def get_test_sheet(format: str = "pdf"):
    """Yazdırılabilir A4 QR test sayfasını döndürür (PDF veya PNG)."""
    from fastapi.responses import Response
    from ..services.test_sheet import generate_test_sheet

    canvas = await run_in_threadpool(generate_test_sheet)
    buf = io.BytesIO()
    if format.lower() == "png":
        canvas.save(buf, format="PNG")
        media_type = "image/png"
        filename = "depogoz_test_sayfasi.png"
    else:
        canvas.save(buf, format="PDF", resolution=150.0)
        media_type = "application/pdf"
        filename = "depogoz_test_sayfasi.pdf"
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.post("/stock/import")
async def import_stock(
    warehouse_id: int,
    file: UploadFile = File(...),
    replace: bool = True,
    session: Session = Depends(get_session),
) -> dict:
    """WMS'ten beklenen stok: CSV sütunları location_code, code[, quantity][, description].

    replace=True: bu depodaki mevcut beklenen stok silinip dosyadakiyle değiştirilir.
    """
    text = (await file.read()).decode("utf-8-sig")
    sample = text[:2048]
    delim = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    need = {"location_code", "code"}
    if not reader.fieldnames or not need <= set(reader.fieldnames):
        raise HTTPException(400, "CSV başlıkları en az location_code ve code içermeli")

    locs = {
        code: lid
        for code, lid in session.execute(
            select(Location.code, Location.id).join(Rack).where(Rack.warehouse_id == warehouse_id)
        )
    }
    if replace:
        session.execute(
            delete(ExpectedItem).where(ExpectedItem.location_id.in_(list(locs.values())))
        )

    added, unknown = 0, set()
    seen: set[tuple[int, str]] = set()
    for row in reader:
        lid = locs.get((row.get("location_code") or "").strip())
        code = (row.get("code") or "").strip()
        if lid is None:
            unknown.add(row.get("location_code"))
            continue
        if not code or (lid, code) in seen:
            continue
        seen.add((lid, code))
        session.add(
            ExpectedItem(
                location_id=lid,
                code=code,
                quantity=int(row.get("quantity") or 1),
                description=(row.get("description") or None),
                source="csv",
            )
        )
        added += 1
    session.commit()
    broker.publish(warehouse_id, {"type": "twin_changed"})
    broker.event(warehouse_id, f"Beklenen stok içe aktarıldı: {added} kayıt")
    return {"added": added, "unknown_locations": sorted(x for x in unknown if x)}


@router.get("/demo")
def demo_status() -> dict:
    return runner.status()


@router.post("/demo/start")
async def demo_start(body: DemoStart) -> dict:
    try:
        return await runner.start(body.speed, body.seed)
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e


@router.post("/demo/stop")
async def demo_stop() -> dict:
    return await runner.stop()
