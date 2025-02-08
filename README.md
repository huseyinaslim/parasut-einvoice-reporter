# Fatura İşleyici

Fatura İşleyici, e-fatura XML dosyalarını analiz edip Excel raporları oluşturan bir masaüstü uygulamasıdır.

# Build Alma

`python3 setup.py py2app`
`codesign --force --deep --entitlements entitlements.plist --sign - "dist/FaturaIsleyici.app"`
`xattr -cr "dist/FaturaIsleyici.app"`

## Kurulum

1. `Fatura İşleyici.app` dosyasını Uygulamalar klasörüne taşıyın
2. İlk kez açarken Control tuşuna basılı tutarak uygulamaya tıklayın ve "Aç" seçeneğini seçin

## Kullanım

1. Uygulamayı açın
2. "Fatura Dizini Seç" butonu ile e-fatura XML'lerinin bulunduğu klasörü seçin
   - Zip dosyaları içindeki XML'ler otomatik olarak işlenecektir
3. "Rapor Dizini Seç" butonu ile raporların kaydedileceği klasörü seçin
4. "İşlemi Başlat" butonuna tıklayın
5. İşlem tamamlandığında, seçilen rapor klasöründe yıllara göre ayrılmış Excel dosyalarını bulabilirsiniz

## Excel Raporları

Her yıl için ayrı bir Excel dosyası oluşturulur (örn: `2024_rapor.xlsx`). Her Excel dosyasında:

- **Faturalar** sayfası: Tüm faturaların özet bilgileri
- **Kalemler** sayfası: Fatura kalemlerinin detaylı dökümü

## Sık Sorulan Sorular

S: Uygulama açılmıyor?
C: Control tuşuna basılı tutarak uygulamaya tıklayın ve "Aç" seçeneğini seçin.

S: XML dosyaları işlenmiyor?
C: XML dosyalarının zip içinde olduğundan emin olun.

## Destek

Destek için issue açabilirsiniz.

## Sürüm Notları

v1.0.0 (2024-02-07)
- İlk sürüm 
