# tests/fixtures

Küçük, ZARARSIZ test dosyaları (ör. .NET `.dll`) için.

Kurallar:
- Yalnızca imzalı / bilinen kaynaklı zararsız dosyalar (ör. `C:\Windows\Microsoft.NET`
  altındaki küçük bir assembly). Gerçek zararlı örnek ASLA eklenmez.
- Dosya başına <= 200 KB; toplam birkaç dosya.
- Her dosya için aşağıdaki tabloya kaynak yolu ve SHA-256 yazılır
  (`certutil -hashfile <dosya> SHA256`).

| Dosya | Kaynak yol | Boyut | SHA-256 |
|-------|------------|-------|---------|
