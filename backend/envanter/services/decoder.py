"""Klasik kod çözücü (QR + 1D/2D barkod), zxing-cpp üzerinde.

Yol haritasındaki karşılaştırma yöntemleri:
  B0  tam görüntü → çözücü
  B1  tam görüntü → klasik ön işleme (kontrast, keskinleştirme, büyütme) → çözücü
A1 (AI ile bölge tespiti + kırpma) ileride `crop` parametresiyle aynı fonksiyonu kullanacak;
böylece bütün yöntemler aynı çözücüyü paylaşır ve adil karşılaştırılır.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import zxingcpp
from PIL import Image, ImageFilter, ImageOps

# Küçük kenarı bundan kısa görüntüler B1'de büyütülür (küçük barkodlar için).
_UPSCALE_BELOW_PX = 1400


@dataclass
class DecodedCode:
    text: str
    symbology: str
    method: str
    polygon: list[list[float]]  # orijinal görüntü koordinatlarında 4 köşe
    confidence: float = 1.0


@dataclass
class DecodeOutcome:
    codes: list[DecodedCode] = field(default_factory=list)
    width: int = 0
    height: int = 0
    sharpness: float = 0.0
    elapsed_ms: float = 0.0
    methods_tried: list[str] = field(default_factory=list)


def _polygon(
    pos: zxingcpp.Position, scale: float, dx: float = 0, dy: float = 0
) -> list[list[float]]:
    pts = (pos.top_left, pos.top_right, pos.bottom_right, pos.bottom_left)
    return [[p.x / scale + dx, p.y / scale + dy] for p in pts]


def _read(img: Image.Image, method: str, scale: float = 1.0, dx: float = 0, dy: float = 0):
    out: list[DecodedCode] = []
    for r in zxingcpp.read_barcodes(img):
        if not r.valid or not r.text:
            continue
        out.append(
            DecodedCode(
                text=r.text,
                symbology=str(r.format),
                method=method,
                polygon=_polygon(r.position, scale, dx, dy),
            )
        )
    return out


def sharpness_score(gray: Image.Image) -> float:
    """Laplace varyansı (küçültülmüş görüntüde). Düşük değer → bulanık kare."""
    g = gray.copy()
    g.thumbnail((640, 640))
    a = np.asarray(g, dtype=np.float32)
    lap = -4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
    return float(lap.var())


def preprocess_b1(gray: Image.Image) -> tuple[Image.Image, float]:
    """Klasik ön işleme (B1): Kontrast, keskinleştirme ve küçük kodlar için büyütme."""
    img = ImageOps.autocontrast(gray, cutoff=1)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=3))
    scale = 1.0
    if min(img.size) < _UPSCALE_BELOW_PX:
        scale = 2.0
        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
    return img, scale


def preprocess_b2_glare(gray: Image.Image) -> tuple[Image.Image, float]:
    """Parlama ve şeffaf bant ön işleme (B2): Yerel arka plan çıkarımı ile yansımayı sıfırlar."""
    blur_rad = max(9, int(min(gray.size) * 0.05))
    bg = gray.filter(ImageFilter.BoxBlur(blur_rad))
    arr_gray = np.asarray(gray, dtype=np.float32)
    arr_bg = np.asarray(bg, dtype=np.float32)
    # Yerel kontrast normalizasyonu: parlak bant şeritlerini ve gölgeleri dengeler
    norm = np.clip(128.0 + (arr_gray - arr_bg) * 2.8, 0, 255).astype(np.uint8)
    img = Image.fromarray(norm)
    img = ImageOps.autocontrast(img, cutoff=2)
    scale = 1.0
    if min(img.size) < _UPSCALE_BELOW_PX:
        scale = 1.5
        img = img.resize((int(img.width * 1.5), int(img.height * 1.5)), Image.Resampling.LANCZOS)
    return img, scale


def preprocess_b3_repair(gray: Image.Image) -> tuple[Image.Image, float]:
    """Çizik ve aşınma onarımı (B3): Morfolojik kapanma ile kırık modülleri birleştirir."""
    # MinFilter beyaz çizikleri ve modül kırılmalarını koyulaştırarak kapatır
    repaired = gray.filter(ImageFilter.MinFilter(3))
    img = ImageOps.autocontrast(repaired, cutoff=2)
    scale = 1.0
    if min(img.size) < _UPSCALE_BELOW_PX:
        scale = 1.5
        img = img.resize((int(img.width * 1.5), int(img.height * 1.5)), Image.Resampling.LANCZOS)
    return img, scale


def _dedupe(codes: list[DecodedCode]) -> list[DecodedCode]:
    seen: dict[tuple[str, str], DecodedCode] = {}
    for c in codes:
        seen.setdefault((c.text, c.symbology), c)
    return list(seen.values())


def decode_image(
    image: Image.Image,
    *,
    fallback: bool = True,
    robust_fallback: bool = False,
    crop: tuple[int, int, int, int] | None = None,
    method: str = "B0",
) -> DecodeOutcome:
    """Görüntüdeki tüm kodları çözer.

    fallback:        B0 hiçbir şey bulamazsa B1'i dener.
    robust_fallback: B1 de bulamazsa B2_GLARE (bant/parlama) ve B3_REPAIR (çizik) dener.
    crop:            (x0, y0, x1, y1) verilirse yalnız o bölge çözülür; koordinatlar yine
                     orijinal görüntüye göre döner (A1 için).
    """
    t0 = time.perf_counter()
    gray = ImageOps.exif_transpose(image).convert("L")
    outcome = DecodeOutcome(width=gray.width, height=gray.height)
    outcome.sharpness = sharpness_score(gray)

    dx = dy = 0.0
    region = gray
    if crop is not None:
        dx, dy = float(crop[0]), float(crop[1])
        region = gray.crop(crop)

    outcome.methods_tried.append(method)
    codes = _read(region, method, dx=dx, dy=dy)

    if not codes and fallback:
        # Aşama 1: Standart netleştirme ve büyütme (B1)
        b1_method = "B1" if method == "B0" else f"{method}+"
        outcome.methods_tried.append(b1_method)
        pre1, scale1 = preprocess_b1(region)
        codes = _read(pre1, b1_method, scale=scale1, dx=dx, dy=dy)

        # Aşama 2 & 3: Zorlu depo hasarları (koli bandı parlaması ve çizikler)
        if not codes and robust_fallback:
            b2_method = "B2_GLARE"
            outcome.methods_tried.append(b2_method)
            pre2, scale2 = preprocess_b2_glare(region)
            codes = _read(pre2, b2_method, scale=scale2, dx=dx, dy=dy)

            if not codes:
                b3_method = "B3_REPAIR"
                outcome.methods_tried.append(b3_method)
                pre3, scale3 = preprocess_b3_repair(region)
                codes = _read(pre3, b3_method, scale=scale3, dx=dx, dy=dy)

    outcome.codes = _dedupe(codes)
    outcome.elapsed_ms = (time.perf_counter() - t0) * 1000
    return outcome
