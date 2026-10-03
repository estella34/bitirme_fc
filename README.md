# Dikey kameralı depo envanter robotu

Lisans bitirme projesi. Depo raflarının önünde duran küçük bir robot, dikey olarak yükselen kamera platformuyla koli etiketlerini görüntüler. Bu görüntülerden raf gözü bazında envanter kaydı üretir: **tarama kimliği, raf/göz, görünen koli sayısı, okunan kimlik, görüntü kanıtı ve sonuç durumu**.

Projenin yapay zekâ katkısı, kendi depo görüntülerimizle fine-tune edilen bir barkod/etiket bölgesi tespit modeli ve okunamayan etiketler için OCR yedeğidir. Her AI modülü, klasik barkod çözücüden oluşan baseline ile aynı test kümesinde karşılaştırılır.

## Durum

| Aşama | Konu | Durum |
|---|---|---|
| A | Parçaları tanı | devam ediyor |
| B | Jetson kurulumu | **devam ediyor** — [kurulum rehberi](docs/jetson/KURULUM.md) |
| C | Tek kamera deneyi | bekliyor |
| D–E | Dikey mekanizma ve kontrolü | bekliyor |
| F | AI'sız okuma hattı (baseline) | bekliyor |
| G–H | Veri seti ve AI katmanı | bekliyor |
| I–J | Canlı demo ve araç entegrasyonu | bekliyor |

Aşamaların ayrıntısı: [docs/YOL_HARITASI.md](docs/YOL_HARITASI.md) · tıklanabilir sürüm: [docs/index.html](docs/index.html)

## Depo yapısı

```text
.
├── docs/
│   ├── PROJE_BRIFINGI.md       # projeye yeni katılan için tam bağlam
│   ├── YOL_HARITASI.md         # aşamalar, çıktılar, metrikler
│   ├── MEKANIZMA_TASLAGI.md    # dikey kamera mekanizması taslağı
│   ├── KARARLAR.md             # teknik karar kaydı
│   ├── index.html              # tıklanabilir yol haritası
│   ├── donanim/                # donanım envanteri ve fotoğraflar
│   ├── jetson/                 # Jetson kurulum rehberi
│   └── referans/               # referans görseller
└── jetson/
    ├── scripts/                # Jetson'da çalışan kurulum / kontrol betikleri
    └── kayitlar/               # Jetson'dan alınan sağlık kontrolü raporları
```

İleride eklenecek klasörler: `envanter/` (Python uygulaması: görüntü alma, barkod, AI, envanter), `firmware/` (dikey eksen kontrolcüsü), `mekanik/` (CAD ve çizimler).

## Donanım

- NVIDIA Jetson Orin Nano Developer Kit (görüntü alma, AI çıkarımı, envanter, arayüz)
- 4 kamera (model ve bağlantı yöntemi henüz belli değil)
- Arduino + motor sürücü (araç hareketi; mevcut)
- Dikey kamera mekanizması (sıfırdan yapılacak)

Ayrıntı: [docs/donanim/DONANIM_ENVANTERI.md](docs/donanim/DONANIM_ENVANTERI.md)

## Çalışma düzeni

- `main` her zaman çalışan, düzgün hâlde tutulur. Yeni iş kısa ömürlü bir dalda yapılır: `ozellik/kamera-yakalama`, `duzeltme/seri-zaman-asimi`, `belge/jetson-kurulum`.
- Commit mesajı biçimi `alan: ne yapıldı`. Örnekler: `jetson: sağlık kontrolü betiği`, `docs: mekanizma ölçüleri güncellendi`, `envanter: barkod çözücü baseline`.
- Verilen her teknik karar [docs/KARARLAR.md](docs/KARARLAR.md) dosyasına yazılır.
- Veri seti, ham görüntü, video ve model ağırlıkları git'e girmez (bkz. `.gitignore`).
