# Yazılım: envanter sunucusu ve dijital ikiz arayüzü

Bu belge `backend/` (Python, FastAPI) ve `web/` (React, three.js) klasörlerindeki yazılımın nasıl çalıştığını, nasıl çalıştırılacağını ve robotun sunucuyla nasıl konuşacağını anlatır.

## Mimari

```text
 Robot tarafı (Jetson üzerinde, ileride)          Sunucu (Jetson üzerinde)                  Tarayıcı (laptop/tablet/telefon)
 ┌──────────────────────────┐   HTTP POST    ┌──────────────────────────────┐   WebSocket   ┌──────────────────────────┐
 │ kamera yakalama          │ ─────────────▶ │ /api/scans/{id}/captures      │ ────────────▶ │ 3B dijital ikiz          │
 │ dikey eksen kontrolcüsü  │                │   → zxing-cpp ile kod çözme   │   canlı olay  │ inceleme kuyruğu         │
 │ LiDAR + konum (SLAM)     │ ─────────────▶ │   → mutabakat (beklenen stok) │               │ taramalar, okuma testi   │
 └──────────────────────────┘ /api/robot/... │ /api/robot/telemetry          │ ◀──────────── │                          │
                                             │   → voksel haritası           │   REST        └──────────────────────────┘
                                             │ SQLite (WAL) + görüntü klasörü│
                                             └──────────────────────────────┘
```

- **3B çizim tarayıcıda yapılır.** Jetson yalnızca derlenmiş dosyaları ve veriyi sunar, yani GPU'su AI modeline kalır.
- **Kod okuma** (`services/decoder.py`), yol haritasındaki karşılaştırma yöntemlerine göre işaretlenir:
  - **B0:** tam görüntü.
  - **B1:** klasik ön işleme yedeği.
  - **A1:** AI tespit modelinin kırptığı bölge. `crop` parametresiyle aynı çözücüyü kullanır.

  Her okuma hangi yöntemle bulunduğunu kaydeder.
- **Mutabakat** (`services/reconcile.py`): Bir gözde okunan kodlar, beklenen stokla (WMS'ten CSV) ve görünen koli sayısıyla karşılaştırılır. Emin olunmayan her sonuç "okunamadı" ya da "çelişki" olur ve inceleme kuyruğuna düşer.

### Göz durumları

| Durum | Anlamı | 3B'de |
|---|---|---|
| Doğrulandı | Okunan kodlar beklenenle birebir aynı | Kraft koli, yeşil etiket |
| Çelişki | Beklenmeyen kod var ya da beklenen koli yok | Yerinde olmayan koli kırmızı yanıp sönen "hayalet"; yanlış koli kırmızı |
| Okunamadı | Koli görünüyor ama kimliği okunamadı | Sarı koli |
| Boş | Göz boş ve boş olması bekleniyordu | Zeminde gri işaret |
| Stok bilgisi yok | Kod okundu ama bu göz için beklenen stok tanımlı değil | Mavi etiketli koli |
| Taranmadı | Henüz bu gözün sonucu yok | Soluk, yarı saydam koli |

"Görünen koli sayısı" (`box_count`), eksik koliyle okunamayan koliyi birbirinden ayırır. Bu değer ileride koli tespit modülünden (yol haritası H, üçüncü modül adayı) veya derinlik verisinden gelecek. Demo bu değeri simülasyondan alır. Değer gönderilmezse sistem temkinli davranır ve "okunamadı" der.

## Çalıştırma (geliştirme)

İlk kurulum, her makinede bir kez:

```bash
cd backend && python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

```bash
cd web && npm install
```

Arayüzü derleyin (dosyalar `web/dist` altına çıkar ve sunucu bunları kendisi sunar):

```bash
cd web && npm run build
```

Sunucuyu başlatın, sonra tarayıcıda http://localhost:8000 adresini açın:

```bash
cd backend && .venv/bin/envanter serve --port 8000
```

İlk açılışta veritabanı boşsa sistem bir **demo deposu** oluşturur. Üstteki "Demo taramayı başlat" düğmesi sanal robotu çalıştırır:
- Sanal LiDAR duvarları, klimayı, kolonu ve panoları haritalar.
- Sentetik kamera görüntüleri **gerçek kod çözücüden** geçer.
- Senaryoda bilinçli olarak 2 kayıp koli, 2 hasarlı etiket, 1 yanlış yere konmuş koli ve 1 kayıt dışı koli bulunur.
- Tarama bitince sistemin bunların kaçını yakaladığı gösterilir.

Arayüz üzerinde çalışırken anlık yenileme için `npm run dev` kullanın (http://localhost:5173, API'yi :8000'e yönlendirir).

Testler ve kod denetimi:

```bash
cd backend && .venv/bin/python -m pytest -q && .venv/bin/ruff check envanter tests
```

```bash
cd web && npm run typecheck
```

### macOS + iCloud uyarısı

Masaüstü/Belgeler iCloud'a senkronize ediliyorsa ve diskte yer azsa, macOS dosyaları buluta boşaltır. Python ve Node bu dosyaları okurken dakikalarca takılabilir. Çözümler:

- **En iyisi:** projeyi iCloud dışında bir klasörde tutmak (ör. `~/Projeler/bitirme`).
- **Proje Masaüstünde kalacaksa:** `.venv` ve `node_modules` klasörlerini sonu `.nosync` ile biten bir klasöre koyup sembolik bağ vermek. iCloud bu klasörlere dokunmaz.

```bash
cd backend && python3.11 -m venv .venv.nosync && ln -s .venv.nosync .venv
```

## Jetson'a kurulum

1. Depoyu Jetson'a alın (`docs/jetson/KURULUM.md` §6).
2. Arka ucu kurun:

   ```bash
   cd ~/bitirme/backend && python3 -m venv .venv && .venv/bin/pip install -e .
   ```

3. Arayüzü Mac'te derleyip `web/dist` klasörünü Jetson'a kopyalayın (Jetson'a Node kurmaya gerek yok):

   ```bash
   rsync -av web/dist/ envanter@depo-jetson.local:~/bitirme/web/dist/
   ```

4. Görüntüler ve veritabanı için `/data/envanter` kullanın, servisi açılışta başlatın:

   ```bash
   sudo mkdir -p /data/envanter && sudo chown envanter /data/envanter
   ```

   ```bash
   sudo cp jetson/envanter.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now envanter
   ```

5. Aynı ağdaki herhangi bir cihazdan `http://depo-jetson.local:8000` adresini açın.

## Robotun sunucuyla konuşması

Etkileşimli API belgesi sunucu çalışırken `http://<sunucu>:8000/docs` adresindedir. Robot tarafının kullanacağı üç uç şunlar.

**1. Tarama başlat**

```http
POST /api/scans
{"warehouse_id": 1, "mode": "robot", "note": "A koridoru gece sayımı"}
```

Yanıttaki `id`, sonraki çağrıların tarama kimliğidir.

**2. Her çekimde görüntü gönder** (multipart form)

```text
POST /api/scans/{scan_id}/captures
  image                 JPEG/PNG dosyası (özgün çözünürlük; kanıt olarak saklanır)
  location_code         ör. A01-2-3  (raf-seviye-pozisyon)
  camera_id             ör. cam1
  vertical_position_mm  mast yüksekliği
  box_count             (isteğe bağlı) görünen koli sayısı
```

Yanıt, okunan kodları (köşe koordinatlarıyla) ve gözün güncel durumunu döndürür. Aynı göz için birden fazla kamera veya çekim gönderilebilir; kodlar birleştirilir.

Bitince `POST /api/scans/{scan_id}/finish` çağrılır. Sonuç `GET /api/scans/{scan_id}/export.csv` ile Excel'e alınır.

**3. Konum ve LiDAR** (5–10 Hz önerilir)

```http
POST /api/robot/telemetry
{
  "warehouse_id": 1,
  "pose": {"x": 5.2, "y": 7.5, "yaw": 0.0},
  "mast_mm": 750,
  "state": "moving",
  "points": [[1.2, 0.4, 0.6], ...]
}
```

- `pose`: depo ekseninde metre ve radyan cinsinden konum. Bu konum ileride bir SLAM düğümünden gelecek; LiDAR tek başına konum vermez.
- `points`: robot ekseninde (x ileri, y sol, z yukarı) 3B LiDAR noktaları.
- 2B LiDAR için `points` yerine `scan2d` gönderilebilir (`angle_min`, `angle_increment`, `ranges`; ROS `LaserScan` ile aynı alanlar). 2B LiDAR yalnız kendi yüksekliğindeki dilimi görür. Duvardaki klima gibi yüksekteki çıkıntılar için 3B LiDAR veya derinlik kamerası gerekir.

**Beklenen stok** (WMS dışa aktarımı):

```http
POST /api/stock/import?warehouse_id=1   (multipart: file=stok.csv)
```

CSV başlıkları `location_code;code;quantity;description` şeklindedir. Ayraç `;` ya da `,` olabilir.

**Depo düzeni:** `POST /api/warehouses` ve `POST /api/racks` uçları, raf konumu (`x`, `y`, `yaw_deg`), göz sayıları ve ölçüleriyle raf ekler. Gözler `RAF-SEVİYE-POZİSYON` biçiminde kendiliğinden oluşur.

## Bilinen sınırlar

- Kimlik doğrulama yok. Sunucu yalnız güvenilen yerel ağda açılmalı.
- B1 ön işlemesi sentetik görüntülerde ölçülebilir katkı göstermedi; parametreleri gerçek kamera verisiyle ayarlanmalı.
- Demo sahnesinde raflar LiDAR için dolu kutu kabul ediliyor; gerçek raflar açık çerçevedir.
