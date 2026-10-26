# Ön kayıt: Faz 1 ve native model, Dot_Net_test'te EŞİT yanlış alarmda

Bu dosya ölçümden ÖNCE yazıldı ve commit'lendi. `on_kayit_net.md`'nin sınırlar bölümündeki açık
soruyu kapatır: Faz 1 (%92,8 kaçan, eşik 0,5) ile native model aynı yanlış alarmda karşılaştırılmadı.

## Düzeltme (ölçümden önce)

Sitedeki "%3,8" Faz 1'in yanlış alarm oranı DEĞİL: .NET araştırma notundaki uzman modelin (M2)
kaçan oranı. Faz 1'in Dot_Net_test'teki yanlış alarm oranı hiçbir belgede yazmıyor; burada ölçülür.

## Modeller ve tahminler (yeniden eğitim yok / deterministik yeniden üretim)

- **Native:** kayıtlı son model, `tahmin_et.model_yukle()` (SHA-256 doğrulamalı). Yeniden eğitilmez.
- **Faz 1:** `net_dogrulama.py`'nin "A (5 ozellik)" modeli: RF(100 ağaç, random_state=42),
  repodaki iki EMBER 2018 CSV'si (11.400 satır), `train_test_split(test_size=0.2, stratify,
  random_state=42)` eğitim kısmı, 5 özellik. Tahminleri kaydedilmediği için AYNI kodla yeniden
  üretilir. GEÇİT: eşik 0,5'te kaçan, 1 ondalığa yuvarlanınca 92,8 olmalı; değilse ölçüm DURUR.
- Küme B: `Dot_Net_test` (120.000; 60.000 zararlı, 60.000 zararsız), `net_olcum.py` ile aynı satırlar.

## Ölçüler

1. **YA_F** = Faz 1'in eşik 0,5'teki yanlış alarmı (zararsız ve p > 0,5), Wilson %95. Kaçan_F
   (zararlı ve p ≤ 0,5) de Wilson ile.
2. **Birincil:** native modelin YA_F'de kaçanı. τ* = native B zararsız skorlarının farklı değerleri
   içinde, YA_native(τ) = pay(p_zararsız > τ) ≤ YA_F olan EN KÜÇÜK τ. Raporlanan: τ*, gerçekleşen
   YA (eşitlik yüzünden YA_F'den küçük olabilir), kaçan(τ*) = pay(p_zararlı ≤ τ*), Wilson. Şeffaflık
   için bir alt adım (YA_F'yi aşan en büyük τ) de yazılır.
3. **İkincil (ters yön):** Faz 1'in, native modelin sabit tür eşiklerindeki B yanlış alarmında
   (%1,05, `net_sonuc.md`) kaçanı; aynı τ kuralı Faz 1 skorlarına uygulanır.
4. Bilgi: iki modelin B'deki AUC'si; EXE / DLL ayrımı (aynı τ ile).

τ* TEST kümesinden (B) seçilir: bu bir ROC çalışma noktasıdır, üretim eşiği değildir (Kural 6).
Amaç iki modeli aynı yanlış alarmda karşılaştırmak; native modelin üretim eşikleri değişmez.

## Yorum kuralı

Native kaçan(τ*) Wilson üst sınırı < Faz 1 kaçan Wilson alt sınırı ise "eşit yanlış alarmda native
model .NET'te daha az kaçırıyor" denir; aralıklar örtüşürse "fark gösterilemedi". İkincil ölçüde
aynı kural. Sonuçlar `net_sonuc.md`'ye EK olarak yazılır; önceki tablo değişmez.
