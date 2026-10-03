"""Uygulama girişi: `uvicorn envanter.main:app` veya `envanter serve`."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from . import __version__
from .api import router as api_router
from .config import get_settings
from .db import SessionLocal, init_db
from .models import Warehouse
from .services.demo import ensure_demo_world, runner
from .services.live import broker
from .services.mapping import get_map_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    broker.bind(asyncio.get_running_loop())
    with SessionLocal() as session:
        empty = session.scalar(select(Warehouse.id).limit(1)) is None
    if empty:  # ilk açılışta arayüz boş kalmasın
        await asyncio.to_thread(ensure_demo_world)
    yield
    with contextlib.suppress(Exception):
        await runner.stop()
    get_map_store().flush()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Depo Envanter API",
        version=__version__,
        description="Dikey kameralı depo envanter robotu — tarama, kod okuma, mutabakat ve dijital ikiz.",
        lifespan=lifespan,
    )
    app.add_middleware(GZipMiddleware, minimum_size=2048)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["sistem"])
    def health() -> dict:
        return {"ok": True, "version": __version__}

    app.include_router(api_router)
    app.mount("/media", StaticFiles(directory=settings.data_dir), name="media")

    dist = settings.web_dist
    if (dist / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            if path.startswith(("api/", "media/")):
                raise HTTPException(404)
            f = (dist / path).resolve()
            if path and f.is_file() and dist.resolve() in f.parents:
                return FileResponse(f)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
