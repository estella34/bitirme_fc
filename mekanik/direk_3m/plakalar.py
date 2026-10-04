"""stl/ klasöründeki parçaları Bambu Lab A1 tablasına (256×256 mm) dizip baskıya hazır
.3mf dosyaları üretir: her tabla bir dosya, her parça ayrı nesne (Türkçe adlı).

Kullanım:  python3 plakalar.py      (build.sh sonunda otomatik çalışır)
"""

from __future__ import annotations

import struct
import zipfile
from pathlib import Path

BED = 256.0
MARGIN = 8.0
GAP = 6.0
HERE = Path(__file__).resolve().parent

# (dosya, Türkçe ad, adet)
PLATES = {
    "tabla1_pabuclar": [
        ("pad_2.7", "pabuc_2.7mm", 28),
        ("pad_2.5", "pabuc_2.5mm_ince", 8),
        ("pad_2.9", "pabuc_2.9mm_kalin", 8),
    ],
    "tabla2_yakalar_makaralar": [
        ("collar0", "yaka_0_60mm", 1),
        ("collar1", "yaka_1_45mm", 1),
        ("collar2", "yaka_2_30mm", 1),
        ("sleeve1", "ayak_kilifi_1_45mm", 1),
        ("sleeve2", "ayak_kilifi_2_30mm", 1),
        ("cap3", "kapak_15mm", 1),
        ("sleeve3", "ayak_kilifi_3_15mm", 1),
        ("drum", "motor_tamburu", 1),
        ("pulley", "makara", 4),
    ],
    "tabla3_taban_tipalar": [
        ("base", "taban_yuvasi", 1),
        ("plug1", "ic_tipa_1_45mm", 1),
        ("plug2", "ic_tipa_2_30mm", 1),
        ("plug3", "ic_tipa_3_15mm", 1),
    ],
}


def read_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    b = path.read_bytes()
    n = struct.unpack("<I", b[80:84])[0]
    tris = []
    for i in range(n):
        v = struct.unpack("<12f", b[84 + i * 50 : 84 + i * 50 + 48])
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris


def bounds(tris):
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    return min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)


def pack(items):
    """Raf yerleşimi: büyükten küçüğe, satır satır. items: [(ad, w, d)] → {i: (x, y)}"""
    order = sorted(range(len(items)), key=lambda i: -items[i][2] * 1000 - items[i][1])
    pos, x, y, row_h = {}, MARGIN, MARGIN, 0.0
    for i in order:
        _, w, d = items[i]
        if x + w > BED - MARGIN:
            x, y, row_h = MARGIN, y + row_h + GAP, 0.0
        if y + d > BED - MARGIN:
            raise SystemExit(f"Tablaya sığmadı: {items[i][0]}")
        pos[i] = (x, y)
        x += w + GAP
        row_h = max(row_h, d)
    return pos


def mesh_xml(tris, dx, dy, dz):
    index: dict[tuple, int] = {}
    verts, faces = [], []
    for t in tris:
        ids = []
        for p in t:
            key = (round(p[0] + dx, 4), round(p[1] + dy, 4), round(p[2] + dz, 4))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            ids.append(index[key])
        if len(set(ids)) == 3:
            faces.append(ids)
    v = "".join(f'<vertex x="{a}" y="{b}" z="{c}"/>' for a, b, c in verts)
    f = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return f"<mesh><vertices>{v}</vertices><triangles>{f}</triangles></mesh>"


def write_3mf(out: Path, objects):
    objs, items = [], []
    for oid, (name, xml) in enumerate(objects, start=1):
        objs.append(f'<object id="{oid}" name="{name}" type="model">{xml}</object>')
        items.append(f'<item objectid="{oid}"/>')
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="tr-TR" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        '<metadata name="Application">DepoGoz plakalar.py</metadata>'
        f'<resources>{"".join(objs)}</resources><build>{"".join(items)}</build></model>'
    )
    ctypes = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    )
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def main() -> None:
    outdir = HERE / "tablalar"
    outdir.mkdir(exist_ok=True)
    layouts = {}
    for plate, parts in PLATES.items():
        expanded = []
        for stl, name, count in parts:
            tris = read_stl(HERE / "stl" / f"{stl}.stl")
            x0, y0, z0, x1, y1, _ = bounds(tris)
            for i in range(count):
                label = name if count == 1 else f"{name}_{i + 1}"
                expanded.append((label, tris, (x0, y0, z0), x1 - x0, y1 - y0))
        pos = pack([(e[0], e[3], e[4]) for e in expanded])
        objects = []
        for i, (label, tris, (x0, y0, z0), w, d) in enumerate(expanded):
            px, py = pos[i]
            objects.append((label, mesh_xml(tris, px - x0, py - y0, -z0)))
        write_3mf(outdir / f"{plate}.3mf", objects)
        layouts[plate] = [(e[0], pos[i][0], pos[i][1], e[3], e[4]) for i, e in enumerate(expanded)]
        print(f"{plate}.3mf: {len(objects)} parça")
    try:
        draw(layouts, outdir)
    except ImportError:
        pass


def draw(layouts, outdir: Path) -> None:
    from PIL import Image, ImageDraw

    s = 2.4
    for plate, rects in layouts.items():
        img = Image.new("RGB", (int(BED * s) + 20, int(BED * s) + 20), "white")
        d = ImageDraw.Draw(img)
        d.rectangle([10, 10, 10 + BED * s, 10 + BED * s], outline="#888", width=2)
        for label, x, y, w, h in rects:
            # 3MF'te y yukarı; görselde aşağı → çevir
            X0, Y1 = 10 + x * s, 10 + (BED - y) * s
            d.rectangle([X0, Y1 - h * s, X0 + w * s, Y1], fill="#f2c39b", outline="#c2622a", width=2)
            if w > 18:
                d.text((X0 + 3, Y1 - h * s + 3), label.replace("_", " ")[:18], fill="#222")
        img.save(outdir / f"{plate}.png")


if __name__ == "__main__":
    main()
