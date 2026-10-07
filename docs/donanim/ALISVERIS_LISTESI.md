# Alışveriş listesi — 3 m teleskopik direk

> Güncelleme: 2026-10-07. Motor, sürücü ve ip netleşti. Fiyatlar arama sırasında görülen değerlerdir; değişmiş olabilir, almadan önce bakın.
> Teknik ayrıntılar: [`MALZEME_LISTESI.md`](MALZEME_LISTESI.md), [`../../mekanik/direk_3m/README.md`](../../mekanik/direk_3m/README.md).

```
1) ALÜMİNYUM KARE PROFİL BORU (her birinden 1 m; kesimi biz yaparız)
- 60 x 60 x 2 mm ................. 1 m
- 45 x 45 x 2 mm ................. 1 m   (yoksa: dış ölçü 44–46 mm olan)
- 30 x 30 x 2 mm ................. 1 m
- 15 x 15 x 1–2 mm ............... 1 m

2) HIRDAVAT
- M3 ısıyla gömülen somun (heat-set insert), ~4 mm boy ... 50 adet
- M3 x 10 yuvarlak başlı cıvata (ISO 7380) .............. 40 adet
- M3 x 16 cıvata ........................................ 6 adet
- M3 x 25 cıvata ........................................ 2 adet
- M3 somun .............................................. 20 adet
- M4 x 70 cıvata + somun ................................ 2 adet
- M5 x 20 cıvata + somun + pul ........................... 4 adet (robot plakasına göre boy değişebilir)
- 623ZZ rulman (3x10x4 mm) ............................... 6 adet (2 yedek)

3) HALAT (İP)
- Dyneema ip, 1,2 mm, ≥16 m .............................. 1 adet
    Örnek: Gırcala Dyneema 1,2 mm 16 m "esnemez Optimist yelken ipi"
    (yelkenmarketi.com, ~700 TL görüldü)
    Yedek seçenek: Apnea Dyneema 1,50 mm 50 m zıpkın ipi (Teknosa, ~730 TL görüldü)
    ! Kalınlık 1,0–1,5 mm arası olmalı. 1,5 mm'den kalın makara oluğuna girmez.
    ! Balıkçı misinasında "PE 1.0" yazıyorsa bu 1 mm DEMEK DEĞİL (~0,17 mm).
      Etikette "mm" yazana bakın.
    ! Naylon misina, pamuk/polyester ip, çelik halat ALMAYIN.

4) MOTOR VE KONTROL
- Sonsuz vidalı redüktörlü DC motor, ENKODERLİ ............ 1 adet
    Model: 5840-31ZY enkoderli (5840-31ZY-EN), 12 V, 40 RPM
    - Kendini kilitler, metal dişli, Hall enkoder (2 kanal)
    - Tork: ~32 kg·cm anma / ~70 kg·cm kilitlenme (ihtiyaç ≥6)
    - Mil 8 mm D → motor tamburu bu mile göre yeniden çizilecek
    Nereden: Türkiye'deki robotik mağazalarında enkoderli olanı stokta yok.
      a) Amazon.com.tr: "sonsuz dişli redüktör motoru enkoderli kendinden kilitlemeli"
         diye aratın. Başlıkta 5840-31ZY, gövde ~58x40 mm, mil 8 mm ve 40 RPM olsun.
      b) AliExpress: "5840-31ZY encoder 12V 40rpm" (kargo ~2–3 hafta).
    Hemen lazımsa (enkodersiz, yerli):
      KWL-31ZY 12V 30 RPM, keskinlerelektronik.com, ~2.400 TL
      (12 kg·cm, şu an stokta yok) + AS5600 enkoder modülü
- Motor sürücü: BTS7960B 43 A ............................. 1 adet
    (robolinkmarket, robotsepeti, robo90, direnc.net'te var)
    ! DRV8871 bu motor için zayıf, ALMAYIN.
- Arduino Nano (veya Uno) + USB kablosu ................... 1 adet
- Mikro switch (makaralı limit anahtarı) .................. 3 adet
- IMU eğim sensörü (MPU-6050) ............................. 1 adet
- Acil durdurma butonu (mantar tipi, NC) .................. 1 adet
- VL53L1X lazer mesafe sensörü ............................ 1 adet (isteğe bağlı; yüksekliği doğrular)

5) GÜÇ VE KABLOLAMA
- 12 V 5 A adaptör (masa testi için) ...................... 1 adet
- Sigorta yuvası + 5 A sigorta ............................ 1 + 2 adet
- Motor hattı için 3 A gecikmeli (yavaş) sigorta + yuva ... 1 + 2 adet
- On/off anahtar .......................................... 1 adet
- Jumper kablo seti + 18 AWG güç kablosu + makaron ......... 1 set
- XT30 veya XT60 konnektör çifti .......................... 2 çift

6) ALET / SARF (yoksa)
- Havya için ısıl somun (insert) uçları ................... 1 set
- Matkap ucu: 3,5 mm, 4,5 mm, 5,5 mm ...................... 1'er
- Çapak alma aleti (eğe de olur) .......................... 1 adet
- Kuru PTFE veya silikon sprey (gres DEĞİL) ............... 1 adet
- Keskin makas (Dyneema normal makasla zor kesilir) ........ 1 adet

7) DAHA SONRA ALINACAKLAR (karar verilince)
- USB kamera, ≥8 MP ....................................... 4 adet  (model seçilecek)
- Harici beslemeli USB 3.0 hub, ≥4 port ................... 1 adet
- Spiral (yaylı) USB kablo ................................ 3 adet
- 12 V beyaz LED şerit + difüzörlü profil + MOSFET modülü .. 1 set
- Robot bataryasından 12 V'a DC-DC dönüştürücü ............ 1 adet (batarya gerilimine göre)
- PETG filament 1 kg (yakaları güçlendirmek için) .......... 1 adet
- POM (Delrin) levha 3 mm, ~100 x 100 mm (pabuç aşınırsa) .. 1 adet
```

## Neden bu seçimler

- **Motor:** Sonsuz vida kendini kilitler, yani elektrik kesilince direk düşmez. Enkoder olunca direğin kaç mm açıldığını ayrıca sensör eklemeden biliriz. Pololu gibi düz dişli motorlar kendini kilitlemediği için uygun değil.
- **Sürücü:** 5840 sıkıştığında ~6,5 A çeker. BTS7960 bunu rahat kaldırır. Ayrıca akım çıkışı (R_IS/L_IS) var; Arduino bununla takılmayı anlayıp motoru durdurur.
- **3 A sigorta:** Bir şey takılırsa güçlü motor basılmış parçaları kırabilir. Sigorta, limit anahtarı ve yazılımdaki akım/süre sınırı bunu önler.
- **Dyneema:** Neredeyse hiç esnemez; kamera aralıkları kaymaz. 1,2 mm bile bizim ~6 kg yükün çok üstünde dayanır.

## İp nasıl bağlanır

- Halatı parçadaki Ø2 delikten **tek kat** geçirin, arka tarafta **çift sekiz (stopper) düğümü** atın. Düğüm deliğe dayanır, kaçamaz.
- Tambura bağlamadan önce halatı **3–4 tur sarın**; yükü sürtünme taşır.
- İlk montajdan sonra direği birkaç kez açıp kapatın, sonra gerginliği yeniden ayarlayın.
