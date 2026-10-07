"""Kamera uçları: canlı görüntü (MJPEG), odak, otomatik odak, çek-ve-oku."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.camera import FOCUS_MAX, VIEWS, CameraError, CameraService, get_camera
from ..services.camera_read import read_codes

router = APIRouter(prefix="/camera", tags=["kamera"])

_BOUNDARY = "kare"


def _cam() -> CameraService:
    cam = get_camera()
    if cam is None:
        raise HTTPException(503, "Bu cihazda kamera yok (kamera yalnız Jetson'da çalışır).")
    return cam


def _view(view: int) -> int:
    if not 0 <= view <= VIEWS:
        raise HTTPException(422, f"Kamera 0..{VIEWS} olmalı (0: dördü birden)")
    return view


@router.get("")
def status() -> dict:
    cam = get_camera()
    if cam is None:
        return {"available": False, "running": False, "views": VIEWS, "focus_max": FOCUS_MAX}
    return cam.status()


@router.get("/stream")
async def stream(
    view: int = 0, w: int = Query(960, ge=160, le=3840), fps: float = Query(10, gt=0, le=30)
) -> StreamingResponse:
    """Canlı görüntü: <img src="/api/camera/stream?view=1"> ile gösterilir."""
    cam = _cam()
    view = _view(view)
    try:
        await run_in_threadpool(cam.start)
    except CameraError as e:
        raise HTTPException(503, str(e)) from e

    async def frames():
        seq = 0
        period = 1 / fps
        while True:
            t0 = asyncio.get_running_loop().time()
            try:
                data, seq = await run_in_threadpool(cam.jpeg, view, w, seq)
            except CameraError:
                break
            yield (
                (
                    f"--{_BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(data)}\r\n\r\n"
                ).encode()
                + data
                + b"\r\n"
            )
            wait = period - (asyncio.get_running_loop().time() - t0)
            if wait > 0:
                await asyncio.sleep(wait)

    return StreamingResponse(
        frames(),
        media_type=f"multipart/x-mixed-replace; boundary={_BOUNDARY}",
        # GZip ara katmanı akışı tamponlamasın.
        headers={"Cache-Control": "no-store", "Content-Encoding": "identity"},
    )


@router.get("/snapshot")
async def snapshot(view: int = 0, w: int = Query(1920, ge=160, le=4656)) -> Response:
    cam = _cam()
    view = _view(view)
    try:
        await run_in_threadpool(cam.start)
        data, _ = await run_in_threadpool(cam.jpeg, view, w, 0, 90)
    except CameraError as e:
        raise HTTPException(503, str(e)) from e
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


class FocusBody(BaseModel):
    position: int = Field(ge=0, le=FOCUS_MAX)


@router.post("/focus")
async def focus(body: FocusBody) -> dict:
    cam = _cam()
    try:
        await run_in_threadpool(cam.start)
    except CameraError as e:
        raise HTTPException(503, str(e)) from e
    cam.set_focus(body.position)
    return cam.status()


class AutofocusBody(BaseModel):
    view: int = 0


@router.post("/autofocus")
async def autofocus(body: AutofocusBody) -> dict:
    cam = _cam()
    view = _view(body.view)
    try:
        return await run_in_threadpool(cam.autofocus, view)
    except CameraError as e:
        raise HTTPException(503, str(e)) from e


class ReadBody(BaseModel):
    # Verilirse okunan kodlar bu deponun taramasına işlenir ve dijital ikiz güncellenir.
    warehouse_id: int | None = None
    # Boşsa göz, okunan kodun stok listesindeki yerinden bulunur.
    location_code: str | None = None
    scan_id: str | None = None


@router.post("/read")
async def read(body: ReadBody) -> dict:
    """Dört kameradan taze bir kare alır, her birinde kodları çözer, isteğe bağlı taramaya işler."""
    cam = _cam()
    try:
        frame = await run_in_threadpool(cam.capture)
        return await run_in_threadpool(
            read_codes,
            frame,
            warehouse_id=body.warehouse_id,
            location_code=body.location_code or None,
            scan_id=body.scan_id or None,
        )
    except CameraError as e:
        raise HTTPException(503, str(e)) from e
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
