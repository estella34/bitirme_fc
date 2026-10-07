"""Kamera uçları: donanımsız (Mac/CI) davranış ve sahte kaynakla çek-ve-oku hattı."""

import io
import random
import time

import numpy as np
import pytest
from PIL import Image

from envanter.services.camera import CameraService, set_camera, split_views
from envanter.services.demo import BoxTruth, render_location_image


class FakeSource:
    def __init__(self, frame: np.ndarray) -> None:
        self.frame = frame

    def open(self) -> None:
        pass

    def read(self) -> np.ndarray:
        time.sleep(0.01)
        return self.frame

    def close(self) -> None:
        pass


def _frame_with(tile_img: bytes, view: int) -> np.ndarray:
    """1280×800'lük demo görüntüsünü 2×2 birleşik karenin `view` (1..4) parçasına koyar."""
    tile = np.asarray(Image.open(io.BytesIO(tile_img)).convert("RGB"))[:, :, ::-1]
    h, w = tile.shape[:2]
    frame = np.full((h * 2, w * 2, 3), 40, np.uint8)
    y, x = divmod(view - 1, 2)
    frame[y * h : (y + 1) * h, x * w : (x + 1) * w] = tile
    return frame


@pytest.fixture
def fake_camera():
    def use(frame: np.ndarray) -> CameraService:
        cam = CameraService(lambda: FakeSource(frame), i2c=None, idle_s=5)
        set_camera(cam)
        return cam

    yield use
    set_camera(None)


def test_no_camera_hardware(client):
    set_camera(None)
    st = client.get("/api/camera").json()
    assert st["available"] is False
    assert client.post("/api/camera/read", json={}).status_code == 503
    assert client.get("/api/camera/snapshot").status_code == 503


def test_split_views_order():
    f = np.zeros((4, 4), np.uint8)
    f[:2, 2:] = 2
    f[2:, :2] = 3
    assert [int(v.max()) for v in split_views(f)] == [0, 2, 3, 0]


def test_snapshot_and_focus(client, fake_camera):
    fake_camera(np.full((200, 320, 3), 128, np.uint8))
    r = client.get("/api/camera/snapshot", params={"view": 2})
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(r.content)).size == (160, 100)
    assert client.post("/api/camera/focus", json={"position": 1234}).json()["focus"] == 1234
    assert client.get("/api/camera/snapshot", params={"view": 9}).status_code == 422


def test_read_assigns_location_by_code(client, fake_camera):
    wh = next(w for w in client.get("/api/warehouses").json() if w["code"] == "DEMO")
    twin = client.get(f"/api/warehouses/{wh['id']}/twin").json()
    loc = next(x for r in twin["racks"] for x in r["locations"] if len(x["expected"]) == 2)
    img = render_location_image([BoxTruth(c, "x") for c in loc["expected"]], random.Random(3))
    fake_camera(_frame_with(img, 2))

    res = client.post("/api/camera/read", json={"warehouse_id": wh["id"]}).json()
    v2 = res["views"][1]
    assert {c["text"] for c in v2["codes"]} == set(loc["expected"])
    assert v2["location_code"] == loc["code"]
    assert v2["location"]["status"] == "verified"
    assert all(not v["codes"] for i, v in enumerate(res["views"]) if i != 1)
    assert res["scan_id"]

    # Aynı elle tarama yeniden kullanılır.
    again = client.post("/api/camera/read", json={"warehouse_id": wh["id"]}).json()
    assert again["scan_id"] == res["scan_id"]


def test_read_without_warehouse_only_decodes(client, fake_camera):
    img = render_location_image([BoxTruth("KL-777001", "x")], random.Random(5))
    fake_camera(_frame_with(img, 4))
    res = client.post("/api/camera/read", json={}).json()
    assert res["scan_id"] is None
    assert [c["text"] for c in res["views"][3]["codes"]] == ["KL-777001"]
    assert res["views"][3]["location"] is None
