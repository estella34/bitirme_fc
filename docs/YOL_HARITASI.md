# Dikey kameralı depo envanter sistemi — yaşayan yol haritası

Bu belge başlangıç taslağıdır. Parça modelleri, raf düzeni ve veri toplama koşulları netleştikçe güncellenecek. Süre veya takvim içermez. Her aşama bir sonraki aşamaya geçmek için somut bir çıktı üretir.

## 1. Projenin hedefi

Yükselen kamera platformu raf gözlerini görüntüler. Yazılım görüntülerden görünen kolileri, barkod/etiketleri ve raf konumunu ilişkilendirerek bir envanter kaydı çıkarır. Okunamayan veya çelişkili durumları ayrıca gösterir; belirsiz okumayı kesin stok kaydı gibi yazmaz.

İlk gösterim için hedef çıktı: `tarama kimliği + raf/göz kimliği + gözlenen koli sayısı + okunan kimlik(ler) + görüntü kanıtı + sonuç durumu`. Sonuç durumu örnekleri: `doğrulandı`, `koli var/kimlik okunamadı`, `göz boş`, `çelişki/manuel kontrol`.

**Açık ürün kararı:** Barkodlar tekil koli kimliği mi, yoksa aynı ürüne ait SKU mu taşıyor? Aynı SKU çok kolide tekrar ediyorsa tek başına barkod okuma koli sayısını vermez.

## 2. Şu an bilinenler ve doğrulanacaklar

| Başlık | Şu anki bilgi | Doğrulanacak ayrıntı |
|---|---|---|
| Ana bilgisayar | Jetson Orin Nano Developer Kit; microSD veya NVMe SSD kullanılabilir | Kesin depolama seçimi ve kapasitesi, güç kaynağı, kullanılacak sistem imajı |
| Kameralar | Dört CSI kamera planı | Tam model/sensör, kablo, arayüz, lens, odak, çözünürlük, aynı anda dört akışın Jetson/kart üzerinde desteklenmesi |
| Yatay hareket | Depoda hareket edecek aracın motorları ve Arduino'ya bağlı sürücü kartı mevcut | Motor/sürücü modelleri ve araç kontrol ayrıntıları daha sonra ele alınacak |
| Dikey hareket | Henüz mekanizma veya ona ait motor seçilmedi; sıfırdan geliştirilecek | Hareket mesafesi, dört kameranın dizilimi, taşıma kapasitesi, aktüatör, duruş noktaları, titreşim, kablo taşıma, mekanik sınırlar |
| Dikey denetim | Henüz seçilmedi | Aktüatör/sürücü/denetleyici uyumu, konum geri bildirimi, limit anahtarları |
| Depo/raf | Kolili raflar | Raf ölçüleri, göz kimlikleri, çekim uzaklığı, ışık koşulları, barkod standardı, etiket örneği |

Kamera sayısı ile Jetson üzerindeki fiziksel CSI soketi sayısını eşit varsaymıyoruz. Dört kameranın bağlantı/topoloji desteği, kesin modüller ve taşıyıcı kart üzerinden doğrulanacak. Bu konu mekanik tasarımı dondurmadan önce çözülmeli. Mevcut araç motorlarının sayısı, dikey mekanizma için ayrılmış motor sayısı olarak değerlendirilmemeli.

## 3. İş sırası ve her aşamanın tamamlanma ölçütü

### A. Parçaları tanıma ve sistem sınırını çizme

Jetson ve kamera modüllerinin üzerindeki tam model kodlarını, güç değerlerini ve bağlantıların fotoğraflarını kaydet. Rafın bir örnek gözünü, kullanılacak barkodu ve koli etiketini belirle. İşlev şemasında Jetson'un görüntü işleme ve kayıt rolünü, mevcut Arduino'nun araç hareketi rolünü belirt. Dikey eksenin kontrolü donanım seçimiyle netleşecek.

**Çıktı:** Kesin parça listesi, bağlantı şeması taslağı, ölçülecek envanter alanları ve açık teknik riskler.

### B. Jetson'un temel kurulumu

Tam kart ve depolama tipine uygun resmî sistem imajını seçip yükle. İlk açılış, ağ bağlantısı, depolama alanı ve güç davranışını doğrula. Gerekli geliştirme ortamını kur; sürümleri ve kurulum adımlarını kaydet. Henüz dört kamera veya motor entegrasyonuna geçme.

**Çıktı:** Yeniden kurulabilir Jetson kurulumu ve temel sağlık kontrolü kaydı.

### C. Tek kamerayla görüntü alma deneyi

Önce tek CSI kamerayı çalıştır. Tam çözünürlüklü fotoğraf ve kısa video kaydet; odak, görüş açısı, ışık, çekim uzaklığı ve hareket bulanıklığını dene. Bir koli üzerindeki barkodun görüntüde kaç piksel genişliğinde kaldığını incele. Ardından ikinci kamerayı, sonra hedeflenen kamera düzenini sınayarak bağlantı ve bant genişliği kararını ver.

**Çıktı:** Bir kamerayla tekrarlanabilir görüntü alma; dört kameranın gerçekten nasıl bağlanacağına dair doğrulanmış karar. Kamera/lens/ışık yerleşimi için örnek görüntüler.

### D. Dikey hareket mekanizmasının Ar-Ge'si

Kamera taşıyıcısının raf boyunca erişmesi gereken yüksekliği ve kaç duruş noktasında fotoğraf çekeceğini belirle. Dört kameranın toplam kütlesini ve yerleşimini ölç; bunlara göre ray/kızak, tahrik ve denge çözümünü seç. Hareketli kablo, güç ve kamera kablosu bükülmesini tasarla. Mekanik son sınır, limit anahtarı ve durdurma davranışını ekle. Platform hareket ederken görüntü almanın mı, her katta durup görüntü almanın mı daha okunaklı olduğunu deneyle seç.

**Çıktı:** Boşta ve kamera yüküyle güvenli biçimde yukarı/aşağı hareket eden prototip; aynı duruş noktasına tekrar gelebilme ölçümü. Gerekirse mekanizma bu aşamada yeniden tasarlanır.

### E. Dikey eksen kontrolü ve Jetson ile haberleşme

Aktüatör ve kontrol kartı seçildikten sonra Jetson `dikey konuma git / taramayı başlat` gibi yüksek seviyeli komutlar yollar. Seçilen denetleyici motor sürücüsünü yönetir, limit ve hata durumlarını izler, konum/durum bilgisini geri yollar. Mevcut Arduino'nun bu görev için de kullanılıp kullanılmayacağı sonra belirlenir. Haberleşme kesilirse hareketin nasıl duracağı tanımlanır. Protokolü küçük ve kaydedilebilir tut: komut, yanıt, hata kodu, zaman damgası.

**Çıktı:** Her duruş noktasında `hareket tamamlandı → titreşim yatıştı → kameralar görüntü aldı` sırasını tekrarlayabilen sistem.

### F. AI öncesi çalışan yazılım omurgası

Raf/göz koordinatlarını tanımla. Görüntüleri `tarama/konum/kamera` kimliğiyle kaydet. Tam görüntü ve uygun klasik ön işleme üzerinde en az bir barkod çözücü çalıştır. Okunan kodu konumla ilişkilendir, tekrar okumalardan tek kayıt çıkar ve sonuçları basit bir dosya/veri tabanı ile arayüzde göster.

**Çıktı:** Başından sonuna bir raf taraması ve kaydedilmiş envanter listesi. Bu sürüm daha sonraki AI modellerinin karşılaştırma çizgisidir.

### G. Gerçek veri setini oluşturma

Kendi mekanizmanızla farklı raf yüksekliği, mesafe, ışık, açı, koli yoğunluğu ve hareket/duruş koşullarında veri topla. Her görüntü için raf gözü, görünen koliler, barkod/etiket kutuları, okunması gereken gerçek kod ve gerekiyorsa etiket metnini işaretle. Aynı kolinin art arda çekilmiş karelerini eğitim ve teste dağıtma; fiziksel koli, çekim oturumu ve mümkünse kod kimliği düzeyinde ayır.

**Çıktı:** Etiketleme kılavuzu, sürümlenmiş eğitim/doğrulama/test bölmeleri, zor koşulları içeren bağımsız test kümesi.

### H. Eğitim/fine-tuning içeren AI katkısı

**Önerilen ana modül:** Barkod ve/veya etiket bölgesi tespiti. Küçük bir ön eğitimli nesne tespit modelini kendi görüntülerinizle fine-tune et; tespit edilen bölgeyi mümkün olduğunca orijinal fotoğraftan kırpıp aynı klasik çözücüye ver.

**Önerilen ikinci modül:** Barkod okunamadığında etiket üzerindeki insan tarafından okunabilir kodu OCR ile çıkar. Hazır OCR ve kendi etiket görüntülerine uyarlanmış OCR'yi ayrı ayrı ölç. OCR sonucunu barkod biçimi ve stok kayıtlarıyla doğrula; düşük güvenli veya çelişkili sonucu inceleme durumuna al.

**Duruma bağlı üçüncü modül:** Veri incelemesi, asıl sorunun bulanıklık olduğunu gösterirse barkoda özel görüntü iyileştirme; asıl sorun görünürlük/sayım ise boş göz ve görünür koli tespiti. Üçüncü modülü sorunun verideki sıklığına göre seç.

**Çıktı:** Eğitilmiş model dosyaları, veri bölmeleri, eğitim ayarları ve AI öncesi sürümle aynı test kümesindeki sonuçlar.

### I. Entegrasyon ve gösterim

Tek düğmeyle veya tek komutla dikey tarama başlat: referans konumuna git, duruş noktalarında görüntü al, işle, raf konumuyla eşleştir ve envanteri üret. İlk uçtan uca gösterim sabit duran araçla yapılabilir. Sonuç ekranında kimlik, raf gözü, görüntü ve durum görülsün. Sistem yanlış okumayı nasıl ele aldığını ve okunamayan örnekleri nasıl raporladığını açıkça göstersin.

**Çıktı:** Tekrarlanabilir canlı demo; test verisi, sonuç tabloları ve bilinen sınırlar.

### J. Araç hareketiyle bütünleşme (daha sonra)

Mevcut Arduino ve araç motorlarının kontrol arayüzünü tanı. Raf önünde durma konumu, tarama sırasında aracın hareketsiz kalması ve bir sonraki raf konumuna geçiş sırasını ekle. Bu aşama, sabit araç üzerinde dikey tarama ve görüntü işleme çalıştıktan sonra ele alınacak.

**Çıktı:** Birden fazla raf önüne geçip her birinde aynı taramayı tekrarlayan sistem.

## 4. Ölçüm planı

| Ölçü | Tanım |
|---|---|
| Tam kod okuma oranı | Gerçek kodun bütün karakterlerinin doğru okunduğu örnekler / tüm ilgili örnekler |
| Ek kurtarma oranı | Klasik yöntemin okuyamadıklarından AI eklenince doğru okunanların oranı |
| Yanlış stok kaydı | Yanlış kimlik veya yanlış raf gözüyle kesin kayıt oluşturma sayısı/oranı |
| Barkod/etiket tespiti | Recall, precision ve mAP; tam kod okuma oranından ayrı raporlanır |
| OCR doğruluğu | Tam dize doğruluğu ve karakter hata oranı |
| Göz/sayım doğruluğu | Boş/dolu F1, görünür koli sayımı için mutlak hata |
| Sistem davranışı | Raf tarama süresi, görüntü işleme gecikmesi, konuma tekrar gelme hatası |

Karşılaştırma sırası: **B0** tam görüntüde klasik çözücü; **B1** klasik ön işleme; **A1** fine-tune tespit + aynı çözücü; **A2** seçilen OCR/restorasyon/raf modülü. Bütün yöntemler aynı test örneklerini ve aynı kare sayısını görmeli.

## 5. İlk birlikte netleştireceğimiz kararlar

1. Kameraların tam modeli ve Jetson'a bağlantı yöntemi nedir? Mevcut araç motor/sürücü ayrıntıları daha sonra kaydedilecek.
2. Kameralar platform üzerinde nasıl dizilecek ve kaç raf gözü aynı anda görülecek?
3. Barkod türü nedir; kod SKU mu, tekil koli kimliği mi? Etikette ayrıca okunabilir metin var mı?
4. Rafın ölçüleri, kamera–koli uzaklığı ve sıfırdan kurulacak dikey platformun hareket mesafesi nedir?
5. Gerçek depo/örnek raf erişimi ve görüntü toplama imkânı nedir?

Bu cevaplar gelene kadar ilk teknik öncelik **parça envanteri → Jetson kurulumu → tek kamerayla gerçek barkod görüntüsü** sırasıdır. Bu üç çıktı, geri kalan tasarımın varsayım yerine gözleme dayanmasını sağlar.
