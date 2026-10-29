#!/usr/bin/env python3
"""Güç butonuna kısa basınca Jetson'ı sormadan, düzgünce kapatır.

Neden gerekli: GNOME (gsd-media-keys) güç tuşu için logind'e engelleme kilidi koyar.
Kilit dururken logind.conf'taki HandlePowerKey ayarı işlemez; GNOME'un kendi ayarında da
Ubuntu 22.04'te "kapat" seçeneği yok. Bu betik tuşu doğrudan giriş aygıtından (gpio-keys)
okur ve `systemctl poweroff` çağırır; masaüstü açık olsun olmasın çalışır.

Kullanım (root gerekir; /dev/input/event* yalnız root ve input grubuna açık):
  sudo python3 jetson/scripts/guc_tusu.py --deneme   # kapatmaz, basışları yazar
  sudo python3 jetson/scripts/guc_tusu.py            # basınca kapatır (servis bunu çalıştırır)

Servis olarak kurulum: jetson/depogoz-guc-tusu.service dosyasının başına bakın.
"""

from __future__ import annotations

import argparse
import struct
import subprocess
import sys
from pathlib import Path

AYGIT_ADI = "gpio-keys"  # Orin Nano geliştirme kartında güç butonu bu aygıttan gelir
EV_KEY = 1
KEY_POWER = 116
BASILDI = 1
# struct input_event: timeval (2 × long) + type (u16) + code (u16) + value (s32)
OLAY = struct.Struct("llHHi")


def aygit_bul(ad: str = AYGIT_ADI) -> Path:
    for isim in sorted(Path("/sys/class/input").glob("event*/device/name")):
        if isim.read_text().strip() == ad:
            return Path("/dev/input") / isim.parent.parent.name
    raise FileNotFoundError(f"'{ad}' giriş aygıtı bulunamadı (/proc/bus/input/devices)")


def basislari_bekle(aygit: Path):
    """Güç tuşuna her basışta bir kez döner (bırakma ve tekrar olayları atlanır)."""
    with aygit.open("rb", buffering=0) as f:
        while True:
            veri = f.read(OLAY.size)
            if len(veri) < OLAY.size:
                return
            _, _, tip, kod, deger = OLAY.unpack(veri)
            if tip == EV_KEY and kod == KEY_POWER and deger == BASILDI:
                yield


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--deneme", action="store_true", help="kapatma; yalnız basışları yaz")
    p.add_argument("--aygit", type=Path, help="giriş aygıtı (varsayılan: gpio-keys bulunur)")
    args = p.parse_args()

    aygit = args.aygit or aygit_bul()
    print(f"Güç butonu dinleniyor: {aygit}", flush=True)
    for _ in basislari_bekle(aygit):
        if args.deneme:
            print("Güç butonuna basıldı (deneme: kapatılmıyor)", flush=True)
            continue
        print("Güç butonuna basıldı: sistem kapatılıyor", flush=True)
        return subprocess.call(["systemctl", "poweroff"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
