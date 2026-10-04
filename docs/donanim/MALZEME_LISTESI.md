# Teleskopik direk — malzeme listesi (1:2 prototip)

Tasarım: [`../TELESKOPIK_DIREK.md`](../TELESKOPIK_DIREK.md). Kapalı ~1 m, açık ~2,9 m; 4 boru, 3 halat, 1 motor, 4 kamera. Fiyat yazılmadı; parça seçiminden önce stok ve fiyat kontrol edilmeli. Model adları **örnektir**; eşdeğeri olur.

## 1. Mekanik

| # | Parça | Özellik | Adet | Not / arama terimi |
|---|---|---|---|---|
| M1 | Kare alüminyum boru | 60×60×2 mm | 1 × 800 mm | "kare alüminyum profil boru" |
| M2 | Kare alüminyum boru | 45×45×2 mm | 1 × 800 mm | Bulunamazsa 40×40; o zaman alt/üst borular da ayarlanır (her yandan ~5 mm boşluk kuralı) |
| M3 | Kare alüminyum boru | 30×30×2 mm | 1 × 800 mm | |
| M4 | Kare alüminyum boru | 15×15×1,5 mm | 1 × 800 mm | |
| M5 | Kayar pabuç malzemesi | 5 mm POM (Delrin) levha, ~100×200 mm | 1 | İlk deneme için PETG baskı da olur |
| M6 | 3B baskı filament | PETG, 1 kg | 1 | Yakalar, ayaklar, vinç makarası, kamera tutucuları, kablo klipsleri |
| M7 | Rulman (makara için) | 623ZZ veya 624ZZ | 6 | 3 makara × 2 (biri yedek); ince pullarla |
| M8 | Halat | 1–1,5 mm Dyneema (örgü misina, ≥45 kg) | 10 m | Çelik halat da olur; o zaman sıkma yüksüğü gerekir |
| M9 | Germe vidası / ayar civatası | M4, küçük | 3 | Halat gerginliği ayarı |
| M10 | Taban montaj plakası | 4–5 mm alüminyum levha, ~200×200 mm | 1 | Direği robot şasesine bağlar; şasiye göre ölçülecek |
| M11 | Köşebent / destek | Alüminyum L köşebent | 4 | Taban borusunu plakaya dik bağlamak için |
| M12 | Lastik tampon | Ø10–15 mm | 4 | Alt dayanma, borular kapanırken çarpmasın |
| M13 | Civata takımı | M3, M4, M5 civata + somun + pul, karışık | 1 set | |
| M14 | Isıyla gömülen somun (insert) | M3 | 30 | Baskı parçalarına |
| M15 | Perçin somun (rivnut) veya kör perçin | M4 | 20 | Yakaları/ayakları ince cidarlı boruya bağlamak için |
| M16 | Kablo zinciri / klips | Küçük | 1 | Gövde içi kablo düzeni |

## 2. Tahrik ve hareket elektroniği

| # | Parça | Özellik | Adet | Not |
|---|---|---|---|---|
| E1 | Redüktörlü motor | 12 V, **sonsuz vidalı**, enkoderli, 30–60 dev/dk (ör. JGY-370 sınıfı) | 1 | Sonsuz vida kendini kilitler: elektrik kesilince direk düşmez. Tork ≥ 10 kg·cm |
| E2 | Vinç makarası | Ø20 mm, motor miline (D kesitli mil) | 1 | PETG baskı, kenarlıklı |
| E3 | Motor sürücü | DRV8871 sınıfı (≥2 A) | 1 | L298N da çalışır ama verimsiz/ısınır |
| E4 | Kontrol kartı | Arduino Nano veya Uno | 1 | Araç Arduino'sundan **ayrı** olması önerilir; Jetson'a USB ile bağlanır |
| E5 | Limit anahtarı | Mikro switch (makaralı) | 3 | Alt, üst + 1 yedek |
| E6 | Mesafe sensörü (isteğe bağlı) | VL53L1X ToF | 1 | En üst yakada aşağı bakar; gerçek yüksekliği doğrular |
| E7 | Eğim sensörü | IMU (MPU-6050 / BNO055) | 1 | Robot eğilirse direği otomatik kapatmak için |
| E8 | Acil durdurma butonu | Mantar tipi, NC kontak | 1 | Motor gücünü keser |

## 3. Kamera ve aydınlatma

| # | Parça | Özellik | Adet | Not |
|---|---|---|---|---|
| C1 | USB kamera | UVC, ≥8 MP (veya 4K), otomatik odak veya ~1 m'ye sabit odak | 4 | Barkod/QR için çözünürlük önemli; mümkünse global shutter |
| C2 | Spiral USB kablo | Yaylı, açıkken ≥2 m | 3 | Hareketli 3 kamera; taban kamerası düz kablo |
| C3 | USB hub | USB 3.0, **harici beslemeli**, ≥4 port | 1 | Gövdede; Jetson'a tek kablo |
| C4 | LED aydınlatma | 12 V beyaz LED şerit + difüzörlü profil, ~20 cm | 4 | Her yakada bir; kısa pozlama = net fotoğraf |
| C5 | LED anahtarlama | MOSFET modülü | 1 | Arduino LED'leri yalnız çekim anında yakar |

## 4. Güç ve kablolama

| # | Parça | Özellik | Adet | Not |
|---|---|---|---|---|
| P1 | 12 V kaynak (masa testi) | 12 V 5 A adaptör | 1 | Robot üstünde: batarya → DC-DC dönüştürücü |
| P2 | DC-DC dönüştürücü | Batarya → 12 V, ≥5 A | 1 | Robot bataryasının gerilimine göre seçilecek |
| P3 | Sigorta + yuva | 5 A bıçak sigorta | 2 | |
| P4 | Ana anahtar | Rocker switch | 1 | |
| P5 | Konnektör | XT30/XT60, JST-XH, klemens | 1 set | |
| P6 | Kablo | 18 AWG (güç), 24 AWG (sinyal), makaron | 1 set | |

## 5. Araç gereç (yoksa ödünç alınabilir)

Demir testeresi veya alüminyum kesme, matkap ve uçlar, eğe/çapak alıcı, M4–M5 kılavuz, kumpas, multimetre, havya, kablo soyucu/sıkıcı, 3B yazıcı.

## Sipariş öncesi kesinleşmesi gerekenler

1. Kamera modeli (C1): çözünürlük ve odak, koridor genişliğine göre seçilecek.
2. Robot bataryasının gerilimi (P2).
3. Şasinin ölçüsü ve direğin bağlanacağı yer (M10).
4. Boru ölçülerinin piyasada bulunup bulunmadığı (M1–M4).
