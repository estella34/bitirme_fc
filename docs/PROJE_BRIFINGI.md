# DepoGöz — dikey kameralı depo envanter robotu: proje brifingi

Bu belge, projeye sonradan katılacak bir yapay zekâ veya geliştiricinin bağlamı kaybetmeden yardımcı olabilmesi için yazılmıştır. Buradaki kesinleşmemiş ayrıntılar tahmin gibi sunulmamalı; ilgili bölümdeki deney veya ölçümle doğrulanmalıdır.

## 1. Projenin kısa tanımı

Bu bir lisans bitirme projesidir. Amaç, depoda rafların önünde hareket edebilen küçük bir robotun, üzerinde yükselen kamera platformu aracılığıyla koli etiketlerini görüntülemesi ve elde edilen görüntülerden envanter bilgisi üretmesidir.

Robotun hedeflediği çıktı yalnızca “barkod okundu” değildir. Her gözlem için aşağıdaki bilgilerin bir araya gelmesi istenir:

```text
tarama kimliği
raf / raf gözü kimliği
görünen koli sayısı
okunan barkod veya etiket kimliği
görüntü kanıtı
sonuç durumu
```

Sonuç durumları örneğin `doğrulandı`, `koli var / kimlik okunamadı`, `göz boş` ve `çelişki / manuel kontrol` olabilir. Sistem, emin olmadığı sonucu kesin stok verisi diye yazmamalıdır.

Projenin ayırt edici tarafı, klasik barkod çözücünün ötesine geçen, kendi depo görüntüleriyle eğitilen veya fine-tune edilen bir yapay zekâ katmanı içermesidir. En güçlü aday, barkod ya da etiket bölgesini bulan bir nesne tespit modeli ve ardından klasik barkod çözücüsüdür. Böylece tam görüntüde okunamayan küçük, açılı veya karmaşık etiket bölgesi kırpılarak daha iyi okunabilir. Okunamayan örneklerde etiket üzerindeki insan tarafından okunabilir metni OCR ile yedeklemek ikinci adaydır.

## 2. Kullanıcının çalışma yaklaşımı ve öncelikleri

- Proje iki kişilik bir bitirme projesidir.
- Donanım sade kalmalı; proje ağırlığı yazılım, veri ve yapay zekâ tarafında olmalıdır.
- Süre planı şu anda öncelik değildir. Her aşamanın somut bir çıktısı olmalıdır.
- Mekanizma henüz yapılmadı; sıfırdan tasarlanacak.
- Mevcut araç hareketi ve dikey mekanizma aynı şey değildir. Araç motorları dikey eksenin motoru kabul edilmemelidir.
- İlk uçtan uca demo, aracın hareket etmesi zorunlu olmadan, sabit duran robot üzerinde yapılabilir. Yatay otonom hareket daha sonraki entegrasyondur.
- Kullanıcı, projenin planını tıklanabilir yol haritası olarak görmek için bir `index.html` hazırlattı. Teknik dokümanlar Markdown olarak tutuluyor.

## 3. Şu an elde bulunan / planlanan donanım

| Bileşen | Durum | Kesin olanlar | Bilinmeyenler |
|---|---|---|---|
| Ana bilgisayar | Mevcut | NVIDIA Jetson Orin Nano Developer Kit | 4 GB mı 8 GB mı olduğu, güç kaynağı, depolama kapasitesi |
| Depolama | Seçilecek | microSD ya da NVMe SSD kullanılabilir | Hangisinin kullanılacağı |
| Kameralar | Planlanıyor | Dört adet CSI kamera hedefleniyor | Sensör/model, lens, odak, çözünürlük, kablo uzunluğu, sürücü desteği |
| Araç hareketi | Mevcut | Araç için motorlar, motor sürücü kartı ve Arduino olduğu söyleniyor | Motor/sürücü modelleri, besleme gerilimi, kontrol kodu |
| Dikey eksen | Yok | Kamera taşıyıcısı sıfırdan yapılacak | Strok, motor, sürücü, profil/ray, vida/kayış, kablo taşıma |
| Raf ve koliler | Hedef ortam | Kolili depo rafları | Raf ölçüleri, göz düzeni, etiket/barkod tipi, aydınlatma, çekim mesafesi |

Jetson Orin Nano Developer Kit üzerinde iki fiziksel CSI kamera soketi vardır. Dört CSI kameranın doğrudan bağlanabildiği varsayılmamalıdır. Kesin kamera modeline göre çoklu kamera kartı, başka bir taşıyıcı kart veya USB/UVC tabanlı bir düzen gerekebilir. Bu karar mekanik yerleşim ve kablo düzenini doğrudan etkiler.

## 4. Hedef sistemin çalışma şekli

İlk hedef akış şöyledir:

1. Robot rafın önünde doğru konuma gelir veya başlangıç demosunda elle sabitlenir.
2. Dikey kamera mekanizması alt referans konumuna döner.
3. Kamera platformu belirlenen raf seviyesine çıkar.
4. Mekanik titreşim kısa süre yatışır.
5. Kamera ya da kameralar görüntü alır.
6. Görüntüler tarama kimliği, konum, seviye ve kamera kimliğiyle kaydedilir.
7. Klasik barkod çözme, AI destekli bölge tespiti ve gerekirse OCR uygulanır.
8. Sonuç raf gözüyle ilişkilendirilir; belirsiz veya çelişkili durum ayrıca gösterilir.
9. Sistem sonraki seviyeye gider ve aynı işlemi tekrarlar.

Bu akışta Jetson görüntü alma, AI çıkarımı, envanter verisi ve arayüzden sorumludur. Arduino ya da seçilecek ayrı bir kontrolcü, motor sürücüsüne adım/yön sinyali verir ve limit anahtarlarını izler. Jetson, kontrolcüye yüksek seviyeli komut gönderir: `HOME`, `MOVE <mm>`, `STOP` gibi. Kontrolcü de `OK`, `AT_POSITION`, `LIMIT`, `ERROR` gibi durum döndürür.

## 5. Dikey kamera mekanizması için mevcut öneri

İlk prototip için önerilen yapı, tek hareketli araba kullanan dikey bir masttır. Jetson, batarya/güç elektroniği ve araç motorları şaside altta sabit kalır. Sadece kamera başlığı, taşıyıcı plaka ve hareket eden kablolar yukarı çıkar.

```text
             üst fiziksel durdurucu
                  + üst limit
      ┌──────────────────────────────┐
      │  kılavuz      vida     kılavuz│
      │    │           │          │   │
      │    │     hareketli araba  │   │
      │    │      [4 kamera]      │   │
      │    │           │          │   │
      └────┴───────────┴──────────┴───┘
             alt limit + durdurucu
                 motor + kaplin
      ═════════ robot şasisi ═════════
```

Mekanik ilke: iki dikey kılavuz, arabanın dönmesini ve sallanmasını engeller; ortadaki vida sadece tahrik sağlar. Vida tek başına kılavuz olarak kullanılmaz. Kılavuz çözümü, iki 2040 alüminyum profil üzerinde V-tekerli araba veya iki lineer ray/kızak olabilir. Üst ve alt traverslerle profil çerçevesi rijit olmalıdır.

Hareketli araba PETG ile 3B basılabilir veya alüminyum plakadan yapılabilir. Dört kamera için açı ayarı ve farklı dizilim denemeleri mümkün olmalıdır. Kamera/LED grubu hafif olmalı ve ağırlık merkezi mümkün olduğunca vida eksenine yakın tutulmalıdır.

Yaklaşık 50–80 cm net strok için tek kademeli vida-kızak prototipi uygundur. Örneğin 60–70 cm net strokta yaklaşık 90–100 cm profil boyu ile başlanabilir. Bu bir başlangıç ölçeğidir, satın alma listesi değildir. Kamera yükü, gerçek strok ve hedef hız ölçülmeden motor/vida kesin seçilmemelidir.

Araç kısa kalmalı fakat kamera 1–1,5 m veya daha fazla açılmalıysa iki kademeli teleskopik mast düşünülür. Teleskopik yapı; iç içe kılavuzlar, senkron hareket, daha zor kablo taşıma ve güç kesilince düşmeyi önleyen çözüm gerektirdiği için ilk prototipte gereksiz yere seçilmemelidir.

Mekanizmada mutlaka bulunması gerekenler:

- Üst ve alt limit anahtarı.
- Limit anahtarından bağımsız fiziksel mekanik durdurucu.
- Altta eksenel yükü taşıyan, üstte hizalayan vida yatakları.
- Kablo zinciri veya kontrollü kablo halkası ve uçlarda çekme emniyeti.
- Dikey eksene özel motor, sürücü ve güç kaynağı.
- Güç kesilmesi hâlinde yükün davranışını doğrulayan test; gerekirse fren ya da karşı denge.
- En üst konumda devrilme riskini azaltan geniş/rijit taban ve gerekirse çapraz destek.

Önemli mekanik test sırası: önce boş araba, sonra kamera yerine eşdeğer ağırlık, ardından tek kamera, en son dört kamera ve aydınlatma. Her durumda alt-orta-üst konuma tekrar gidiş, titreşim ve kablo sıkışması ölçülmelidir.

## 6. Kamera ve bağlantı riski

Kameraların kesin modeli bilinmiyor. Bu yüzden aşağıdaki kararlar verilmemiştir:

- Kameralar aynı yükseklikte yan yana mı, yoksa taşıyıcı üzerinde farklı yüksekliklerde mi duracak?
- Bir kamera bir raf gözünü mü görecek, yoksa birden fazla göz mü hedeflenecek?
- CSI kabloları, dikey hareket boyunca güvenilir biçimde çalışacak mı?
- Dört kamera aynı anda mı, sırayla mı görüntü alacak?
- Jetson kartı ve seçilen JetPack sürümü bu kamera modellerini destekliyor mu?

Doğru ilerleme, tek kamerayı Jetson üzerinde çalıştırıp gerçek koli etiketinin görüntüsünü almaktır. Ardından kabloyla tam strokta tekrar eden hareket yapılmalıdır. Dört kamera düzenine, tek kamera deneyi ve bağlantı topolojisi doğrulandıktan sonra geçilmelidir.

## 7. Yazılım mimarisi

Önerilen yapı dört ayrı katmandır:

| Katman | Görev |
|---|---|
| Donanım denetimi | Motor, limit anahtarları, referans alma, hata durdurma; Arduino veya ayrı kontrolcü üzerinde |
| Görüntü alma | Kamerayı seçme, fotoğraf/video alma, dosyalama ve görüntü kalitesi kontrolü |
| Görsel analiz | Barkod çözme, ön işleme, AI ile etiket/barkod tespiti, OCR, koli/göz analizi |
| Envanter uygulaması | Raf gözü eşleme, tekrar kayıtları birleştirme, güven skoru, kanıt görüntüsü ve kullanıcı arayüzü |

Görüntü dosyalarının adı ve metadata’sı tekrarlanabilir olmalıdır. Örnek alanlar:

```text
scan_id, timestamp, rack_id, shelf_id, vertical_position_mm,
camera_id, image_path, barcode_result, ocr_result,
detector_confidence, final_status
```

Sistem bir barkodu okuyamadığında kaydı kaybetmemeli; görüntüyü, konumu ve `koli var / kimlik okunamadı` durumunu saklamalıdır. Bu örnekler hem manuel inceleme hem de sonraki eğitim verisi için değerlidir.

## 8. AI araştırma ve geliştirme planı

### Temel karşılaştırma: AI olmadan çalışan sürüm

İlk sürümde tüm görüntü, klasik barkod çözücülere verilir. ZXing, pyzbar veya uygun alternatifler denenebilir. Gerekli olduğunda gri seviye, kontrast, eşikleme, keskinleştirme veya perspektif düzeltme gibi klasik ön işlemler uygulanabilir. Bu sürüm “baseline”dır ve AI’ın gerçek katkısını ölçmek için korunmalıdır.

### Ana AI eklentisi: barkod/etiket bölgesi tespiti

Küçük bir ön eğitimli nesne tespit modeli, projenin kendi raf ve kamera görüntüleriyle fine-tune edilir. Model barkod, etiket veya ikisini birden kutu olarak bulur. Tespit edilen bölge, orijinal çözünürlüklü görüntüden kırpılır; ardından aynı klasik barkod çözücüye verilir.

Bu yaklaşım, AI’ın barkod karakterlerini doğrudan çözmesi yerine görüntüde doğru bölgeyi bulması nedeniyle lisans projesi için daha uygulanabilir ve karşılaştırılabilirdir. Başarı; tespit mAP/precision/recall yanında, en önemlisi tam kod okuma oranı ile ölçülmelidir.

### İkinci AI eklentisi: OCR yedeği

Barkod çözülemezse, etiket üzerindeki insan tarafından okunabilir SKU, koli numarası veya metin OCR ile çıkarılabilir. Hazır OCR ile kendi depo etiketlerine uyarlanmış yöntem ayrı ayrı ölçülmelidir. OCR metni, beklenen kod biçimi veya stok listesiyle doğrulanmalı; düşük güvenli sonuç kesin kayıt olmamalıdır.

### Veri belirlerse seçilecek üçüncü eklenti

Veri incelenmeden üçüncü modüle kesin karar verilmemeli:

- Sorun ağırlıkla hareket bulanıklığı veya düşük çözünürlükse görüntü iyileştirme/deblurring/süper çözünürlük.
- Sorun raf görünürlüğü, koli sayısı veya boş gözse boş/dolu göz ve görünür koli tespiti.
- Sorun yanlış raf yerleşimiyse etiket–göz–ürün eşleşmesi ve değişim tespiti.

Her modül, sadece gerçek test verisinde ölçülebilir bir katkı gösterirse projeye eklenmelidir.

## 9. Veri seti planı

En değerli veri, bu robotun kendi kamerasından ve kendi hedef raf düzeninden toplanan veridir. Veri; farklı yükseklik, mesafe, ışık, açı, koli yoğunluğu, etiketi kısmen kapalı örnekler ve hafif hareket bulanıklığı içermelidir.

Her görüntü için mümkünse şunlar tutulur:

- Gerçek barkod metni / beklenen kod.
- Barkod ve etiket kutuları.
- Raf ve raf gözü kimliği.
- Görünür koli sayısı.
- Etiket üzerindeki okunabilir metin.
- Işık, mesafe, açı ve kamera kimliği.
- Okunabilirlik durumu: okunur, zor, okunamaz, kapalı, hasarlı vb.

Eğitim, doğrulama ve test ayrımı kare bazında rastgele yapılmamalıdır. Aynı fiziksel koli veya aynı çekim oturumunun art arda kareleri farklı bölümlere düşerse model ezber yapabilir ve sonuçlar yanıltıcı olur. Bölme fiziksel koli, çekim oturumu ve mümkünse kod kimliği düzeyinde yapılmalıdır.

## 10. Başarı metrikleri

| Metrik | Anlamı |
|---|---|
| Tam kod okuma oranı | Gerçek kodun tüm karakterleriyle doğru okunduğu örnek oranı |
| Ek kurtarma oranı | Klasik yöntemin okuyamadığı örneklerden AI sayesinde doğru okunanların oranı |
| Yanlış stok kaydı | Yanlış kimlik veya yanlış raf gözü ile kesin kayıt oluşturma oranı |
| Tespit metriği | Barkod/etiket için precision, recall, mAP |
| OCR doğruluğu | Tam dize doğruluğu ve karakter hata oranı |
| Raf/göz doğruluğu | Boş/dolu göz F1; koli sayımı için mutlak hata |
| Sistem davranışı | Tarama süresi, görüntü işleme gecikmesi, konuma tekrar gelme hatası |

Adil karşılaştırma için bütün yöntemler aynı test kümesini ve aynı görüntüleri görmelidir:

```text
B0: Tam görüntü + klasik barkod çözücü
B1: Tam görüntü + klasik ön işleme + klasik çözücü
A1: Fine-tune tespit + orijinal görüntüden kırpma + aynı klasik çözücü
A2: A1 sonucu başarısızsa OCR veya seçilen ek AI modülü
```

## 11. Şu anki en önemli açık kararlar

1. Jetson Orin Nano’nun bellek sürümü, güç kaynağı ve seçilecek depolama.
2. Dört kamera modülünün tam modeli, sürücü uyumu ve dört kameranın bağlantı topolojisi.
3. Rafın alt/üst kamera merkezi yüksekliği, net dikey strok ve duruş noktaları.
4. Kameraların platform üzerindeki dizilimi.
5. Kamera, braket, ışık ve hareketli kabloların toplam kütlesi.
6. Kamera–etiket uzaklığı, barkod türü ve etiketin üzerinde okunabilir metin olup olmadığı.
7. Barkodların tekil koli kimliği mi yoksa tekrar eden ürün SKU’su mu olduğu.
8. Gerçek depo veya temsilî raf erişimi ve veri toplama imkânı.

## 12. Bundan sonra önerilen somut çalışma sırası

1. Eldeki tüm parçaların fotoğrafını, model kodunu, gerilim/akım değerini kaydet.
2. Jetson’a uygun işletim sistemi kurulumu yap, ağ ve depolamayı doğrula.
3. Tek CSI kamerayı gerçek koli/barkod ile çalıştır; görüntü kalitesi ve sürücüyü doğrula.
4. Rafın ölçülerini ve istenen kamera yüksekliği aralığını ölç.
5. Tek kademeli dikey mast için hareketli yük, strok ve taban kararlılığı hesabını yap; sonra mekanik parçaları seç.
6. Motorsuz mekanik iskelet → tahrik → limitler → tek kamera kablosu → dört kamera yükü sırasıyla test et.
7. AI’sız barkod–raf eşleme hattını çalıştır ve sonuçları kaydet.
8. Kendi mekanizmasıyla veri topla, etiketle ve bağımsız test kümesi ayır.
9. Barkod/etiket tespit modelini fine-tune et; baseline ile aynı test kümesinde ölç.
10. İhtiyaç varsa OCR veya başka bir üçüncü AI modülü ekle.
11. En son araç hareketini güvenli biçimde bütünleştir.

## 13. İlgili yerel dosyalar

Yollar depo köküne göredir.

- `docs/YOL_HARITASI.md`: aşamalar, tamamlanma ölçütleri ve metrikler.
- `docs/MEKANIZMA_TASLAGI.md`: dikey kamera mekanizması için ilk teknik taslak.
- `docs/index.html`: kullanıcı için hazırlanmış tıklanabilir proje yol haritası.
- `docs/KARARLAR.md`: verilen teknik kararların ve gerekçelerinin kaydı.
- `docs/donanim/DONANIM_ENVANTERI.md`: eldeki parçaların model, gerilim ve durum listesi.
- `docs/jetson/KURULUM.md`: Jetson Orin Nano kurulum rehberi (Aşama B).
- `jetson/scripts/`: Jetson üzerinde çalıştırılan kurulum ve sağlık kontrolü betikleri.

Bu brifingte belirtilen noktalar değiştikçe önce ilgili kaynak dosyalar, sonra bu belge güncellenmelidir.
