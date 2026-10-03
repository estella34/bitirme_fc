import random

import numpy as np

from envanter.services.demo import BoxTruth, LidarSim, lidar_obstacles, render_location_image


def _demo_wh(client):
    whs = client.get("/api/warehouses").json()
    return next(w for w in whs if w["code"] == "DEMO")


def _location_with(twin, n_expected):
    for r in twin["racks"]:
        for loc in r["locations"]:
            if len(loc["expected"]) == n_expected:
                return loc
    raise AssertionError("uygun göz yok")


def _upload(client, scan_id, loc_code, boxes, box_count):
    data = render_location_image(boxes, random.Random(1))
    return client.post(
        f"/api/scans/{scan_id}/captures",
        files={"image": ("c.jpg", data, "image/jpeg")},
        data={"location_code": loc_code, "camera_id": "cam1", "box_count": str(box_count)},
    )


def test_health(client):
    assert client.get("/api/health").json()["ok"] is True


def test_twin_has_demo_layout(client):
    wh = _demo_wh(client)
    twin = client.get(f"/api/warehouses/{wh['id']}/twin").json()
    assert len(twin["racks"]) == 6
    assert all(len(r["locations"]) == 12 for r in twin["racks"])


def test_capture_pipeline_verified_and_missing(client):
    wh = _demo_wh(client)
    twin = client.get(f"/api/warehouses/{wh['id']}/twin").json()
    scan = client.post("/api/scans", json={"warehouse_id": wh["id"], "mode": "robot"}).json()

    full = _location_with(twin, 3)
    boxes = [BoxTruth(c, "x") for c in full["expected"]]
    r = _upload(client, scan["id"], full["code"], boxes, len(boxes))
    assert r.status_code == 201, r.text
    assert r.json()["location"]["status"] == "verified"

    # Aynı tarama, başka göz: bir koli kayıp → çelişki (kırmızı)
    other = next(
        loc
        for rk in twin["racks"]
        for loc in rk["locations"]
        if len(loc["expected"]) == 3 and loc["code"] != full["code"]
    )
    boxes = [BoxTruth(c, "x") for c in other["expected"][:2]]
    st = _upload(client, scan["id"], other["code"], boxes, 2).json()["location"]
    assert st["status"] == "conflict"
    assert st["missing"] == [other["expected"][2]]

    queue = client.get("/api/review", params={"warehouse_id": wh["id"]}).json()
    assert any(q["code"] == other["code"] for q in queue)

    approved = client.post(
        f"/api/observations/{st['observation_id']}/review", json={"action": "approve"}
    ).json()
    assert approved["review_status"] == "approved"

    detail = client.get(f"/api/locations/{other['id']}").json()
    assert detail["captures"] and detail["captures"][0]["reads"]

    csv_text = client.get(f"/api/scans/{scan['id']}/export.csv").text
    assert other["code"] in csv_text and "çelişki" in csv_text

    done = client.post(f"/api/scans/{scan['id']}/finish").json()
    assert done["status"] == "completed"
    assert done["counts"] == {"verified": 1, "conflict": 1}


def test_unknown_location_is_404(client):
    wh = _demo_wh(client)
    scan = client.post("/api/scans", json={"warehouse_id": wh["id"]}).json()
    r = _upload(client, scan["id"], "YOK-1-1", [], 0)
    assert r.status_code == 404


def test_telemetry_builds_map(client):
    wh = _demo_wh(client)
    sim = LidarSim(lidar_obstacles(), np.random.default_rng(0))
    pts = sim.scan(5.0, 7.5, 0.0)
    assert len(pts) > 500
    r = client.post(
        "/api/robot/telemetry",
        json={
            "warehouse_id": wh["id"],
            "pose": {"x": 5.0, "y": 7.5, "yaw": 0.0},
            "points": pts.tolist(),
        },
    )
    assert r.json()["new_cells"] > 100
    m = client.get(f"/api/warehouses/{wh['id']}/map").json()
    assert len(m["cells"]) % 3 == 0 and len(m["cells"]) > 300


def test_decode_endpoint(client):
    data = render_location_image([BoxTruth("KL-424242", "x")], random.Random(0))
    r = client.post("/api/decode", files={"image": ("a.jpg", data, "image/jpeg")}).json()
    assert [c["text"] for c in r["codes"]] == ["KL-424242"]
