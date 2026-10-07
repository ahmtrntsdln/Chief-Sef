# Şef Projesi - CLAUDE.md

Savunma amaçlı, yapay zeka destekli statik zararlı yazılım sınıflandırıcı
(EDR/antivirüs benzeri). Faz 1 (PE header + entropi + IAT ile Random Forest,
`gumruk_memuru/`) KAPANDI; .NET uzman modeli ve native dizge modeli
DENEYSEL; Faz 2 (eBPF) başlamadı.

Ayrıntılar SADECE gerekince okunur:
- `PROJE_DURUMU.md` - ölçüm sonuçları, dosya listesi, veri yeniden üretme
  talimatları, sonraki adımlar, tüm Kritik Kurallar (1-6) ve gerekçeleri.
- `GELISIM_SURECI.md` - kararların hikayesi.

## Değişmez Kurallar
1. **Gerçek zararlı örnek repoya ASLA girmez** (ikili, zip, parça, base64
   dahil). Zararlı taraf yalnızca EMBER özellik vektörlerinden gelir; canlı
   zararlı dosya bu ortamda işlenmez (izolasyon Faz 3'ün konusu).
2. **Veri dosyaları git'e girmez**: ham/üretilmiş veri (JSONL, zip, CSV,
   `model.pkl`, tarama çıktıları) yerine kaynak + üretim scripti yazılır.
   Tek istisna repodaki üç CSV (`gumruk_memuru/sef_dataset_*.csv`); bunlar
   yalnızca şema değişikliğinde yeniden yazılır, yenisi eklenmez.
   `tests/fixtures/` küçük ZARARSIZ test dosyaları içindir (bkz. oradaki README).
3. **Değerlendirme zamana VE zararlı ailesine göre ayrılmış sette yapılır**:
   eğitim eski dönem, test sonraki dönem (EMBER 2018: Ocak-Ekim -> Kasım-Aralık;
   EMBER2024: ilk 52 hafta -> son 12 hafta); aile bazında ayrı ölçüm/ayrım
   (bir ailenin testte görülen örnekleri eğitimde sızıntı yaratmamalı,
   aile bazında kaçma oranı raporlanmalı). Rastgele/aynı-dönem bölme ana
   sayı olarak raporlanmaz; raporlanacaksa zamansal sayıyla yan yana.
4. İki sınıf AYNI kaynaktan ve AYNI ölçüm koduyla üretilir; alanlar indeksle
   değil isimle okunur. Özellik çıkaran kod değişince: `python -m pytest tests`.
5. Genel skor alt grup çöküşünü gizler: .NET / EXE / DLL / paketli ayrıca
   ölçülür; yüksek doğruluk şüphe sebebidir (feature_importances_ kontrolü).
6. `except Exception` ile varsayılan değer döndürülmez; yalnızca beklenen
   hata yakalanır, PE olmayan / bozuk kayıt sayılıp açıkça atlanır.

## Çalışma
- Bağımlılıklar: `requirements.txt` (+ `-dev` testler, `-experimental` LightGBM).
- Makineye özel yollar yalnızca `gumruk_memuru/sef_ayarlar.py`'de; ölçüm
  sabitleri yalnızca `gumruk_memuru/sef_sabitler.py`'de.
- Ham EMBER verisi ve büyük CSV'ler proje DIŞINDA (kullanıcının Windows
  makinesinde `C:\ember2018`, `C:\ember2024`); bulut oturumunda yok - bu
  verilere dayanan scriptler burada çalışmaz, testler çalışır.
- Kök dizindeki `Chief 1.0/1.1` ve mimari PDF'ler tarihsel, dokunulmaz.
