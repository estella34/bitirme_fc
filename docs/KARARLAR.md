# Teknik karar kaydı

Projede verilen her önemli teknik kararı burada tutuyoruz: ne seçildi, neden, hangi alternatifler elendi. Tez yazımında "neden böyle yaptınız" sorusunun cevabı bu dosyadan çıkar.

Yeni kararı en üste ekleyin. Durum: `açık` (henüz verilmedi), `kabul`, `değişti → K-xxx`.

| No | Tarih | Konu | Durum |
|---|---|---|---|
| K-003 | 2026-10-03 | Jetson depolama düzeni | açık |
| K-002 | 2026-10-03 | Jetson JetPack sürümü | kabul |
| K-001 | 2026-10-03 | Depo yapısı ve dokümantasyon düzeni | kabul |

---

## K-003 — Jetson depolama düzeni

**Durum:** açık

**Seçenekler:**
- İşletim sistemi microSD'de, NVMe `/data` olarak veri diski (JetPack 6 yolunda Mac'ten kurulabilir).
- İşletim sistemi doğrudan NVMe'de (JetPack 7 ISO kurulumcusuyla veya Ubuntu bilgisayar + SDK Manager ile).
- Yalnız microSD (en basit; veri seti büyüyünce yavaş ve yıpranmaya açık).

**Öneri:** Elde NVMe varsa ilk seçenek. Ayrıntı: `docs/jetson/KURULUM.md` §3A ve §7.

## K-002 — Jetson JetPack sürümü

**Durum:** kabul — **JetPack 6.2.1** (Jetson Linux r36.4.4, Ubuntu 22.04), microSD kart imajıyla kurulum.

**Seçenekler:** JetPack 6.2.1 (r36.4.4, Ubuntu 22.04) veya JetPack 7.2.1 (r39.2.1, Ubuntu 24.04).

**Gerekçe:** Projenin ihtiyaçları (CSI kamera, OpenCV, barkod çözücü, YOLO + TensorRT) 6.2.1'de karşılanıyor; 7.2.1'in yenilikleri bu projede belirleyici değil. Kurulum USB bellek gerektirmiyor. Dört kamera bağlantısı en büyük risk. Üçüncü taraf kamera sürücüleri genelde belirli Jetson Linux sürümlerine bağlı ve 6.x en geniş desteğe sahip. Kamera üreticisi r39 desteğini belirtirse 7.2.1'e geçilebilir. Ayrıntı: `docs/jetson/KURULUM.md` §1.

## K-001 — Depo yapısı ve dokümantasyon düzeni

**Durum:** kabul

**Karar:**
- Tüm belgeler `docs/` altında. Brifing, yol haritası ve mekanizma taslağı Markdown olarak tutuluyor; `docs/index.html` tıklanabilir yol haritası.
- Jetson'a özgü betikler `jetson/scripts/`, Jetson'dan alınan raporlar `jetson/kayitlar/` altında.
- Büyük dosyalar (veri seti, ham görüntü/video, model ağırlıkları, imajlar) git'e girmiyor. Nerede tutuldukları belgelenecek.
- Satır sonları LF (`.gitattributes`). Jetson, macOS ve Windows arasında betikler bozulmuyor.
