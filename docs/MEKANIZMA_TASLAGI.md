# Dikey kamera mekanizması — ilk yapılabilir taslak

> **Güncel yön (2026-10-04):** Kullanıcının tercihi dört kameralı, eş zamanlı açılan teleskopik direk (kapalı ~2 m → açık 5–6 m, kameralar arası hep eşit). Kurulum rehberi ve parça listesi: [`TELESKOPIK_DIREK.md`](TELESKOPIK_DIREK.md). Aşağıdaki tek arabalı vida-kızak taslağı daha basit bir yedek seçenek olarak duruyor.

Bu taslak, **Jetson ve araç motorları tabanda sabitken** dört kamerayı taşıyan tek bir arabanın raf boyunca yükselmesi içindir. Kesin parça siparişi değildir: raf yüksekliği, istenen hareket mesafesi, kameraların dizilişi ve hareketli kütle ölçülünce boyutlandırılacak. İlk hedef, araç hareketsizken bir rafı dur–çek–ilerle düzeniyle taramak.

## Önerilen ilk mimari

```text
    üst mekanik durdurucu + üst limit anahtarı
    ┌─────────────────────────────────────┐
    │  sol kılavuz   vida   sağ kılavuz   │
    │      │          │          │        │
    │      │     ┌────┴────┐     │        │
    │      │     │ hareketli│     │        │
    │      │     │  araba    │     │        │
    │      │     └─kameralar┘    │        │
    │      │          │          │        │
    └──────┴──────────┴──────────┴────────┘
    alt limit + mekanik durdurucu
           motor + kaplin + sürücü
    ═══════════ robot şasisi ═══════════
       Jetson (sabit)   Arduino (sabit)
```

İki dikey kılavuz arabanın dönmesini ve sallanmasını sınırlar; ortadaki trapez vida yalnız yukarı–aşağı tahrik sağlar. Vidayı tek başına kılavuz gibi kullanmayız. İki 2040 alüminyum profil ve V-tekerli araba **veya** iki hazır lineer ray/kızak kullanılabilir. Üst-alt travers ve köşe bağlantılarıyla profiller tek rijit çerçeveye bağlanır. Çerçeve araç şasisine geniş bir taban plakası ve çapraz desteklerle sabitlenir.

Hareketli araba PETG baskı ya da alüminyum plakadan yapılabilir; ilk sürümde dört kameranın açı ve yüksekliği ayarlanabilir yuvalar bırakılır. Kameraların aynı mı farklı mı seviyede duracağına göre bu plakanın biçimi değişir. Kamera/LED başlığı olabildiğince hafif ve vida eksenine yakın tutulur.

**Atölyede kurulabilecek örnek ölçek:** Net strok yaklaşık 60–70 cm çıkarsa, iki adet yaklaşık 90–100 cm uzunluğunda 2040 profil, bunların üzerinde tekerli/kızaklı bir araba ve ortada ince adımlı bir trapez vida ile başlayın. Arabanın önüne önce tek kamera ve deneme ağırlığı koyun. 8 mm sınıfı vida ve NEMA 17 sınıfı motor bu ölçekte *denenebilecek* parçalardır; dört kameralı son sistem için onaylanmış seçim sayılmazlar. Vida boyu, destekleme biçimi, motor/sürücü ve profil aralığı gerçek strok ve kütle ölçüsüne göre yeniden seçilir.

## Ölçüden parçaya geçiş

Önce şu dört değeri ölçün: **en alt ve en üst kamera merkezi** (mm), **gereken net strok** (mm), **araba + dört kamera + braket + ışık + hareket eden kablonun toplam kütlesi** (kg), **robotun taban genişliği** (mm). Basit tek kademeli mastın kapalı boyu yaklaşık strok + araba boyu + uç payları kadar olur; dolayısıyla örneğin 70 cm strok istiyorsanız mast araç üstünde zaten yaklaşık 80–100 cm yer kaplar. Bu aralık bir tasarım tahminidir, parça ölçüsü değildir.

Strok yaklaşık 50–80 cm ve mastın bu boyda kalması kabul ediliyorsa tek kademeli vida-kızak düzeni ilk deneme için makuldür. Daha uzun strokta vida çapı, serbest boyu, yataklama ve hedef hız birlikte kontrol edilmelidir; uzun, ince bir vidayı yalnız tork hesabına göre seçmeyin. Araç kısa kalmalı ama mast 1–1,5 m'den fazla açılmalıysa iki kademeli teleskopik kolon ayrı bir tasarımdır: iç içe kızaklar, senkron tahrik, kablo yönlendirme ve güç kesilince tutma çözümü gerektirir. İlk prototip için otomatik olarak teleskopik tasarımı seçmeyin.

İlk parça grupları: (1) iki kılavuz profil/ray ve uyumlu araba/teker/kızak, (2) üst-alt travers, taban plakası, köşebent ve bağlantı elemanları, (3) seçilen strok ve yüke uygun trapez vida, somun, iki uç yatak ve kaplin, (4) **dikey eksene özel** step motor ve uyumlu sürücü/güç kaynağı, (5) üst-alt limit anahtarı ve bağımsız fiziksel durdurucular, (6) kamera braketi ve hareketli kablo taşıyıcısı. Araçta zaten bulunan yürüyüş motorları bu eksenin motoru olarak sayılmıyor.

Motor ve vida için alışveriş kararı, kütle/hız/strok ölçülüp üretici tablolarındaki dikey yük, kritik vida devri ve motorun hedef devirdeki torku kontrol edildikten sonra verilir. İnce adımlı trapez vidanın sürtünmeyle konumu koruması mümkün olsa da **yükün kendiliğinden inmeyeceğini varsaymayın**: somun tipi, adım, yağlama ve yük sonucu değiştirir. Güç kesildiğinde düşme testi yapın; gerekirse fren veya karşı denge kullanın.

## Yapım sırası

1. **Masaüstü iskelet:** Profilleri/rayları ve arabayı kurun. Motorsuz elle tam strok boyunca sıkışmadan kaydığını ve arabanın öne doğru eğilmediğini görün.
2. **Tahrik:** Ortadaki vidayı altta eksenel yükü taşıyan bir yatakla, üstte hizalayan uygun bir destekle kurun; somunu arabaya, alttaki motoru kaplinle vidaya bağlayın. Vida ve iki kılavuz paralel olmalı; sıkışma varsa motor gücüyle zorlamayın.
3. **Sınırlar:** Alt ve üst limit anahtarlarını, her ikisinden bağımsız sert mekanik durdurucuları ekleyin. Kontrolcü açılışta düşük hızda alt referansa dönsün; sınır veya hata algılanınca hareketi kessin. Hareketli bölgeye el/kablo girmesini önleyen kapak düşünün.
4. **Kablolar:** Jetson ve güç kaynağı tabanda kalsın. Kamera kablolarını arka tarafta bir kablo zinciri veya kontrollü halka üzerinden, bükülme yarıçapı ve uçlarda çekme emniyeti sağlayarak taşıyın. Önce **tek kameranın** kablosuyla tüm strokta tekrarlı hareket ve görüntü testini yapın.
5. **Yük testi:** Önce kamera yerine eşdeğer ağırlık bağlayın; altta, ortada, üstte durup tekrar aynı konuma dönebildiğini ölçün. Ardından kameraları ve ışığı ekleyin; titreşim yatıştıktan sonra fotoğraf çekin. En üst konumda robotun devrilme eğilimini kontrol edin.
6. **Yazılım:** Arduino motor sürücüsü ve limitleri yönetir; Jetson seri bağlantıyla `HOME`, `MOVE <mm>`, `STOP` gibi komutlar verir. `konuma vardı → kısa süre sabitlendi → görüntü alındı` sırası uygulanır. Araç yürürken mast kapalı ve kilitli olmalı.

## Kamera bağlantısının tasarıma etkisi

Orin Nano Developer Kit üzerinde **iki fiziksel 22 pin CSI soketi** vardır. Dört CSI kamera için uyumlu çoklu kamera kartı/taşıyıcı çözümü veya kamera arayüzü değişikliği ayrıca doğrulanmalıdır; dört modülün doğrudan takılabildiğini varsaymayın. Bu seçim, hareket edecek kablo sayısını ve kablo taşıyıcısının ölçüsünü belirler. Uzun hareketli CSI şerit kablosunun çalışacağını da önceden kabul etmeyin; gerçek kablo ve kamera modeliyle tam stroklu deney yapın.

## Tasarımı netleştirmek için eksik üç bilgi

- Rafın altından üstüne erişilecek kamera yüksekliği ve istenen net yükselme mesafesi.
- Dört kameranın aynı seviyede mi, farklı yüksekliklerde mi duracağı.
- Kamera modüllerinin model kodu ile toplam hareketli yükün yaklaşık kütlesi.

## Teknik dayanaklar

- [NVIDIA Orin Nano Developer Kit donanım yerleşimi](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/hardware_layout.html): iki fiziksel CSI bağlantısı.
- [igus: dikey eksende vida seçimi](https://toolbox.igus.com/motion-plastics-blog/lead-screws-for-vertical-machine-tool-axes/): yük, strok, kritik devir ve güç kesilince konum koruma birlikte değerlendirilmeli.
- [igus: kendinden kilitleme koşulları](https://toolbox.igus.com/motion-plastics-blog/self-locking-what-is-it/): vida geometrisi ve sürtünmeye bağlıdır.
