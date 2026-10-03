"""Canlı akış: arayüz bu WebSocket'e bağlanıp robot, harita ve göz güncellemelerini alır."""

from __future__ import annotations

import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.live import broker

router = APIRouter(tags=["canlı"])


@router.websocket("/ws")
async def ws(websocket: WebSocket, warehouse_id: int) -> None:
    await websocket.accept()
    queue = broker.subscribe(warehouse_id)

    async def pump() -> None:
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)

    sender = asyncio.create_task(pump())
    try:
        while True:  # istemciden gelen mesajları (ping) tüket; kapanınca çık
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await sender
        broker.unsubscribe(warehouse_id, queue)
