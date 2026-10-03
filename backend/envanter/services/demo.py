"""Demo simülasyonu: donanım olmadan uçtan uca sistemi göstermek için.

Simüle edilen: depo (duvarlar, klima, kolon, panolar), raflar ve gerçek koli içerikleri,
robot hareketi, 3B LiDAR (Livox Mid-360 benzeri görüş alanı) ve kamera görüntüleri.
Simüle EDİLMEYEN: görüntüler gerçek kod çözücüden (zxing-cpp), sonuçlar gerçek mutabakat
mantığından, harita gerçek telemetri hattından geçer. Yani demo, yazılımın kendisini çalıştırır.

`box_count` (görünen koli sayısı) ileride koli tespit modülünün (veya derinlik/LiDAR) vereceği
değerdir; demoda simülasyonun gerçek değeri kullanılır.
"""

from __future__ import annotations

import asyncio
import io
import math
import random
from dataclasses import dataclass, field

import numpy as np
import zxingcpp
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..db import SessionLocal
from ..models import (
    ExpectedItem,
    Location,
    Observation,
    ObservationStatus,
    Rack,
    Scan,
    ScanMode,
    ScanStatus,
    Warehouse,
)
from .inventory import finish_scan, ingest_capture, start_scan
from .layout import bay_front_center, create_rack
from .live import broker
from .mapping import get_map_store
from .telemetry import ingest_telemetry

DEMO_CODE = "DEMO"
WIDTH, LENGTH, WALL_H = 24.0, 14.0, 3.2
LEVELS, POSITIONS, BAY_W, DEPTH, LEVEL_H = 3, 4, 1.2, 0.8, 0.5

# (kod, x, y, yaw) — A sırası kuzeyde koridora (−y) bakar, B sırası güneyde (+y) bakar.
DEMO_RACKS = [
    ("A01", 4.0, 9.6, 0.0),
    ("A02", 9.6, 9.6, 0.0),
    ("A03", 15.2, 9.6, 0.0),
    ("B01", 8.8, 5.4, 180.0),
    ("B02", 14.4, 5.4, 180.0),
    ("B03", 20.0, 5.4, 180.0),
]

# Sabit engeller: (xmin, ymin, zmin, xmax, ymax, zmax). Arayüz bunları göstermez; yalnız
# LiDAR onları "görür". Haritada beliren her şey sensörden gelir.
OBSTACLES = np.array(
    [
        (-0.2, -0.2, 0, 1.0, 0.0, WALL_H),  # güney duvar (kapının batısı)
        (3.0, -0.2, 0, WIDTH + 0.2, 0.0, WALL_H),  # güney duvar (kapının doğusu)
        (1.0, -0.2, 2.2, 3.0, 0.0, WALL_H),  # kapı lentosu
        (-0.2, LENGTH, 0, WIDTH + 0.2, LENGTH + 0.2, WALL_H),  # kuzey duvar
        (-0.2, 0, 0, 0.0, LENGTH, WALL_H),  # batı duvar
        (WIDTH, 0, 0, WIDTH + 0.2, LENGTH, WALL_H),  # doğu duvar
        (11.0, 13.6, 2.3, 12.4, LENGTH, 2.9),  # klima iç ünitesi (kuzey duvar)
        (0.0, 6.0, 0.9, 0.25, 7.0, 1.9),  # elektrik panosu (batı duvar)
        (WIDTH - 0.3, 3.0, 0.8, WIDTH, 3.8, 1.6),  # yangın dolabı (doğu duvar)
        (21.8, 9.8, 0, 22.2, 10.2, WALL_H),  # taşıyıcı kolon
        (18.0, 1.0, 0, 19.2, 2.2, 1.1),  # zeminde palet yığını
        (6.0, 12.6, 0, 8.4, 13.8, 0.9),  # zeminde bekleyen sevkiyat
    ],
    dtype=np.float64,
)

PRODUCTS = [
    "Ayçiçek Yağı 5 L ×4",
    "Makarna 500 g ×20",
    "Toz Deterjan 6 kg ×3",
    "Su 1,5 L ×6",
    "Siyah Çay 1 kg ×12",
    "Un 5 kg ×4",
    "Domates Salçası 830 g ×12",
    "Pirinç 2,5 kg ×8",
    "Bulaşık Tableti ×40",
    "Kağıt Havlu ×12",
    "Zeytin 1 kg ×6",
    "Mercimek 1 kg ×10",
]

DOCK = (1.6, 7.5)
LANE_A, LANE_B = 8.6, 6.4  # robot şeritleri (rafa ~1 m)
V_LIN, V_ANG, V_MAST = 0.6, 0.9, 0.5  # m/s, rad/s, m/s
MAST_MIN_MM = 150.0
TICK_S = 0.1


# --- dünya kurulumu ------------------------------------------------------------


def ensure_demo_world() -> int:
    """Demo deposunu (yoksa) oluşturur ve kimliğini döndürür."""
    with SessionLocal() as session:
        wh = session.scalar(select(Warehouse).where(Warehouse.code == DEMO_CODE))
        if wh is not None:
            return wh.id
        wh = Warehouse(code=DEMO_CODE, name="Demo Deposu", width_m=WIDTH, length_m=LENGTH)
        session.add(wh)
        rng = random.Random(42)
        serial = 100000
        for code, x, y, yaw in DEMO_RACKS:
            rack = create_rack(
                session,
                wh,
                code,
                x=x,
                y=y,
                yaw_deg=yaw,
                levels=LEVELS,
                positions=POSITIONS,
                bay_width_m=BAY_W,
                depth_m=DEPTH,
                level_height_m=LEVEL_H,
                aisle="K1",
            )
            for loc in rack.locations:
                n = rng.choices([0, 1, 2, 3], weights=[1, 2, 4, 3])[0]
                product = rng.choice(PRODUCTS)
                for _ in range(n):
                    serial += rng.randint(1, 40)
                    loc.expected_items.append(
                        ExpectedItem(code=f"KL-{serial}", description=product, source="demo")
                    )
        session.commit()
        return wh.id


# --- gerçeklik ve senaryo ------------------------------------------------------


@dataclass
class BoxTruth:
    code: str
    product: str
    damaged: bool = False


@dataclass
class Scenario:
    truth: dict[str, list[BoxTruth]]
    anomalies: dict[str, str]  # göz kodu → açıklama
    summary: list[str] = field(default_factory=list)


def build_scenario(expected: dict[str, list[tuple[str, str]]], seed: int) -> Scenario:
    rng = random.Random(seed)
    truth = {loc: [BoxTruth(c, p) for c, p in items] for loc, items in expected.items()}
    anomalies: dict[str, str] = {}
    used: set[str] = set()

    def pick(min_boxes: int) -> str:
        cands = sorted(k for k, v in truth.items() if len(v) >= min_boxes and k not in used)
        k = rng.choice(cands)
        used.add(k)
        return k

    for _ in range(2):  # kayıp koli
        loc = pick(2)
        lost = truth[loc].pop(rng.randrange(len(truth[loc])))
        anomalies[loc] = f"Kayıp koli: {lost.code}"
    for _ in range(2):  # etiketi hasarlı koli
        loc = pick(2)
        rng.choice(truth[loc]).damaged = True
        anomalies[loc] = "Etiketi hasarlı koli"
    src, dst = pick(1), pick(1)  # yanlış göze konmuş koli
    moved = truth[src].pop(rng.randrange(len(truth[src])))
    truth[dst].append(moved)
    anomalies[src] = f"{moved.code} başka göze taşınmış"
    anomalies[dst] = f"{moved.code} yanlış göze konmuş"
    cands = sorted(k for k, v in truth.items() if 1 <= len(v) <= 2 and k not in used)
    loc = rng.choice(cands)
    used.add(loc)
    truth[loc].append(BoxTruth("KL-999" + str(rng.randint(100, 999)), "Kayıt dışı koli"))
    anomalies[loc] = "Sistemde kaydı olmayan koli"

    summary = ["2 kayıp koli", "2 hasarlı etiket", "1 yanlış yere konmuş koli", "1 kayıt dışı koli"]
    return Scenario(truth, anomalies, summary)


# --- kamera görüntüsü sentezi ----------------------------------------------------


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # eski Pillow
        return ImageFont.load_default()


def render_location_image(boxes: list[BoxTruth], rng: random.Random) -> bytes:
    """Kameranın bir raf gözünde göreceği sahneyi çizer (koliler + QR etiketler)."""
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), (52, 56, 62))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 56, h], fill=(28, 72, 150))  # dikmeler
    d.rectangle([w - 56, 0, w, h], fill=(28, 72, 150))
    d.rectangle([0, h - 92, w, h - 44], fill=(232, 122, 28))  # turuncu kiriş
    d.rectangle([0, 0, w, 40], fill=(232, 122, 28))
    f_code, f_text = _font(22), _font(16)

    n = len(boxes)
    if n:
        slot = (w - 150) / n
        for i, b in enumerate(boxes):
            bw = slot * rng.uniform(0.8, 0.92)
            bh = rng.uniform(470, 600)
            x0 = 75 + i * slot + (slot - bw) / 2
            y1 = h - 92
            y0 = y1 - bh
            tone = rng.randint(-14, 14)
            d.rectangle(
                [x0, y0, x0 + bw, y1],
                fill=(196 + tone, 152 + tone, 104 + tone),
                outline=(128, 94, 60),
                width=3,
            )
            d.rectangle([x0 + bw * 0.42, y0, x0 + bw * 0.58, y0 + 70], fill=(214, 182, 130))

            scale = 6 if bw > 300 else 5 if bw > 240 else 4
            qr = zxingcpp.create_barcode(b.code, zxingcpp.BarcodeFormat.QRCode).to_image(
                scale=scale
            )
            qr_img = Image.fromarray(np.asarray(qr)).convert("RGB")
            lw = min(bw - 20, qr_img.width + 60)
            lh = qr_img.height + 80
            lx = x0 + (bw - lw) / 2 + rng.uniform(-8, 8)
            ly = y0 + rng.uniform(80, max(90, bh - lh - 30))
            d.rectangle([lx, ly, lx + lw, ly + lh], fill=(248, 248, 244), outline=(190, 190, 190))
            qx, qy = int(lx + (lw - qr_img.width) / 2), int(ly + 8)
            img.paste(qr_img, (qx, qy))
            d.text((lx + 10, qy + qr_img.height + 6), b.code, fill=(20, 20, 20), font=f_code)
            d.text(
                (lx + 10, qy + qr_img.height + 36), b.product[:24], fill=(70, 70, 70), font=f_text
            )
            if b.damaged:  # koli bandı QR'ın sol yarısını kapatmış (iki bulucu desen gider)
                d.rectangle(
                    [qx - 6, qy - 6, qx + qr_img.width * 0.56, qy + qr_img.height + 6],
                    fill=(206, 172, 118),
                )
                d.line([lx, ly + lh * 0.3, lx + lw, ly + lh * 0.75], fill=(150, 120, 90), width=4)

    # optik kusurlar: hafif bulanıklık, ışık farkı, sensör gürültüsü
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 0.9)))
    a = np.asarray(img, dtype=np.float32) * rng.uniform(0.85, 1.08)
    a += np.random.default_rng(rng.randint(0, 1 << 30)).normal(0, 4.0, a.shape)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


# --- LiDAR simülasyonu -------------------------------------------------------------


class LidarSim:
    """Kutulara karşı ışın izleme. Görüş alanı Livox Mid-360 benzeri: 360° × (−7°…52°)."""

    RANGE_M = 14.0
    SENSOR = (0.12, 0.0, 0.55)  # robot ekseninde konum (m)

    def __init__(self, boxes: np.ndarray, rng: np.random.Generator) -> None:
        self.bmin = boxes[:, :3]
        self.bmax = boxes[:, 3:]
        self.rng = rng
        self.az_step = math.radians(2.0)
        self.elev = np.radians(np.linspace(-7.0, 52.0, 20))

    def scan(self, x: float, y: float, yaw: float) -> np.ndarray:
        rng = self.rng
        az = np.arange(0.0, 2 * math.pi, self.az_step) + rng.uniform(0, self.az_step)
        el = self.elev + rng.uniform(0, self.elev[1] - self.elev[0])
        A, E = np.meshgrid(az + yaw, el)
        dirs = np.stack([np.cos(E) * np.cos(A), np.cos(E) * np.sin(A), np.sin(E)], axis=-1).reshape(
            -1, 3
        )
        dirs[np.abs(dirs) < 1e-9] = 1e-9

        c, s = math.cos(yaw), math.sin(yaw)
        sx, sy, sz = self.SENSOR
        o = np.array([x + c * sx - s * sy, y + s * sx + c * sy, sz])

        inv = 1.0 / dirs
        t1 = (self.bmin[None] - o) * inv[:, None]
        t2 = (self.bmax[None] - o) * inv[:, None]
        tmin = np.minimum(t1, t2).max(axis=2)
        tmax = np.maximum(t1, t2).min(axis=2)
        hit = (tmax >= tmin) & (tmin > 0.05)
        t_box = np.where(hit, tmin, np.inf).min(axis=1)
        t_floor = np.where(dirs[:, 2] < 0, -o[2] / dirs[:, 2], np.inf)
        t = np.minimum(t_box, t_floor)
        ok = t < self.RANGE_M
        pts = o + dirs[ok] * t[ok, None]
        pts += rng.normal(0, 0.01, pts.shape)

        rel = pts[:, :2] - (x, y)  # dünya → robot ekseni
        return np.column_stack(
            [c * rel[:, 0] + s * rel[:, 1], -s * rel[:, 0] + c * rel[:, 1], pts[:, 2]]
        )


# --- robot ve senaryo yürütücüsü -------------------------------------------------


def _wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


class DemoRunner:
    def __init__(self) -> None:
        self.task: asyncio.Task | None = None
        self.state: dict = {"running": False}

    def status(self) -> dict:
        return dict(self.state)

    async def start(self, speed: float = 4.0, seed: int = 7) -> dict:
        if self.task and not self.task.done():
            raise RuntimeError("Demo zaten çalışıyor")
        wid = await asyncio.to_thread(ensure_demo_world)
        speed = max(0.25, min(speed, 20.0))
        self.state = {"running": True, "warehouse_id": wid, "speed": speed, "progress": 0.0}
        self.task = asyncio.create_task(self._run(wid, speed, seed))
        await asyncio.sleep(0)
        return self.status()

    async def stop(self) -> dict:
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        return self.status()

    # -- iç işleyiş --

    async def _run(self, wid: int, speed: float, seed: int) -> None:
        self.speed = speed
        self.wid = wid
        self.x, self.y, self.yaw, self.mast = DOCK[0], DOCK[1], 0.0, MAST_MIN_MM
        self.lidar = LidarSim(lidar_obstacles(), np.random.default_rng(seed))
        self.img_rng = random.Random(seed)
        self.tick = 0
        scan_id = None
        try:
            racks, expected = await asyncio.to_thread(self._prepare, wid)
            scenario = build_scenario(expected, seed)
            self.state = {
                "running": True,
                "warehouse_id": wid,
                "speed": speed,
                "seed": seed,
                "scenario": scenario.summary,
                "progress": 0.0,
                "result": None,
            }
            broker.publish(wid, {"type": "reset"})
            broker.event(wid, "Demo başladı · senaryo: " + ", ".join(scenario.summary))
            scan_id = await asyncio.to_thread(self._start_scan, wid)
            self.state["scan_id"] = scan_id

            await self._telemetry("starting", lidar=True)
            stops = self._plan(racks)
            done = 0
            for kind, *args in stops:
                if kind == "goto":
                    await self._drive_to(*args)
                elif kind == "turn":
                    await self._rotate_to(args[0])
                elif kind == "bay":
                    rack, pos = args
                    await self._scan_bay(scan_id, rack, pos, scenario)
                    done += 1
                    self.state["progress"] = round(done / (len(racks) * POSITIONS), 3)
            await self._telemetry("idle", lidar=True)

            result = await asyncio.to_thread(self._finish, scan_id, scenario)
            self.state["result"] = result
            broker.event(
                wid,
                f"Senaryo kontrolü: {result['detected']}/{result['anomalies']} anomali yakalandı, "
                f"{result['false_alarms']} yanlış alarm",
                "ok" if result["detected"] == result["anomalies"] else "warn",
            )
        except asyncio.CancelledError:
            if scan_id:
                await asyncio.to_thread(self._cancel, scan_id)
            broker.event(wid, "Demo durduruldu", "warn")
            raise
        except Exception as exc:  # demo hatası sunucuyu düşürmesin
            broker.event(wid, f"Demo hatası: {exc}", "error")
            if scan_id:
                await asyncio.to_thread(self._cancel, scan_id, ScanStatus.FAILED)
            raise
        finally:
            self.state["running"] = False
            get_map_store().flush()

    def _prepare(self, wid: int):
        get_map_store().reset(wid)
        with SessionLocal() as session:
            session.execute(
                update(Location)
                .where(Location.rack_id.in_(select(Rack.id).where(Rack.warehouse_id == wid)))
                .values(last_observation_id=None)
            )
            session.commit()
            racks = session.scalars(
                select(Rack)
                .where(Rack.warehouse_id == wid)
                .options(selectinload(Rack.locations).selectinload(Location.expected_items))
            ).all()
            expected = {
                loc.code: [
                    (e.code, e.description or "")
                    for e in sorted(loc.expected_items, key=lambda e: e.code)
                ]
                for r in racks
                for loc in r.locations
            }
        return racks, expected

    def _start_scan(self, wid: int) -> str:
        with SessionLocal() as session:
            return start_scan(session, wid, ScanMode.DEMO, "Demo simülasyonu").id

    def _cancel(self, scan_id: str, status: ScanStatus = ScanStatus.CANCELLED) -> None:
        with SessionLocal() as session:
            scan = session.get(Scan, scan_id)
            if scan and scan.status == ScanStatus.RUNNING:
                finish_scan(session, scan, status)

    def _finish(self, scan_id: str, scenario: Scenario) -> dict:
        with SessionLocal() as session:
            scan = session.get(Scan, scan_id)
            finish_scan(session, scan)
            rows = session.execute(
                select(Location.code, Observation.status)
                .join(Location, Observation.location_id == Location.id)
                .where(Observation.scan_id == scan_id)
            ).all()
        flagged = {
            code
            for code, st in rows
            if st in (ObservationStatus.CONFLICT, ObservationStatus.UNREADABLE)
        }
        anomalies = set(scenario.anomalies)
        return {
            "anomalies": len(anomalies),
            "detected": len(anomalies & flagged),
            "false_alarms": len(flagged - anomalies),
            "details": scenario.anomalies,
        }

    def _plan(self, racks: list[Rack]) -> list[tuple]:
        a_side = sorted((r for r in racks if r.code.startswith("A")), key=lambda r: r.x)
        b_side = sorted((r for r in racks if r.code.startswith("B")), key=lambda r: -r.x)
        plan: list[tuple] = [("goto", 3.0, LANE_A), ("turn", 0.0)]
        for r in a_side:
            for p in range(1, r.positions + 1):
                bx, _ = bay_front_center(r, p)
                plan += [("goto", bx, LANE_A), ("bay", r, p)]
        plan += [("goto", 21.0, LANE_A), ("goto", 21.0, LANE_B), ("turn", math.pi)]
        for r in b_side:
            for p in range(1, r.positions + 1):
                bx, _ = bay_front_center(r, p)
                plan += [("goto", bx, LANE_B), ("bay", r, p)]
        plan += [("goto", 3.0, LANE_B), ("goto", *DOCK), ("turn", 0.0)]
        return plan

    async def _telemetry(self, state: str, lidar: bool) -> None:
        pts = self.lidar.scan(self.x, self.y, self.yaw) if lidar else None
        ingest_telemetry(
            self.wid, x=self.x, y=self.y, yaw=self.yaw, mast_mm=self.mast, state=state, points=pts
        )
        await asyncio.sleep(TICK_S / self.speed)

    async def _step(self, state: str) -> None:
        self.tick += 1
        await self._telemetry(state, lidar=self.tick % 2 == 0)

    async def _rotate_to(self, target: float) -> None:
        while True:
            err = _wrap(target - self.yaw)
            if abs(err) < 1e-3:
                break
            self.yaw = _wrap(self.yaw + max(-V_ANG * TICK_S, min(V_ANG * TICK_S, err)))
            await self._step("turning")

    async def _drive_to(self, tx: float, ty: float) -> None:
        dist = math.hypot(tx - self.x, ty - self.y)
        if dist < 1e-3:
            return
        heading = math.atan2(ty - self.y, tx - self.x)
        # Geri gitmek yerine dönmek: hedef arkadaysa önce o yöne dön.
        await self._rotate_to(heading)
        while dist > 1e-3:
            step = min(V_LIN * TICK_S, dist)
            self.x += math.cos(heading) * step
            self.y += math.sin(heading) * step
            dist -= step
            await self._step("moving")
        self.x, self.y = tx, ty

    async def _move_mast(self, target_mm: float) -> None:
        while abs(target_mm - self.mast) > 0.5:
            delta = max(-V_MAST * 1000 * TICK_S, min(V_MAST * 1000 * TICK_S, target_mm - self.mast))
            self.mast += delta
            await self._step("mast")
        self.mast = target_mm

    async def _scan_bay(self, scan_id: str, rack: Rack, pos: int, scenario: Scenario) -> None:
        locs = sorted(
            (loc for loc in rack.locations if loc.position == pos), key=lambda loc_: loc_.level
        )
        for loc in locs:
            await self._move_mast(loc.camera_height_mm or MAST_MIN_MM)
            for _ in range(3):  # titreşimin yatışmasını bekle
                await self._step("settling")
            boxes = scenario.truth.get(loc.code, [])
            await asyncio.to_thread(self._capture, scan_id, loc.code, boxes)
            await self._step("capturing")
        await self._move_mast(MAST_MIN_MM)

    def _capture(self, scan_id: str, loc_code: str, boxes: list[BoxTruth]) -> None:
        data = render_location_image(boxes, self.img_rng)
        ingest_capture(
            scan_id,
            data,
            location_code=loc_code,
            camera_id="cam1",
            vertical_position_mm=self.mast,
            box_count=len(boxes),
        )


def lidar_obstacles() -> np.ndarray:
    """LiDAR için raflar da engeldir (dolu kutu olarak yaklaşıklanır)."""
    rows = [OBSTACLES]
    for _, x, y, yaw in DEMO_RACKS:
        length, height = POSITIONS * BAY_W, LEVELS * LEVEL_H + 0.05
        if yaw == 0:
            rows.append(np.array([[x, y, 0, x + length, y + DEPTH, height]]))
        else:  # 180°
            rows.append(np.array([[x - length, y - DEPTH, 0, x, y, height]]))
    return np.vstack(rows)


runner = DemoRunner()
