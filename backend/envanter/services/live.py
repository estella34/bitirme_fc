"""Canlı olay yayını (WebSocket aboneleri için süreç içi yayıncı).

Tarama hattı iş parçacıklarında (threadpool) çalıştığı için `publish` iş parçacığı
güvenlidir: olaylar olay döngüsüne `call_soon_threadsafe` ile aktarılır.
"""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone
from typing import Any

_QUEUE_LIMIT = 2000


class Broker:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._subs: dict[int, set[asyncio.Queue]] = {}

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self, warehouse_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=_QUEUE_LIMIT)
        self._subs.setdefault(warehouse_id, set()).add(q)
        return q

    def unsubscribe(self, warehouse_id: int, q: asyncio.Queue) -> None:
        self._subs.get(warehouse_id, set()).discard(q)

    def publish(self, warehouse_id: int, message: dict[str, Any]) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        message.setdefault("ts", datetime.now(timezone.utc).isoformat())
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is self._loop:
            self._fanout(warehouse_id, message)
        else:
            self._loop.call_soon_threadsafe(self._fanout, warehouse_id, message)

    def _fanout(self, warehouse_id: int, message: dict[str, Any]) -> None:
        for q in list(self._subs.get(warehouse_id, ())):
            if q.full():  # yavaş istemci: en eski olayı at, akış dursun istemeyiz
                with contextlib.suppress(asyncio.QueueEmpty):
                    q.get_nowait()
            q.put_nowait(message)

    def event(self, warehouse_id: int, text: str, level: str = "info", **extra: Any) -> None:
        """Arayüzdeki olay akışında görünen kısa insan-okur mesaj."""
        self.publish(warehouse_id, {"type": "event", "level": level, "text": text, **extra})


broker = Broker()
