import io
import random

import numpy as np
import zxingcpp
from PIL import Image, ImageFilter

from envanter.services.decoder import decode_image
from envanter.services.demo import BoxTruth, render_location_image


def _qr(text: str, scale: int = 5) -> Image.Image:
    img = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.QRCode).to_image(scale=scale)
    return Image.fromarray(np.asarray(img)).convert("RGB")


def test_reads_qr_and_reports_position():
    canvas = Image.new("RGB", (800, 600), (120, 110, 100))
    canvas.paste(_qr("KL-123456"), (300, 200))
    out = decode_image(canvas)
    assert [c.text for c in out.codes] == ["KL-123456"]
    assert out.codes[0].method == "B0"
    xs = [p[0] for p in out.codes[0].polygon]
    assert 300 <= min(xs) and max(xs) <= 300 + 200


def test_reads_linear_barcode():
    bc = zxingcpp.create_barcode("8690000123452", zxingcpp.BarcodeFormat.EAN13).to_image(scale=3)
    canvas = Image.new("RGB", (900, 500), "white")
    canvas.paste(Image.fromarray(np.asarray(bc)), (200, 150))
    out = decode_image(canvas)
    assert [c.text for c in out.codes] == ["8690000123452"]
    assert "EAN" in out.codes[0].symbology


def test_b1_fallback_runs_only_when_b0_fails():
    canvas = Image.new("RGB", (640, 480), (128, 128, 128))
    canvas.paste(_qr("KL-777001"), (250, 150))
    assert decode_image(canvas).methods_tried == ["B0"]

    blurred = canvas.filter(ImageFilter.GaussianBlur(6))
    out = decode_image(blurred)
    assert out.methods_tried == ["B0", "B1"]
    assert decode_image(blurred, fallback=False).methods_tried == ["B0"]


def test_crop_returns_original_coordinates():
    """A1 (AI tespit + kırpma) için: kırpılmış bölgedeki kodun köşeleri tam görüntüye göre döner."""
    canvas = Image.new("RGB", (1600, 1000), (90, 90, 90))
    canvas.paste(_qr("KL-246810", scale=4), (1100, 600))
    out = decode_image(canvas, crop=(1000, 500, 1500, 950), method="A1")
    assert [c.method for c in out.codes] == ["A1"]
    xs = [p[0] for p in out.codes[0].polygon]
    ys = [p[1] for p in out.codes[0].polygon]
    assert 1100 <= min(xs) < max(xs) <= 1100 + 140
    assert 600 <= min(ys) < max(ys) <= 600 + 140


def test_demo_images_decode_except_damaged_labels():
    """Demo görüntüleri gerçek çözücüden geçtiği için: sağlam etiket okunmalı, hasarlı okunmamalı."""
    rng = random.Random(3)
    for n in (1, 2, 3, 4):
        boxes = [BoxTruth(f"KL-{500000 + i}", "Test ürünü") for i in range(n)]
        boxes[-1].damaged = n >= 2
        data = render_location_image(boxes, rng)
        got = {c.text for c in decode_image(Image.open(io.BytesIO(data))).codes}
        want = {b.code for b in boxes if not b.damaged}
        assert got == want, (n, got, want)
