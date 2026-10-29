"""Depo ortamındaki fiziksel hasarları yazılımsal olarak simüle eden modül.

Simüle edilen durumlar:
  1. Bulanıklık (defocus / lens odak hatası / titreşim)
  2. Koli bandı ve parlama (specular reflection / highlight)
  3. Çizik ve yırtıklar (scratch / abrasion)
  4. Katlanma ve kırışıklık gölgesi (crease / fold line)
  5. Düşük kontrast ve solma (faded / low contrast)
"""

from __future__ import annotations

import random
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


def simulate_blur(image: Image.Image, radius: float = 3.0) -> Image.Image:
    """Lens odak hatası veya mekanizma titreşimi nedeniyle oluşan Gauss bulanıklığı."""
    return image.filter(ImageFilter.GaussianBlur(radius))


def simulate_motion_blur(image: Image.Image, passes: int = 2) -> Image.Image:
    """Dikey eksen hareketi sırasında oluşan dikey hareket bulanıklığı (motion blur)."""
    # Pillow ImageFilter.Kernel yalnız (3, 3) veya (5, 5) destekler
    kernel = [
        0, 0, 1, 0, 0,
        0, 0, 1, 0, 0,
        0, 0, 1, 0, 0,
        0, 0, 1, 0, 0,
        0, 0, 1, 0, 0,
    ]
    k_filter = ImageFilter.Kernel((5, 5), kernel, scale=5)
    res = image
    for _ in range(passes):
        res = res.filter(k_filter)
    return res


def simulate_tape_glare(
    image: Image.Image,
    x_range: tuple[float, float] = (0.2, 0.8),
    y_range: tuple[float, float] = (0.3, 0.6),
    tape_color: tuple[int, int, int, int] = (255, 255, 230, 140),
    glare_width: int = 12,
) -> Image.Image:
    """Koli etiketinin üzerine çekilmiş şeffaf veya sarı koli bandı ve ışık yansıması."""
    img = image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(overlay)
    w, h = img.size

    x0, x1 = int(w * x_range[0]), int(w * x_range[1])
    y0, y1 = int(h * y_range[0]), int(h * y_range[1])

    # Bant gövdesi
    d.rectangle([x0, y0, x1, y1], fill=tape_color)
    # Parlayan yansıma şeridi (specular highlight)
    gy = int(y0 + (y1 - y0) * 0.4)
    d.line([x0, gy, x1, gy], fill=(255, 255, 255, 220), width=glare_width)
    # Bant kenarı hafif gölge
    d.line([x0, y1, x1, y1], fill=(160, 150, 130, 180), width=2)

    merged = Image.alpha_composite(img, overlay)
    return merged.convert("RGB")


def simulate_scratches(
    image: Image.Image,
    num_scratches: int = 3,
    max_width: int = 5,
    seed: int | None = 42,
) -> Image.Image:
    """Etiket yüzeyinde sürtünme ve yırtık sonucu oluşan beyaz/açık renk çizikler."""
    rng = random.Random(seed)
    img = image.copy()
    d = ImageDraw.Draw(img)
    w, h = img.size

    for _ in range(num_scratches):
        x0 = rng.randint(int(w * 0.1), int(w * 0.8))
        y0 = rng.randint(int(h * 0.1), int(h * 0.8))
        length = rng.randint(int(w * 0.3), int(w * 0.7))
        angle = rng.uniform(-0.8, 0.8)
        x1 = int(x0 + length * np.cos(angle))
        y1 = int(y0 + length * np.sin(angle))
        width = rng.randint(2, max_width)
        d.line([x0, y0, x1, y1], fill="white", width=width)

    return img


def simulate_crease_fold(
    image: Image.Image,
    position: float = 0.5,
    width: int = 6,
) -> Image.Image:
    """Koli kenarına katlanan etiketlerde oluşan dikey katlama çizgisi ve gölgesi."""
    img = image.copy()
    d = ImageDraw.Draw(img)
    w, h = img.size
    fx = int(w * position)

    # Katlanma gölgesi (karanlık hat)
    d.line([fx - 1, 0, fx - 1, h], fill=(70, 70, 70), width=width // 2 + 1)
    # Katlanma sırtı (açık renk ışık kırılması)
    d.line([fx + 2, 0, fx + 2, h], fill=(240, 240, 240), width=width // 2)
    return img


def simulate_faded(image: Image.Image, contrast_factor: float = 0.4) -> Image.Image:
    """Termal yazıcısı zayıflamış veya güneşte solmuş düşük kontrastlı etiket."""
    from PIL import ImageEnhance

    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(contrast_factor)


DegradationType = Literal["blur", "motion_blur", "tape_glare", "scratches", "crease", "faded"]


def apply_degradation(image: Image.Image, kind: DegradationType) -> Image.Image:
    if kind == "blur":
        return simulate_blur(image, radius=2.5)
    elif kind == "motion_blur":
        return simulate_motion_blur(image, passes=2)
    elif kind == "tape_glare":
        return simulate_tape_glare(image)
    elif kind == "scratches":
        return simulate_scratches(image, num_scratches=3, max_width=5)
    elif kind == "crease":
        return simulate_crease_fold(image)
    elif kind == "faded":
        return simulate_faded(image, contrast_factor=0.35)
    return image
