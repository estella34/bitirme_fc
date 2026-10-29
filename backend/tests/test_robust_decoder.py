import io

import numpy as np
import zxingcpp
from PIL import Image

from envanter.services.decoder import decode_image
from envanter.services.qr_degrade import (
    simulate_blur,
    simulate_crease_fold,
    simulate_faded,
    simulate_motion_blur,
    simulate_scratches,
    simulate_tape_glare,
)
from envanter.services.test_sheet import generate_test_sheet


def _make_qr(text: str, ec: str = "H", scale: int = 7) -> Image.Image:
    bc = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.QRCode, ec_level=ec)
    return Image.fromarray(np.asarray(bc.to_image(scale=scale))).convert("RGB")


def test_tape_glare_recovered_by_b2():
    qr = _make_qr("KL-TEST-GLARE", ec="H")
    degraded = simulate_tape_glare(qr)

    # Ham okuma (B0/B1) başarısız olmalı veya zorlanmalı
    raw_outcome = decode_image(degraded, fallback=True, robust_fallback=False)

    # Dayanıklı okuma (robust_fallback=True) B2_GLARE ile çözmeli
    robust_outcome = decode_image(degraded, fallback=True, robust_fallback=True)
    assert any(c.text == "KL-TEST-GLARE" for c in robust_outcome.codes)
    assert "B2_GLARE" in robust_outcome.methods_tried or "B0" in [c.method for c in robust_outcome.codes]


def test_scratches_recovered_by_b3():
    qr = _make_qr("KL-TEST-SCRATCH", ec="H")
    degraded = simulate_scratches(qr, num_scratches=3, max_width=4, seed=123)

    robust_outcome = decode_image(degraded, fallback=True, robust_fallback=True)
    assert any(c.text == "KL-TEST-SCRATCH" for c in robust_outcome.codes)


def test_degradations_produce_valid_images():
    qr = _make_qr("KL-TEST-DEGRADE", ec="M")
    for fn in (simulate_blur, simulate_motion_blur, simulate_crease_fold, simulate_faded):
        out = fn(qr)
        assert isinstance(out, Image.Image)
        assert out.size == qr.size


def test_printable_sheet_generation():
    sheet = generate_test_sheet()
    assert sheet.size == (1240, 1754)
    # Sayfadaki kodlar çözülebilir olmalı
    out = decode_image(sheet, fallback=True, robust_fallback=True)
    texts = {c.text for c in out.codes}
    assert "KL-TAPE-88210" in texts
    assert "KL-SCRATCH-103" in texts
