# DepoGöz: çalışma rehberi (ekip için)

> Son güncelleme: 29 Ekim 2026. Genel durum özeti: [GUNCEL_DURUM.md](GUNCEL_DURUM.md).
> Bu dosya, Jetson'a bağlanıp proje üzerinde çalışmak için gereken her şeyi anlatıyor.
> **Şifreler burada yok**; ayrıca söylenir.

## 1. Kısa özet

- **Depo:** https://github.com/estella34/bitirme_fc. Proje Jetson'da da `~/bitirme` klasöründe duruyor.
- **Jetson Orin Nano Super:**
  - Kullanıcı `depogoz_fc`, bilgisayar adı `depogoz`.
  - JetPack 6.2.1 (Ubuntu 22.04, Jetson Linux 36.4.7, firmware 36.4.7).
- **DepoGöz sunucusu:**
  - Jetson'da `depogoz` adlı systemd servisi olarak çalışıyor, açılışta kendiliğinden başlıyor.
  - Port **8000**.
- **Arayüz:** Tarayıcıda `http://<jetson-ip>:8000`.

## 2. Ağ ve IP adresleri

### Jetson hangi ağa bağlanıyor?
- **Otomatik:** Jetson daha önce bağlandığı Wi-Fi ağlarını hatırlıyor. Şu an kullandığımız ağ telefonun internet paylaşımı. Adı: **`internet`**.
- **Ethernet:** Kablo takılırsa o ağdan otomatik adres alır.
- **Kendi Wi-Fi'si yok:** Jetson kendi ağını yaymıyor; böyle bir ayar yapılmadı.

### IP adresini bulmak
Telefonun paylaşımı **her açılışta farklı bir ağ adresi** veriyor. Örneğin bir gün `10.92.90.x`, başka gün `10.51.89.x`. Ama Jetson şimdiye kadar hep **sonu `.64` olan** adresi aldı.

| Tarih | Bilgisayarın adresi | Jetson |
|---|---|---|
| 7 Ekim | 10.92.90.89 | **10.92.90.64** |
| 29 Ekim | 10.51.89.89 | **10.51.89.64** |

Jetson'ı bulmanın yolları:
1. **Bilgisayarın adresine bak, sonunu `.64` yap:**
   - macOS: `ipconfig getifaddr en0`
   - Windows: `ipconfig`

   Örneğin bilgisayar `10.51.89.89` ise Jetson büyük ihtimalle `10.51.89.64`'tür.
2. **Ağdaki cihazları listele:** `arp -a` (macOS ve Windows'ta çalışır). Listede `.64` ile biten adres Jetson'dır.
3. **Jetson'ın kendi ekranında:** Terminal'i aç (Ctrl+Alt+T), `hostname -I` yaz. İlk adres doğru olan. `172.17.0.1` Docker'ın iç adresi, onu kullanma.
4. **Ağ yoksa USB-C kablo:** Jetson'ın USB-C girişini veri kablosuyla bilgisayara bağla. Jetson **her zaman `192.168.55.1`** adresinde olur. İnternet ya da Wi-Fi gerekmez; sunum ve gösterimler için en güvenilir yol bu.

## 3. Jetson'a bağlanmak (SSH)

```bash
ssh depogoz_fc@<jetson-ip>
```
- İlk bağlantıda "Are you sure…?" sorusuna `yes` yaz. Sonra Jetson'ın şifresini gir.
- **Şifresiz bağlanmak için** bilgisayarının SSH anahtarını bir kez Jetson'a tanıt:
  ```bash
  ssh-keygen -t ed25519            # anahtarın yoksa (Enter, Enter, Enter)
  ssh-copy-id depogoz_fc@<jetson-ip>
  ```
- Windows'ta PowerShell'de `ssh` komutu var. `ssh-copy-id` yoksa:
  ```powershell
  type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh depogoz_fc@<jetson-ip> "cat >> ~/.ssh/authorized_keys"
  ```

### Şifre isteyen (sudo) işler
| İş | Komut |
|---|---|
| Kapatmak | `ssh -t depogoz_fc@<ip> 'sudo shutdown -h now'` |
| Yeniden başlatmak | `ssh -t depogoz_fc@<ip> 'sudo reboot'` |
| Sunucuyu yeniden başlatmak (kod değişince) | `ssh -t depogoz_fc@<ip> 'sudo systemctl restart depogoz'` |
| Sunucunun durumu ve son kayıtları | `ssh depogoz_fc@<ip> 'systemctl status depogoz; journalctl -u depogoz -n 50'` |

## 4. Kodu güncellemek (iş akışı)

Kodun ana kaynağı GitHub deposu. Önerilen akış:
1. Kendi bilgisayarında değiştir, commit'le, GitHub'a push'la.
2. Jetson'da çek ve servisi yeniden başlat:
   ```bash
   ssh depogoz_fc@<ip>
   cd ~/bitirme
   git remote get-url origin 2>/dev/null || git remote add origin https://github.com/estella34/bitirme_fc.git
   git pull origin main
   ```
3. **Python (arka uç) değiştiyse:**
   ```bash
   cd ~/bitirme/backend && .venv/bin/python -m pytest -q     # testler (31+ test)
   sudo systemctl restart depogoz
   ```
4. **Arayüz (web/) değiştiyse:** Arayüz Jetson'da derleniyor. Node.js `~/.local/node` altında kurulu.
   ```bash
   export PATH=$HOME/.local/node/bin:$PATH
   cd ~/bitirme/web && npm ci && npm run build
   ```
   Tarayıcıda sayfayı yenilemen yeterli; sunucuyu yeniden başlatmaya gerek yok.

> Jetson'daki eski kopyada `mac` adında bir uzak depo var; Mac'ten git bundle ile güncelleniyordu. Artık GitHub'ı (`origin`) kullanın.

## 5. Klasör yapısı

| Klasör | İçerik |
|---|---|
| `backend/` | Sunucu (Python 3.10, FastAPI, SQLite): kod okuma (zxing-cpp), mutabakat, kamera, demo simülasyonu. Jetson'da sanal ortamı `backend/.venv`. |
| `web/` | Arayüz (React + three.js): 3B dijital ikiz, Kameralar, İnceleme, Taramalar, Okuma testi |
| `jetson/` | Jetson kurulum betikleri (`scripts/kurulum_sonrasi.sh`, `saglik_kontrolu.sh`) ve `depogoz.service` |
| `mekanik/` | Teleskopik direk tasarımları (OpenSCAD), STL ve A1 baskı tablaları (.3mf) |
| `docs/` | Kararlar, Jetson kurulum rehberi, malzeme ve alışveriş listeleri |

Jetson'da veri (veritabanı ve fotoğraflar) `~/depogoz-veri` altında durur.

### Faydalı komutlar (Jetson'da, `~/bitirme/backend` içinde)
```bash
.venv/bin/depogoz print-sheet -o test.pdf     # yazdırılabilir A4 barkod/QR test sayfası
.venv/bin/depogoz benchmark --code KL-992104  # hasarlı QR okuma dayanıklılık testi
.venv/bin/depogoz demo-world                  # demo deposunu veritabanına ekle
```
Test sayfası arayüzden de alınabilir: `http://<ip>:8000/api/test-sheet` (PDF) ya da `?format=png`.

## 6. Kameralar

### CSI kameralar (Arducam CamArray + 4 × IMX519 16 MP)
- **Bağlantı:** 4 kamera → CamArray adaptörü (UC-512 Rev D2) → tek yassı kablo → Jetson'ın kamera girişi.
- **Güç:** Adaptörün 6 delikli soketi Jetson'ın 40 pinli başlığının **1–6 numaralı pinlerine** takılır. Adaptördeki **3.3V** yazısı **1 numaralı pine** gelmeli.
- ⚠️ **Adaptör ile Jetson arasındaki kablonun yönü önemli.** Ters takılınca kameralar kontrol komutlarına cevap veriyor ama **görüntü gelmiyor**.
- **En az 3 kamera takılı olmalı**, yoksa adaptör görüntü göndermiyor.
- **Görüntü düzeni:** Dört görüntü 2×2 tek karede birleşiyor: sol üst 1, sağ üst 2, sol alt 3, sağ alt 4. Kamera başına ~4 MP.
- **I2C adresleri:** Adaptör ve odak motoru I2C **bus 10** üzerinde. Adaptör `0x24`, odak motoru (AK7375) `0x0c`. Kamera sensörü `0x1a`.
- **Odak:** 0 = yakın, 4095 = uzak. Odak motoru dört kamerada birlikte hareket eder.
- **Görüntüye bakmak:**
  - DepoGöz → **Kameralar** sekmesi (canlı görüntü, otomatik odak, çek ve oku).
  - Ya da Jetson'da `./kamera_izle.sh` (dördü birden), `./kamera_izle.sh 2` (tek kamera).
  - İkisi aynı anda çalışmaz, kamerayı tek program kullanabiliyor.
  - **Cheese gibi normal kamera programları bu kameraları açamaz.** Görüntü yalnız NVIDIA'nın Argus servisi üzerinden alınabiliyor.
- **Hızlı kontrol:**
  ```bash
  ls /dev/video*                                   # kamera aygıtı
  i2cdetect -y -r 10                               # 24 ve UU(1a) görünmeli
  journalctl -k -b | grep imx519                   # sürücü kayıtları
  curl localhost:8000/api/camera                   # DepoGöz kamera durumu
  ```
- ⚠️ **29 Ekim durumu:** Adaptör I2C'de hiç görünmüyordu (`0x24` yok). Güç soketi ve kablo kontrol edilecek. Yazılım tarafı sağlam.

### Intel RealSense D435 (derinlik kamerası)
- **Doğru giriş:** Jetson'ın **USB-A (USB 3.2)** girişlerinden birine, **USB 3 destekli** kabloyla takılmalı. USB-C girişi USB 2.0 hızında; orada bağlantı yavaş ve kopuyor.
- **Python kütüphanesi:** `pyrealsense2` pip'ten kuruluyor; Jetson için hazır paketi var, denendi.
- **Kalan adım:** Normal kullanıcının kameraya erişebilmesi için udev kuralı eklenecek (sudo gerekiyor). Henüz yapılmadı.
- **Amaç:** Henüz kararlaştırılmadı. Rafa mesafe ölçmek, koli saymak ya da engel algılamak için kullanılabilir.

## 7. Bilinen tuzaklar (önemli)

1. **Sistem dili İngilizce kalmalı.** Türkçe dilde "i/İ" dönüşümü yüzünden Arducam kurulum betiği çöktü (`lsblk: unknown column`). Kurulum betiklerini `LC_ALL=C` ile çalıştırın.
2. **Ubuntu'nun "Software Updater" penceresinden güncelleme yapmayın.** Kamera sürücüsü NVIDIA çekirdeğinin yerine kuruldu. Bütün `nvidia-l4t-*` paketleri `apt-mark hold` ile kilitli; yine de büyük güncellemeleri birlikte yapalım.
3. **Jetson'daki tarayıcılar ekran kartını kullanamıyor** (snap yalıtımı yüzünden). Bu yüzden:
   - Chromium menüdeki kısayoldan açılmalı (`--disable-gpu --enable-unsafe-swiftshader` ile). Başka yoldan açılınca 3B sahne "WebGL kullanılamıyor" der.
   - 3B dijital ikize bilgisayardan bakmak çok daha akıcı.
   - Snap sistemi `snapd 24724` sürümünde sabitlendi; yeni sürüm Chromium'u açtırmıyordu.
4. **`pkill -f "..."` komutunu SSH ile verirken dikkat.** Desen, komutun kendi satırına da uyuyor ve SSH oturumunu öldürüyor. `pkill -x <ad>` kullanın.
5. **SSH'tan kapatma ve servis yeniden başlatma şifre ister.** `ssh -t` ile verin (bkz. 3. bölüm).
6. **Firmware** 36.4.7. Açılış bölümü küçük olduğu için otomatik firmware güncellemesi yer bulamıyor; gerekirse NVIDIA'nın elle yöntemiyle yapılıyor (Jetson'da `/opt/ota_package/t23x/TEGRA_BL_3767_super.Cap`).
7. **Güç butonu** (ONPOW, radyatörün altındaki buton başlığına bağlı) açar ama kendi başına kapatmaz:
   - GNOME güç tuşunu üstüne alıyor (`systemd-inhibit --list` → `gsd-media-keys ... handle-power-key`). Bu yüzden `logind.conf`'taki `HandlePowerKey` işlemiyor; GNOME'un ayarında da "kapat" seçeneği yok (`gsettings ... power-button-action` yalnız `nothing/suspend/hibernate/interactive` alır).
   - Çözüm: `depogoz-guc-tusu` servisi tuşu doğrudan okur, kısa basışta `systemctl poweroff` çalıştırır. Önce kapatmadan dene (Ctrl+C ile çık), sonra kur:
     ```bash
     cd ~/bitirme && sudo python3 jetson/scripts/guc_tusu.py --deneme
     sudo cp jetson/depogoz-guc-tusu.service /etc/systemd/system/
     sudo systemctl daemon-reload && sudo systemctl enable --now depogoz-guc-tusu
     ```
   - Basışın Jetson'a ulaşıp ulaşmadığı: `journalctl -b -u systemd-logind | grep "Power key"`.

## 8. Donanım kararları ve sıradaki işler

- **Direk:** 4 kademeli teleskopik, halat-makara düzeni.
  - Kapalıyken ~1 m, açıkken ~2,9 m. Kameralar arası mesafe her kademede eşit: 7 cm'den 67 cm'ye.
  - Yükselirken motor tek ipi sarıyor; inerken ipi bırakıyor ve borular kendi ağırlıklarıyla iniyor.
  - Motor ipindeki yük ~34 N, sürtünmeyle 50–60 N. Ayrıntı: `mekanik/direk_3m/README.md`.
- **Motor ve parçalar:**
  - Motor: 5840-31ZY enkoderli 12 V 40 RPM, sonsuz vida (kendini kilitliyor).
  - Sürücü: BTS7960. İp: 1,2 mm Dyneema.
  - Liste: `docs/donanim/ALISVERIS_LISTESI.md`.
- **Hareket eden kameralar için plan:** CSI kablosu uzayıp kısalan direkte çalışmaz. Önerilen düzen:
  - Hareket eden 3 kamera → her biri aynı yakada bir **Raspberry Pi Zero**'ya → yaylı micro-USB kablo (USB ağ bağlantısı) → Jetson.
  - En alttaki sabit kamera doğrudan Jetson'a bağlanacak.
  - Elde 3 adet Pi Zero var.
- **ESP32:** Direk kontrolcüsü olarak kullanılacak: motor, enkoder, limit anahtarları, akım koruması, LED.
- **Sıradaki işler:**
  1. CamArray bağlantısını düzeltmek.
  2. QR okuma testi (0,5 / 1 / 1,5 m).
  3. Pi Zero denemesi.
  4. Direğin montajı ve motor braketi.
  5. RealSense'in kullanım amacı.
  6. Robot şasesi ve LiDAR.
