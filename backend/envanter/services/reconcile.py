"""Envanter mutabakatı: bir gözde okunan kodları beklenen stokla karşılaştırır.

Temel ilke (brifing §1): sistem emin olmadığı sonucu kesin stok kaydı gibi yazmaz.
Şüpheli her durum ya UNREADABLE ya da CONFLICT olur ve inceleme kuyruğuna düşer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ObservationStatus, ReviewStatus


@dataclass
class Verdict:
    status: ObservationStatus
    reason: str
    missing: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)

    @property
    def review(self) -> ReviewStatus:
        needs = self.status in (ObservationStatus.CONFLICT, ObservationStatus.UNREADABLE)
        return ReviewStatus.PENDING if needs else ReviewStatus.NONE


def reconcile(
    codes: set[str],
    expected: set[str] | None,
    box_count: int | None = None,
) -> Verdict:
    """
    codes:     bu taramada gözde okunan benzersiz kodlar
    expected:  gözde olması beklenen kodlar; None → bu göz için stok bilgisi yok
    box_count: görünen koli sayısı; None → bilinmiyor (henüz koli tespit modeli yok)
    """
    if expected is None:
        if codes:
            if box_count is not None and box_count > len(codes):
                return Verdict(
                    ObservationStatus.UNREADABLE,
                    f"{box_count} koli görüldü, {len(codes)} kimlik okundu",
                )
            return Verdict(ObservationStatus.OBSERVED, "Okundu; bu göz için beklenen stok yok")
        if box_count == 0:
            return Verdict(ObservationStatus.EMPTY, "Göz boş")
        return Verdict(ObservationStatus.UNREADABLE, "Kimlik okunamadı")

    missing = sorted(expected - codes)
    unexpected = sorted(codes - expected)

    if unexpected:
        return Verdict(
            ObservationStatus.CONFLICT,
            "Beklenmeyen kod" + (" ve eksik koli" if missing else ""),
            missing,
            unexpected,
        )

    if not codes:
        if box_count == 0:
            if expected:
                return Verdict(ObservationStatus.CONFLICT, "Göz boş, koli bekleniyordu", missing)
            return Verdict(ObservationStatus.EMPTY, "Göz boş (beklenen)")
        if not expected and box_count is None:
            # Kod yok, beklenen de yok, koli sayısı bilinmiyor: boş olduğuna kesin diyemeyiz.
            return Verdict(ObservationStatus.UNREADABLE, "Kod bulunamadı; boşluk doğrulanamadı")
        return Verdict(ObservationStatus.UNREADABLE, "Kimlik okunamadı", missing)

    if missing:
        if box_count is not None and box_count <= len(codes):
            return Verdict(ObservationStatus.CONFLICT, "Beklenen koli eksik", missing)
        return Verdict(
            ObservationStatus.UNREADABLE,
            "Bazı koliler okunamadı veya eksik",
            missing,
        )

    if box_count is not None and box_count > len(codes):
        return Verdict(
            ObservationStatus.CONFLICT,
            f"{box_count} koli görüldü, {len(codes)} beklenen kod var",
        )
    return Verdict(ObservationStatus.VERIFIED, "Beklenen stokla birebir eşleşti")
