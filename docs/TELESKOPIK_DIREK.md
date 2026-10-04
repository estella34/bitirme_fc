# Dört kameralı eş zamanlı teleskopik direk — kurulum rehberi (1:2 prototip)

Hedef ürün: kapalıyken ~2 m, açıkken 5–6 m; her borunun tepesinde bir kamera; kameralar arası mesafe her açıklıkta eşit. Bu belge aynı mekanizmanın **yarı ölçekli prototipini** anlatır: kapalı ~1 m, açık ~2,9 m. Ölçüler başlangıç önerisidir; piyasada bulunan profillere göre ayarlanır.

## Çalışma ilkesi

Tek motor yalnız 1. boruyu kaldırır. Diğer borular, boyu hiç değişmeyen "kademe halatları" ile otomatik olarak 2 ve 3 kat yükselir (forklift direği ilkesi). 1. boru `x` yükselince 2. boru `2x`, 3. boru `3x` yükselir; tepelerindeki kameralar arası hep `x`'tir.

| Halat | Sabit ucu | Geçtiği makara | Bağlandığı yer | Sonuç |
|---|---|---|---|---|
| Motor halatı | Gövdedeki vinç makarası (sarılır) | Taban borusu yakası | 1. borunun ayağı | 1. boru `x` |
| A halatı | Taban borusu yakası | 1. boru yakası | 2. borunun ayağı | 2. boru `2x` |
| B halatı | 1. boru yakası | 2. boru yakası | 3. borunun ayağı | 3. boru `3x` |

Halatlar borular arasındaki boşlukta, kayar pabuçların olmadığı yüzlerde iner. Makaralar yakaların üstünde, borunun dışındadır.

## Parça listesi

| Parça | Öneri | Adet | Not |
|---|---|---|---|
| Kare alüminyum boru | 60×60×2, 45×45×2, 30×30×2, 15×15×1,5 mm; her biri 800 mm | 4 | Kural: iç içe borular arasında her yandan ~5 mm boşluk kalsın (pabuç + halat payı) |
| Kayar pabuç | 5 mm POM/Delrin şerit (ilk deneme PETG baskı) | 12–16 | Dış borunun ağzına içten, iç borunun ayağına dıştan; karşılıklı iki yüzde |
| Yaka (borunun tepesi) | PETG 3B baskı | 4 | Makara mili, halat bağlantı vidası, kamera tutucusu, ağız pabuçları |
| Ayak (hareketli boruların dibi) | PETG 3B baskı | 3 | Dış pabuçlar, halat bağlama halkası, **dayanma çıkıntısı** (tam açılınca dış borunun yakasına takılır, boru çıkıp düşmez) |
| Makara | 623/624 rulman veya küçük V makara | 3 | Taban yakası, 1. boru yakası, 2. boru yakası |
| Halat | 1–1,5 mm Dyneema (veya çelik halat) | ~6 m | Bağlantı uçlarında germe vidası |
| Tahrik | 12 V sonsuz vidalı redüktörlü DC motor, enkoderli, 30–60 dev/dk | 1 | Sonsuz vida kendini kilitler: elektrik kesilince direk düşmez |
| Vinç makarası | Ø20 mm, motor miline | 1 | |
| Motor sürücü | Örn. DRV8871 / BTS7960 sınıfı | 1 | Arduino'dan PWM + yön |
| Limit anahtarı | Alt (kapalı) + üst (tam açık) | 2 | Mekanik dayanmalardan bağımsız |
| Mesafe sensörü (isteğe bağlı) | VL53L1X, en üst yakada aşağı bakar | 1 | Gerçek yüksekliği doğrular |
| Kamera | USB kamera, her yakada bir | 4 | Hepsi rafa doğru aynı yöne bakar |
| Kablo | Spiral (yaylı) USB kablo, hareketli 3 kamera için | 3 | Gövdedeki USB hub'a iner |

**Kaba yük hesabı:** Hareketli kütle ~2 kg (borular + yakalar + kameralar). Kaskat oranları yüzünden motor halatındaki kuvvet ≈ g·(m₁ + 2m₂ + 3m₃) ≈ 30 N; sürtünmeyle ~50 N tasarlanmalı. Ø20 mm makarada ~0,5 N·m tork: küçük bir sonsuz vidalı motor yeter. 40 dev/dk'da 1. boru ~4 cm/s, tepe kamera ~12 cm/s hızla yükselir.

**Ölçüler (prototip):** Boru boyu 800 mm, iç içe kalan kısım en az 180 mm → her kademe en fazla ~620 mm açılır. Taban borusu gövdenin 200 mm üstünde başlarsa: kapalı tepe ~1,0 m, açık tepe ~2,9 m. Kameralar arası 0 → 620 mm.

## Kurulum sırası

Her adım bir öncekinin çalıştığını kanıtlamalı; sorun varsa bir sonrakine geçme.

1. **Kesim ve hazırlık:** Boruları kes, çapaklarını al. Her boruda iki yüzü "pabuç yüzü", diğer ikisini "halat yüzü" olarak işaretle.
2. **Baskı parçaları:** Yakaları ve ayakları bas. Ayaklardaki dayanma çıkıntısını unutma.
3. **Kuru montaj:** Halatsız, boruları iç içe geçirip elle kaydır. Pabuç kalınlığını, takılmadan kayacak ama sallanmayacak şekilde ayarla. En çok deneme bu adımda.
4. **İki boru + motor:** Taban + 1. boru, vinç ve motor halatı. Kaldır-indir; takılma ve boşluk kontrolü.
5. **A halatı + 2. boru:** 1. boru 10 cm çıkınca 2. borunun 20 cm çıktığını ölç. Fark varsa halat gerginliğini ayarla.
6. **B halatı + 3. boru:** 10 / 20 / 30 cm oranını ölç. Tam açıkken tepenin ne kadar sallandığına bak.
7. **Sınırlar:** Alt ve üst limit anahtarları; mekanik dayanmaların limitlerden önce değil sonra devreye girdiğini kontrol et.
8. **Kameralar ve kablolar:** Yakalara kameraları, hareketli olanlara spiral kabloları tak. Tam strokta 20 kez aç-kapa; kablo takılıyor mu?
9. **Ölçüm:** Durduktan kaç saniye sonra fotoğraf net? Aynı yüksekliğe tekrar gelince kaç mm sapma var? Elektrik kesilince direk duruyor mu?
10. **Robota montaj:** Direk tam açıkken robotu hafifçe it; devrilme eğilimi var mı? Gerekirse taban genişlet / ağırlığı aşağı al. Robot yalnız direk kapalıyken hareket etsin.

## Yazılım tarafı

- Kontrolcü (Arduino): `HOME` (alt limite in, enkoderi sıfırla), `MOVE <x_mm>` (1. borunun açıklığı), `STOP`; yanıtlar `AT_POSITION`, `LIMIT`, `ERROR`.
- Jetson kamera yüksekliklerini hesaplar: `h_k = h_0 + k·(x + kademe payı)`, k = 0…3. DepoGöz her fotoğrafı bu yüksekliğe göre raf gözüne eşler.
- Kameralar arası mesafe = `x`; raf seviye aralığına göre seçilir (her kamera bir seviyeye baksın) veya görüş alanları birbirine değecek şekilde ayarlanır.

## Açık konular

- Koridor genişliği / kamera–raf uzaklığı → kameranın gördüğü yükseklik → ideal `x`.
- En alt seviye: taban kamerası ~1 m'de; zemine yakın etiketler için aşağı eğik kamera veya gövdede ek kamera.
- İki taraflı raf: her yakada iki kamera (sol/sağ) mı, yoksa koridorda iki geçiş mi?
