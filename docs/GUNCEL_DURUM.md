# DepoGöz: güncel durum (7 Ekim 2026)

Proje: rafları kamerayla tarayıp koli etiketlerini (QR/barkod) okuyan, eksik ya da yanlış koliyi 3B "dijital ikiz" üzerinde gösteren depo envanter robotu. Beyin Jetson Orin Nano; kameralar teleskopik bir direğin üzerinde.

## Kısaca nerede kaldık

| Parça | Durum |
|---|---|
| Jetson Orin Nano | ✅ Kuruldu: JetPack 6.2.1, Ubuntu 22.04, Jetson Linux 36.4.7 (firmware de 36.4.7) |
| 4 kamera (Arducam IMX519 16 MP, CamArray adaptörüyle) | ✅ Çalışıyor: canlı görüntü, odak motoru, otomatik odak, QR okuma |
| DepoGöz yazılımı (sunucu + web arayüzü) | ✅ Jetson'da servis olarak çalışıyor, açılışta kendiliğinden başlıyor |
| Kameraların arayüze bağlanması | ✅ Yeni **Kameralar** sekmesi: okunan kodlar dijital ikizde ilgili raf gözünü günceller |
| 3 m teleskopik direk (mekanik) | 🟡 Plastik parçalar tasarlandı ve çoğu basıldı; alüminyum borular, motor ve ip alınacak |
| Motor, sürücü, ip | 🟡 Seçildi, sipariş edilecek ([alışveriş listesi](donanim/ALISVERIS_LISTESI.md)) |
| Robot şasesi, LiDAR, hareket | ⬜ Henüz başlanmadı (arayüzde şimdilik simülasyon var) |

## Arayüzü açmak

Jetson ile aynı ağdaki herhangi bir bilgisayardan tarayıcıda:

**http://10.92.90.64:8000**

> IP adresi ağa göre değişebilir. Değişirse Jetson'da Terminal'de `hostname -I` yazıp yeni adresi alın.

Sekmeler:
- **Depo:** 3B dijital ikiz. Raf gözüne tıklayınca beklenen ve okunan kodlar görünür. "Demo taramayı başlat" robotu simüle eder.
- **Kameralar:** Dört kameranın canlı görüntüsü, **Otomatik odakla**, elle odak kaydırıcısı, **Çek ve oku**.
- **İnceleme / Taramalar / Okuma testi:** Sorunlu gözler, geçmiş taramalar (CSV olarak indirilebilir), telefondan fotoğraf yükleyip okuma denemesi.

**3B sahneye bilgisayardan bakın.** Jetson'daki tarayıcılar ekran kartını kullanamıyor; 3B sahne orada işlemciyle çiziliyor ve kasıyor. Kameralar sekmesi Jetson'da da sorunsuz.

### Kendin deneyebileceğin şey
1. **Depo** sekmesinde bir raf gözüne tıkla, beklenen kodlardan birini not al (ör. `KL-...`).
2. Telefonda herhangi bir QR üreticiyle bu kodu QR yap.
3. **Kameralar** sekmesinde telefonu bir kameraya 30–50 cm'den göster → **Otomatik odakla** → **Çek ve oku**.
4. Kod görüntüde yeşil çerçeveyle işaretlenir; Depo sekmesinde o göz yeşile döner.

## Kameralar nasıl bağlı

- 4 × Arducam IMX519 (16 MP, otomatik odaklı) → **CamArray adaptörü (UC-512)** → tek kabloyla Jetson'ın kamera girişine.
- Adaptör dört görüntüyü 2×2 tek karede birleştirir (kamera başına ~4 MP, saniyede ~9–17 kare).
- Adaptör, 40 pinli başlığın **1–6 numaralı pinlerine** oturur. Adaptördeki 3.3V yazısı Jetson'ın 1 numaralı pinine gelmeli.
- ⚠️ **Adaptör ile Jetson arasındaki kablonun yönü önemli.** Ters takılıyken kameralar "var" görünüyor ama görüntü gelmiyor. Şu anki yön doğru; çıkarırsan aynı yönde tak.
- En az 3 kamera takılı olmalı, yoksa adaptör görüntü göndermiyor.
- Odak motoru dört kamerada birlikte hareket eder (0 = yakın, 4095 = uzak).
- **Cheese gibi normal kamera programları bu kameraları açamaz.** Görüntü yalnız NVIDIA'nın kamera servisi üzerinden alınabiliyor. Bakmak için DepoGöz'ün Kameralar sekmesini ya da Jetson'da `./kamera_izle.sh` komutunu kullan. İkisi aynı anda çalışmaz, kamerayı tek program kullanabiliyor.

## Jetson'da dikkat edilecekler

- **Ubuntu'nun "Software Updater" penceresine güvenme.** Kamera sürücüsü NVIDIA çekirdeğinin yerine kuruldu. NVIDIA paketleri güncellemeye karşı kilitlendi ama yine de büyük güncellemeleri birlikte yapalım.
- **Sistem dili İngilizce bırakılmalı.** Türkçe dil ayarı ("İ/ı" sorunu yüzünden) kamera sürücüsünün kurulumunu bozmuştu. Klavye Türkçe Q, saat İstanbul.
- **Chromium:** Menüdeki kısayoldan açılmalı (özel ayarlarla açılıyor). Başka yoldan açılırsa 3B sahne "WebGL kullanılamıyor" der.
- **Kullanıcı:** `depogoz_fc`. Şifreyi ayrıca söylerim, buraya yazmıyorum.

## Donanım kararları (özet)

**Direk:** Teleskopik, 4 kademeli kare alüminyum boru (60 / 45 / 30 / 15 mm, ~90 cm boylar). Kapalıyken ~1 m, açıkken ~2,9 m. Halat-makara düzeniyle bütün kademeler birlikte açılıyor ve kameralar arası mesafe hep eşit kalıyor. Plastik parçalar (yakalar, kayar pabuçlar, makaralar, taban) Bambu A1'de PLA ile basılıyor. Ayrıntı: [mekanik/direk_3m/README.md](../mekanik/direk_3m/README.md)

**Motor:** 5840-31ZY enkoderli sonsuz vidalı motor, 12 V, 40 RPM. Kendini kilitliyor, yani elektrik gidince direk düşmüyor. **Sürücü:** BTS7960. **İp:** 1,2 mm Dyneema (esnemeyen ip). Tam liste: [donanim/ALISVERIS_LISTESI.md](donanim/ALISVERIS_LISTESI.md)

**Kamera görüşü:** Yaptığımız simülasyona göre rafa en iyi mesafe **0,8–1,1 m**, 30 mm'lik QR etiketlerle. Alt raflar için alt kamera ~25° aşağı, üst kamera ~15° yukarı eğilmeli. Robot hareket ederken okuyabilmesi için kısa pozlama ve LED aydınlatma gerekiyor.

## Sıradaki işler

1. QR'larla gerçek okuma testi (0,5 / 1 / 1,5 m mesafeden, farklı ışıkta).
2. Alüminyum boru, motor, ip ve sürücü siparişi. Motor gelince tambur ve motor braketi basılacak.
3. Direğin montajı, kayma ve halat ayarı.
4. Robot şasesi, LiDAR ve hareket. Simülasyonun yerine gerçek veri gelecek.
5. Yapay zekâ ile koli ve etiket bulma: Jetson'ın ekran kartı burada kullanılacak.

## Kod ve belgeler

Bütün proje tek git deposunda (Jetson'da `~/bitirme`):
- `backend/`: sunucu (Python, FastAPI); kod okuma, mutabakat, kamera
- `web/`: arayüz (React + three.js)
- `jetson/`: Jetson kurulum betikleri ve servis dosyası
- `mekanik/`: direk tasarımları (OpenSCAD) ve basılacak dosyalar
- `docs/`: kararlar, kurulum rehberi, malzeme listeleri
