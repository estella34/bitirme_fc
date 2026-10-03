# Jetson Orin Nano kurulum rehberi (Aşama B)

**Amaç:** Jetson Orin Nano Developer Kit'i, gerektiğinde aynı adımlarla yeniden kurulabilecek şekilde hazırlamak ve temel sağlık kontrolünü kayda geçirmek.

**Aşamanın çıktısı:** Açılıp çalışan Jetson; `jetson/kayitlar/` altında commit edilmiş bir sağlık kontrolü raporu; `docs/KARARLAR.md` içinde JetPack sürümü ve depolama kararı.

> Bu rehber Ekim 2026 itibarıyla NVIDIA'nın resmî belgelerine göre yazıldı. Sürüm numaraları değişmiş olabilir; indirmeden önce [JetPack indirme sayfasını](https://developer.nvidia.com/embedded/jetpack/downloads) kontrol edin.

---

## 0. Gerekenler

| Parça | Not |
|---|---|
| Jetson Orin Nano Developer Kit | Developer Kit 8 GB modülle gelir; kurulumdan sonra `free -h` ile doğrulayın |
| Güç adaptörü | Kutudan çıkan 19 V / 45 W adaptör. Kart **yalnız DC jaktan** beslenir (5,5×2,5 mm, orta uç +, 9–20 V). USB-C portu sadece veri içindir. Adaptörün AC kablosu çıkarılabilir ve Amerikan tipidir (Type B); Türkiye için adaptör tarafına uyan topraklı bir kablo kullanın (aşağıdaki not) |
| microSD kart | En az 64 GB, UHS-1 veya daha hızlı |
| NVMe SSD (isteğe bağlı) | M.2 2280 PCIe. Veri seti ve hız için önerilir |
| USB bellek | En az 16 GB. Yalnız JetPack 7 yolunda gerekir |
| Ekran + klavye + fare | Kartta **DisplayPort** çıkışı var. DP→HDMI adaptörlerin bazıları çalışmaz, aktif adaptör daha güvenli |
| Mac | İmajı yazmak için [balenaEtcher](https://etcher.balena.io/) |
| Ağ | Ethernet kablosu en kolayı. Kartta Wi-Fi modülü de var |

**Fiş notu:** Adaptörün etiketinde `Input: 100-240V ~ 50/60Hz` yazıyorsa yalnız fiş şeklini değiştirmek yeterli, voltaj dönüştürücüsü gerekmez. En temiz yol, Amerikan kabloyu adaptörden çıkarıp yerine adaptördeki girişe uyan Türkiye fişli bir kablo takmaktır. Yonca tipi 3 delikli girişe C5 kablo, 8 şeklindeki 2 delikli girişe C7 kablo uyar. Bu kablolar laptop şarj aletlerinde yaygındır. Fişi kesip yeniden bağlamayın, Amerikan fişi de prize zorlayarak takmayın.

**USB-C ile besleme (resmî değil):** USB-C PD → 5,5×2,5 mm DC "trigger" kablosu, 15 V veya 20 V'a sabitlenmiş hâlde, en az 45 W (tercihen 65 W) PD şarj aletiyle kullanılabilir. Kutudaki adaptör çalışıyorsa buna gerek yok.

Kurulumdan önce `docs/donanim/DONANIM_ENVANTERI.md` dosyasına kartın, SSD'nin ve adaptörün etiket fotoğraflarını ve model kodlarını işleyin.

---

## 1. Karar: hangi JetPack?

Şu an iki aday var:

| | **JetPack 6.2.1** | **JetPack 7.2.1** |
|---|---|---|
| Jetson Linux | r36.4.4 | r39.2.1 |
| Ubuntu | 22.04 | 24.04 |
| CUDA / TensorRT | 12.6 / 10.3 | 13.2 / 10.16 |
| Kurulum | Hazır **SD kart imajı** → Etcher | **ISO** → USB bellek → microSD veya NVMe'ye kurulum |
| Mac'ten NVMe'ye kurulum | Doğrudan yok (Ubuntu bilgisayar + SDK Manager gerekir) | Var (ISO kurulumcusu NVMe'yi hedef seçebiliyor) |
| Topluluk / üçüncü taraf desteği | Olgun. Çoğu kamera sürücüsü, öğretici ve hazır wheel bu sürüme göre | Yeni. Üçüncü taraf kamera sürücüleri ve öğreticiler geriden gelebilir |

**Öneri: JetPack 6.2.1.** Gerekçe şu: Projenin en büyük teknik riski 4 kameranın bağlanması. Çoklu kamera kartları ve üçüncü taraf CSI sensörlerin sürücüleri genelde belirli Jetson Linux sürümlerine göre yayınlanıyor. Kamera modeli kesinleşmeden en yaygın desteklenen sürümde kalmak daha güvenli.

**JetPack 7.2.1'e ne zaman geçilir?** Seçilen kameranın üreticisi r39 desteğini açıkça belirtiyorsa, ya da işletim sistemini doğrudan NVMe'ye kurmak öncelikliyse. Şu an veri olmadığı için ileride yeniden kurulum yapmanın maliyeti düşük.

Verilen kararı `docs/KARARLAR.md` dosyasına yazın.

---

## 2. Firmware (QSPI/UEFI) sürümünü kontrol et

Bu adım **en sık atlanan adımdır.** JetPack 6 ve 7, kartta en az **36.0** sürümlü firmware olmasını ister. Eski stoktan gelen kartlarda 35.x firmware bulunabilir. Bu durumda yeni imaj açılmaz ve ekran kararır ya da UEFI kabuğuna düşer.

1. Ekranı ve klavyeyi bağlayın, gücü verin.
2. NVIDIA logosu çıkınca **Esc** tuşuna art arda basın.
3. UEFI menüsünün üst kısmındaki firmware sürümünü okuyun.

- **36.x veya üstü:** 3. adıma geçin.
- **35.x veya altı:** önce 2a'yı uygulayın.

### 2a. Eski firmware'i güncelleme (yalnız 35.x ise)

NVIDIA'nın [firmware güncelleme yolu](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/update_firmware.html):

1. JetPack 5.1.3 köprü imajını indirin (`JP513-orin-nano-sd-card-image_b29.zip`) ve Etcher ile microSD'ye yazın.
2. Bu kartla açın ve ilk kurulumu tamamlayın.
3. Firmware güncellemesinin zamanlandığını doğrulayın:
   `sudo systemctl status nv-l4t-bootloader-config`
   Servis başarıyla `inactive` duruma geçene kadar bekleyin.
4. `sudo reboot` ile yeniden başlatın. Güncelleme ekranda görünür. **Bu sırada gücü kesmeyin.**
5. QSPI güncelleyicisini kurun ve yeniden başlatın:
   ```bash
   sudo apt update && sudo apt install nvidia-l4t-jetson-orin-nano-qspi-updater
   ```
6. Kartı kapatın. Hedef JetPack imajıyla 3. adıma devam edin. İlk açılıştan sonra aynı `systemctl status` komutuyla bekleyen bir güncelleme var mı bakın; varsa bir kez daha yeniden başlatın.

---

## 3A. JetPack 6.2.1 kurulumu (önerilen yol)

1. SD kart imajını [JetPack 6.2.1 sayfasından](https://developer.nvidia.com/embedded/jetpack-sdk-621) indirin: `jp62-r1-orin-nano-sd-card-image.zip`.
2. balenaEtcher → *Flash from file* → zip dosyası → microSD kart → *Flash*. Zip'i açmanıza gerek yok.
   - **macOS:** Etcher'ı Uygulamalar klasöründen çalıştırın ve açıldıktan sonra birkaç saniye bekleyip dosyayı seçin. Aksi hâlde `requestMetadata is not a function` hatası çıkabiliyor. Safari zip'i kendiliğinden açmaya çalışıp "başarısız" diyebilir; bunun önemi yok.
   - **Windows:** Kart takılınca ve yazma bittikten sonra Windows "sürücüyü kullanmadan önce biçimlendirmeniz gerekir" diye defalarca sorar. Hepsinde **İptal**'e basın; biçimlendirirseniz imaj bozulur. Etcher hata verirse sağ tıklayıp *Yönetici olarak çalıştır*'ı deneyin.
3. microSD'yi kartın modülünün altındaki yuvaya takın. Ekranı, klavyeyi ve Ethernet'i bağlayın, sonra gücü verin.
4. 4. adımdaki ilk açılış kurulumuna geçin.

**NVMe bu yolda nasıl kullanılır?** İşletim sistemi microSD'de kalır, NVMe'yi `/data` olarak bağlarız (bkz. [7. adım](#7-nvmeyi-veri-diski-olarak-bağlama-jetpack-6-yolu)). Veri seti, görüntüler ve modeller hızlı diskte durur. İşletim sistemi bozulsa da veri korunur.

## 3B. JetPack 7.2.1 kurulumu (alternatif)

1. ISO dosyasını [Quick Start sayfasından](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html) indirin (`jetsoninstaller-r39.2.1-…-arm64.iso`).
2. Etcher ile **USB belleğe** yazın. ISO'yu microSD'ye yazmayın.
3. Kartta microSD ve/veya NVMe takılıyken USB belleği takın ve gücü verin.
4. NVIDIA logosunda **Esc** → *Boot Manager* → USB belleği seçin.
5. Firmware güncellemesi sorulursa 30 saniye içinde **Y** tuşuna basın.
6. GRUB menüsünde *Install Jetson ISO r39.2.1* seçeneğini seçin. Hedef olarak NVMe'yi (önerilir) veya microSD'yi seçin ve onaylayın.
7. Kurulum bitince USB belleği çıkarın ve yeniden başlatın.

---

## 4. İlk açılış kurulumu

Ekrandaki sihirbazda:

- NVIDIA EULA'yı kabul edin.
- Dil: İngilizce (önerilir; hata mesajlarını aramak kolaylaşır). Klavye: Türkçe Q. Saat dilimi: Istanbul.
- **Kullanıcı adı:** ikiniz de aynı hesabı kullanacaksanız kısa ve ortak bir ad seçin (ör. `envanter`).
- **Bilgisayar adı:** `depo-jetson` (bu rehberdeki komutlar bu adı kullanır).
- Ağa bağlanın.

Parolayı bir parola yöneticisinde saklayın, depoya yazmayın.

---

## 5. Mac'ten SSH ile bağlanma

Kurulumun geri kalanını Mac'ten yapmak daha rahattır. Jetson ile Mac aynı ağdayken:

```bash
ssh envanter@depo-jetson.local
```

`.local` adı çözülmezse Jetson'da `hostname -I` ile IP adresini öğrenip onu kullanın.

**Ekran yokken:** Jetson'u Mac'e USB-C kabloyla bağlayın. Jetson USB aygıt modunda `192.168.55.1` adresinde görünür:

```bash
ssh envanter@192.168.55.1
```

**Parolasız giriş için** (Mac'te, bir kez):

```bash
ssh-keygen -t ed25519 -C "bitirme-jetson"
```

```bash
ssh-copy-id envanter@depo-jetson.local
```

---

## 6. Depoyu Jetson'a alma ve kurulum betiği

Depo GitHub'a yüklendikten sonra Jetson'da:

```bash
git clone <depo-adresi> ~/bitirme
```

Henüz uzak depo yoksa Mac'ten kopyalayın:

```bash
rsync -av --exclude .git ~/Desktop/bitirme/ envanter@depo-jetson.local:~/bitirme/
```

Jetson'da kurulum betiğini çalıştırın:

```bash
cd ~/bitirme && ./jetson/scripts/kurulum_sonrasi.sh --jtop
```

Bu betik sistemi günceller, temel paketleri kurar, eksikse `nvidia-jetpack` (CUDA, TensorRT, cuDNN) kurar, SSH'yi açar ve `jtop`'u kurar. Güç modunu, ağı ve diski değiştirmez. Bittiğinde yeniden başlatın.

---

## 7. NVMe'yi veri diski olarak bağlama (JetPack 6 yolu)

> **Dikkat:** Bu adım NVMe üzerindeki her şeyi siler. Önce `lsblk` ile diskin gerçekten `nvme0n1` olduğunu ve boş olduğunu doğrulayın.

```bash
lsblk
```

```bash
sudo parted /dev/nvme0n1 --script mklabel gpt mkpart data ext4 0% 100%
```

```bash
sudo mkfs.ext4 -L data /dev/nvme0n1p1
```

```bash
sudo mkdir -p /data && echo 'LABEL=data /data ext4 defaults,noatime,nofail 0 2' | sudo tee -a /etc/fstab
```

```bash
sudo mount -a && sudo chown "$USER":"$USER" /data && df -h /data
```

`nofail` seçeneği sayesinde SSD takılı değilse de kart açılmaya devam eder.

---

## 8. Güç modu

Developer Kit, JetPack 6.2 ve sonrasında **MAXN SUPER** modunu destekler. Mevcut modu görmek için:

```bash
sudo nvpmodel -q
```

Masa başında geliştirme yaparken en yüksek performans modu uygundur. Robot bataryayla çalışacağı zaman güç modu ayrıca seçilecek ve `KARARLAR.md` dosyasına yazılacak. Mod Ubuntu üst çubuğundaki NVIDIA simgesinden de değiştirilebilir. `jtop` ile anlık güç, sıcaklık ve GPU kullanımı izlenebilir.

---

## 9. Sağlık kontrolü ve kayıt (aşamanın çıktısı)

Jetson'da:

```bash
cd ~/bitirme && ./jetson/scripts/saglik_kontrolu.sh
```

Rapor `jetson/kayitlar/saglik-<hostname>-<tarih>.md` dosyasına yazılır. Raporda şunları kontrol edin:

- [ ] Model "Orin Nano Developer Kit", bellek ~7.4 GiB (8 GB modül)
- [ ] L4T sürümü seçilen JetPack ile uyumlu (6.2.1 → R36.4.x)
- [ ] Önyükleyici "Current version" 36.x veya üstü
- [ ] Kök dosya sistemi beklenen diskte; `/data` bağlıysa görünüyor
- [ ] `nvcc` ve TensorRT paketleri görünüyor
- [ ] OpenCV içe aktarılabiliyor ve GStreamer desteği `YES`
- [ ] SSH aktif, internet erişilebilir

Raporu commit edin. Bu dosya Aşama B'nin kanıtıdır:

```bash
git add jetson/kayitlar && git commit -m "jetson: ilk sağlık kontrolü raporu"
```

---

## 10. Sonraki adım: Aşama C (tek kamera)

Kamera modeli belli olunca:

- **CSI kamera:** `sudo /opt/nvidia/jetson-io/jetson-io.py` ile kamera soketini sensöre göre yapılandırın, yeniden başlatın, sonra `nvgstcapture-1.0` ile ilk görüntüyü alın.
- **USB kamera:** `v4l2-ctl --list-devices` ve `v4l2-ctl --list-formats-ext` ile desteklenen çözünürlükleri görün.

Kameranın sürücüsü seçilen Jetson Linux sürümünü desteklemiyorsa, kamera alınmadan önce 1. adımdaki karar gözden geçirilmeli.

---

## Sorun giderme

| Belirti | Olası neden |
|---|---|
| Ekran tamamen siyah, logo bile yok | DP→HDMI adaptörü; başka adaptör veya doğrudan DP ekran deneyin |
| Logodan sonra siyah ekran veya UEFI kabuğu | Firmware eski → 2a |
| Kart açılıp kapanıyor | Yetersiz güç; orijinal 19 V adaptörü kullanın |
| `depo-jetson.local` bulunamıyor | IP adresiyle bağlanın ya da Mac'i aynı ağa alın |
| `apt` kilit hatası | İlk açılışta otomatik güncelleme sürüyordur; birkaç dakika bekleyin |

## Kaynaklar

- [Jetson Orin Nano Developer Kit — Quick Start](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html)
- [Firmware güncelleme yolu (JetPack 6.x Update Path)](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/update_firmware.html)
- [JetPack 6.2.1](https://developer.nvidia.com/embedded/jetpack-sdk-621)
- [JetPack indirmeleri](https://developer.nvidia.com/embedded/jetpack/downloads)
- [Jetson Linux 39.2.1 sürüm notları](https://docs.nvidia.com/jetson/archives/r39.2.1/ReleaseNotes/Jetson_Linux_Release_Notes_r39.2.1.pdf)
