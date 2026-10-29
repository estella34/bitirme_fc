"""DepoGöz: Yazdırılabilir A4 Gerçekçi Depo Barkod & QR Dayanıklılık Test Sayfası.

Depolarda en yaygın olan 1D çizgili barkodlar (Code 128, EAN-13, Code 39) ile
2D kodları (QR Code, DataMatrix) eşit ve dengeli şekilde içerir.
Koli bandı, katlama ve çizik hasarlarını hem 1D hem 2D üzerinde test etmeyi sağlar.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import zxingcpp
from PIL import Image, ImageDraw, ImageFont


def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        return ImageFont.truetype(font_path, size, index=0 if not bold else 1)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def _make_qr(text: str, ec: str = "H", scale: int = 5) -> Image.Image:
    bc = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.QRCode, ec_level=ec)
    arr = np.asarray(bc.to_image(scale=scale))
    return Image.fromarray(arr).convert("RGB")


def _make_barcode(text: str, fmt=zxingcpp.BarcodeFormat.Code128, scale: int = 2) -> Image.Image:
    bc = zxingcpp.create_barcode(text, fmt)
    arr = np.asarray(bc.to_image(scale=scale))
    return Image.fromarray(arr).convert("RGB")


def generate_test_sheet() -> Image.Image:
    """A4 boyutunda (150 DPI: 1240 x 1754 piksel) gerçekçi depo test sayfası."""
    w, h = 1240, 1754
    canvas = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(canvas)

    f_title = _get_font(28, bold=True)
    f_sub = _get_font(16)
    f_head = _get_font(19, bold=True)
    f_body = _get_font(14)
    f_mono = _get_font(15, bold=True)
    f_small = _get_font(12)

    # Dış kenarlık
    d.rectangle([25, 25, w - 25, h - 25], outline=(40, 40, 40), width=2)
    # Başlık şeridi
    d.rectangle([25, 25, w - 25, 115], fill=(244, 246, 250), outline=(200, 205, 215), width=1)
    d.text((45, 38), "DEPOGÖZ — DEPO BARKOD (1D) & QR (2D) DAYANIKLILIK TEST ŞABLONU", fill=(20, 35, 60), font=f_title)
    d.text(
        (45, 78),
        "Depolarda yaygın 1D Barkod (Code 128, EAN-13, Code 39) ve 2D QR kodların fiziksel hasar testi şablonu.",
        fill=(70, 80, 95),
        font=f_sub,
    )

    # 4 Ana Hasar Test Bölgesi (Her kutuda hem 1D Barkod hem QR Kod var!)
    sections = [
        {
            "title": "BÖLGE 1: KOLİ BANDI & PARLAMA TESTİ (1D Barkod + QR Kod)",
            "desc": "Koli bandını hem çizgili barkodun hem QR kodun üstünü kapatacak şekilde yapıştırın.\n"
                    "Parlayan ışık altında zxing çözücünün ve B2_GLARE filtresinin başarısını test edin.",
            "barcode_type": zxingcpp.BarcodeFormat.Code128,
            "barcode_text": "KL-TAPE-88210",
            "barcode_label": "Code 128 Koli Takip",
            "qr_text": "KL-TAPE-88210",
            "qr_ec": "H",
            "box": [45, 130, w - 45, 470],
            "accent": (230, 140, 30),
        },
        {
            "title": "BÖLGE 2: KUTU KENARI KATLANMA & KIRIŞIKLIK TESTİ",
            "desc": "Kırmızı kesikli çizgi boyunca sayfayı katlayıp parmağınızla iyice bastırın.\n"
                    "1D barkod çizgilerinin kırılmasını ve 2D QR kodun geometrik bozulmasını simüle eder.",
            "barcode_type": zxingcpp.BarcodeFormat.EAN13,
            "barcode_text": "8690123456789",
            "barcode_label": "EAN-13 Ürün Barkodu",
            "qr_text": "KL-FOLD-44109",
            "qr_ec": "H",
            "box": [45, 490, w - 45, 830],
            "accent": (220, 50, 50),
            "fold_line": True,
        },
        {
            "title": "BÖLGE 3: ÇİZİK, YIRTILMA & SÜRTÜNME TESTİ",
            "desc": "Tükenmez kalemle soldaki 1D barkodun ve sağdaki QR kodun üzerinden 2-3 çizgi çekin.\n"
                    "1D barkodun çiziklere hassasiyetini vs QR kodun Level H (%30 onarım) gücünü karşılaştırın.",
            "barcode_type": zxingcpp.BarcodeFormat.Code39,
            "barcode_text": "LOC-A02-B1",
            "barcode_label": "Code 39 Raf Lokasyon",
            "qr_text": "KL-SCRATCH-103",
            "qr_ec": "H",
            "box": [45, 850, w - 45, 1190],
            "accent": (140, 60, 180),
        },
    ]

    for s in sections:
        bx0, by0, bx1, by1 = s["box"]
        # Kart arkaplanı
        d.rectangle([bx0, by0, bx1, by1], fill=(253, 254, 255), outline=(195, 205, 218), width=2)
        # Başlık
        d.rectangle([bx0, by0, bx1, by0 + 36], fill=(242, 246, 252), outline=(205, 215, 228))
        d.rectangle([bx0, by0, bx0 + 6, by0 + 36], fill=s["accent"])
        d.text((bx0 + 15, by0 + 8), s["title"], fill=(30, 45, 70), font=f_head)
        d.text((bx0 + 15, by0 + 44), s["desc"], fill=(70, 80, 95), font=f_body)

        # Sol taraf: 1D Çizgili Barkod
        d.rectangle([bx0 + 20, by0 + 85, bx0 + 580, by1 - 15], fill=(248, 250, 253), outline=(215, 222, 232))
        d.text((bx0 + 35, by0 + 95), f"1D ÇİZGİLİ BARKOD: {s['barcode_label']}", fill=(30, 50, 80), font=f_mono)
        bc = _make_barcode(s["barcode_text"], fmt=s["barcode_type"], scale=2)
        canvas.paste(bc, (bx0 + 40, by0 + 130))
        d.text((bx0 + 40, by0 + 130 + bc.height + 8), f"Metin: {s['barcode_text']}", fill=(40, 40, 40), font=f_body)

        # Sağ taraf: 2D QR Kod (Level H)
        d.rectangle([bx0 + 610, by0 + 85, bx1 - 20, by1 - 15], fill=(248, 250, 253), outline=(215, 222, 232))
        d.text((bx0 + 625, by0 + 95), "2D KAREKOD: QR Code (Level H - %30 Kurtarma)", fill=(30, 100, 60), font=f_mono)
        qr = _make_qr(s["qr_text"], ec=s["qr_ec"], scale=5)
        canvas.paste(qr, (bx0 + 630, by0 + 130))
        tx = bx0 + 630 + qr.width + 25
        d.text((tx, by0 + 135), "Metin:", fill=(110, 120, 135), font=f_small)
        d.text((tx, by0 + 155), s["qr_text"], fill=(20, 25, 35), font=f_mono)
        d.text((tx, by0 + 195), "Standart:", fill=(110, 120, 135), font=f_small)
        d.text((tx, by0 + 215), "ISO/IEC 18004", fill=(50, 60, 75), font=f_body)

        if s.get("fold_line"):
            # Katlama çizgisi (sayfayı dikey kesen kırmızı kesikli çizgi)
            fx = bx0 + int((bx1 - bx0) / 2)
            d.line([fx, by0 + 80, fx, by1 - 10], fill=(220, 50, 50), width=2)
            d.text((fx - 45, by1 - 32), "KATLAMA ÇİZGİSİ", fill=(220, 50, 50), font=f_small)

    # Bölge 4: Gerçekçi Depo Koli Sevkiyat Etiketi (GS1 Shipping Label Mockup)
    d.rectangle([45, 1210, w - 45, 1530], fill=(253, 254, 255), outline=(195, 205, 218), width=2)
    d.rectangle([45, 1210, w - 45, 1246], fill=(242, 246, 252), outline=(205, 215, 228))
    d.rectangle([45, 1210, 51, 1246], fill=(50, 130, 210))
    d.text((60, 1218), "BÖLGE 4: GERÇEK DEPO KOLİ SEVKİYAT ETİKETİ (GS1 / SSCC ÖRNEĞİ)", fill=(30, 45, 70), font=f_head)

    # Koli etiketi içeriği: Ürün barkodu, Seri no, Sevkiyat SSCC barkodu
    bc_sscc = _make_barcode("(00)386901234500001234", fmt=zxingcpp.BarcodeFormat.Code128, scale=2)
    canvas.paste(bc_sscc, (70, 1270))
    d.text((70, 1270 + bc_sscc.height + 6), "SSCC Koli Kimliği: (00) 3869012345 0000123 4", fill=(30, 40, 50), font=f_mono)

    bc_ean = _make_barcode("8690999888776", fmt=zxingcpp.BarcodeFormat.EAN13, scale=2)
    canvas.paste(bc_ean, (680, 1270))
    d.text((680, 1270 + bc_ean.height + 6), "EAN-13 Ürün Kodu: 8690999888776", fill=(30, 40, 50), font=f_mono)

    qr_wms = _make_qr("WMS-LOC:K1-R02-L3-P01", ec="M", scale=4)
    canvas.paste(qr_wms, (1030, 1270))
    d.text((1000, 1270 + qr_wms.height + 6), "Raf Konum QR", fill=(30, 40, 50), font=f_small)

    d.text(
        (70, 1490),
        "Tipik depo etiketinde koli takip barkodu (Code 128), ürün kodu (EAN-13) ve raf QR kodu birlikte bulunur.",
        fill=(90, 100, 115),
        font=f_body,
    )

    # Alt Bilgi
    d.rectangle([45, 1550, w - 45, 1715], fill=(245, 248, 252), outline=(190, 200, 215), width=1)
    d.text((65, 1565), "NASIL TEST EDECEKSİNİZ?", fill=(20, 35, 60), font=f_head)
    steps = [
        "1. Bu sayfayı A4 kağıda yazdırın.",
        "2. Bölge 1'e koli bandı çekin; Bölge 2'yi katlayıp ezin; Bölge 3'e kalemle çizik atın.",
        "3. Telefonunuzla veya Jetson kamerasıyla fotoğrafını çekin.",
        "4. Web arayüzünde (http://10.92.90.64:8000/decode) Okuma Testi sayfasına yükleyin.",
    ]
    y_step = 1595
    for s in steps:
        d.text((65, y_step), s, fill=(50, 60, 75), font=f_body)
        y_step += 25

    return canvas


def save_test_sheet(output_path: str | Path, fmt: str = "PNG") -> Path:
    p = Path(output_path)
    canvas = generate_test_sheet()
    if p.suffix.lower() == ".pdf" or fmt.upper() == "PDF":
        canvas.save(p, "PDF", resolution=150.0)
    else:
        canvas.save(p, "PNG")
    return p
