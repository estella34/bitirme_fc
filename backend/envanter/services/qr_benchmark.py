"""Depo QR kodlarının zorlu koşullardaki okuma başarımını ölçen benchmark modülü.

Farklı hata düzeltme seviyelerinde (L, M, Q, H) ve farklı bozulma tiplerinde
(bulanıklık, koli bandı parlaması, çizikler, katlanma, solma) çözücünün
hangi yöntemle (B0, B1, B2, B3) başarıya ulaştığını test eder.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import zxingcpp
from PIL import Image

from .decoder import decode_image
from .qr_degrade import apply_degradation


@dataclass
class BenchmarkResult:
    test_name: str
    ec_level: str
    degradation: str
    success: bool
    method_used: str | None
    methods_tried: list[str]
    elapsed_ms: float


def run_benchmark(sample_text: str = "KL-992104") -> list[BenchmarkResult]:
    ec_levels = ["L", "M", "Q", "H"]
    degradations = ["none", "blur", "motion_blur", "tape_glare", "scratches", "crease", "faded"]

    results: list[BenchmarkResult] = []

    for ec in ec_levels:
        # 160x160 civarı gerçekçi etiket ölçeği
        bc = zxingcpp.create_barcode(sample_text, zxingcpp.BarcodeFormat.QRCode, ec_level=ec)
        base_qr = Image.fromarray(np.asarray(bc.to_image(scale=6))).convert("RGB")

        for deg in degradations:
            test_img = base_qr.copy()
            if deg != "none":
                test_img = apply_degradation(test_img, deg)  # type: ignore

            t0 = time.perf_counter()
            outcome = decode_image(test_img, fallback=True, robust_fallback=True)
            elapsed = (time.perf_counter() - t0) * 1000

            success = any(c.text == sample_text for c in outcome.codes)
            method = outcome.codes[0].method if success else None

            results.append(
                BenchmarkResult(
                    test_name=f"{ec}_{deg}",
                    ec_level=ec,
                    degradation=deg,
                    success=success,
                    method_used=method,
                    methods_tried=outcome.methods_tried,
                    elapsed_ms=round(elapsed, 2),
                )
            )

    return results


def print_benchmark_table(results: list[BenchmarkResult]) -> None:
    print("\n" + "=" * 78)
    print(f"{'HATA DÜZELTME':<14} | {'BOZULMA TİPİ':<14} | {'DURUM':<8} | {'YÖNTEM':<10} | {'SÜRE (ms)':<10}")
    print("=" * 78)

    for r in results:
        status_str = "BAŞARILI" if r.success else "BAŞARISIZ"
        method_str = r.method_used or "-"
        print(
            f"Level {r.ec_level:<8} | {r.degradation:<14} | {status_str:<8} | {method_str:<10} | {r.elapsed_ms:<10.1f}"
        )
    print("=" * 78 + "\n")
