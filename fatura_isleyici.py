import os
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio
import aiofiles
from datetime import datetime
import sys
import shutil  # Temp klasörünü silmek için ekleyelim

class FaturaIsleyici:
    def __init__(self, ana_dizin, cikti_dizin):
        self.ana_dizin = Path(ana_dizin)
        self.cikti_dizin = Path(cikti_dizin)
        self.temp_dizin = self.cikti_dizin / "temp"
        
        # Debug mesajları ekleyelim
        print(f"Ana dizin: {self.ana_dizin.absolute()}")
        print(f"Çıktı dizin: {self.cikti_dizin.absolute()}")
        
        # Dizinleri oluştururken hata kontrolü ekleyelim
        try:
            self.temp_dizin.mkdir(exist_ok=True, parents=True)
            self.cikti_dizin.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            print(f"Dizin oluşturulurken hata: {e}")

        self.progress_callback = None
        self.fatura_yillari = {}  # {yil: [fatura_verileri]}

    async def zip_ac(self, zip_yolu):
        try:
            hedef_dizin = self.temp_dizin / zip_yolu.stem
            print(f"Zip hedef dizin: {hedef_dizin}")
            
            with zipfile.ZipFile(zip_yolu, 'r') as zip_ref:
                # Zip içindeki dosyaları listele
                icerdeki_dosyalar = zip_ref.namelist()
                print(f"Zip içindeki dosyalar: {icerdeki_dosyalar}")
                
                # Ana zip'i aç
                zip_ref.extractall(hedef_dizin)
                
                # İç zip dosyalarını bul ve aç
                for dosya in icerdeki_dosyalar:
                    if dosya.lower().endswith('.zip'):
                        ic_zip_yolu = hedef_dizin / dosya
                        print(f"İç zip bulundu: {ic_zip_yolu}")
                        try:
                            with zipfile.ZipFile(ic_zip_yolu, 'r') as ic_zip:
                                ic_zip.extractall(hedef_dizin / ic_zip_yolu.stem)
                                print(f"İç zip açıldı: {ic_zip_yolu}")
                        except Exception as e:
                            print(f"İç zip açılırken hata: {ic_zip_yolu} - {e}")
                            
            return hedef_dizin
        except Exception as e:
            print(f"Zip açılırken hata: {zip_yolu} - {e}")
            return None

    def xml_oku(self, xml_yolu):
        try:
            # Eğer dizin ise atla
            if xml_yolu.is_dir():
                return None
            
            # XML dosyasını bul - iç zip'ten çıkan .xml dosyasını ara
            xml_dosyasi = None
            if xml_yolu.suffix == '.zip':
                with zipfile.ZipFile(xml_yolu, 'r') as zip_ref:
                    for isim in zip_ref.namelist():
                        if isim.endswith('.xml'):
                            # XML'i geçici olarak çıkar
                            zip_ref.extract(isim, xml_yolu.parent)
                            xml_dosyasi = xml_yolu.parent / isim
                            break
            else:
                xml_dosyasi = xml_yolu
            
            if not xml_dosyasi or not xml_dosyasi.exists():
                print(f"XML dosyası bulunamadı: {xml_yolu}")
                return None
            
            tree = ET.parse(xml_dosyasi)
            root = tree.getroot()
            
            # UBL-TR namespace'lerini tanımlayalım
            ns = {
                'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
            }
            
            # Temel verileri çekelim
            toplam = float(root.find('.//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount', ns).text)
            para_birimi = root.find('.//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount', ns).attrib.get('currencyID', 'TRY')
            
            # Döviz kuru bilgisini al
            try:
                kur_elementi = root.find('.//cac:PricingExchangeRate', ns)
                if not kur_elementi:
                    kur_elementi = root.find('.//cac:PaymentAlternativeExchangeRate', ns)
                
                if kur_elementi:
                    kur = float(kur_elementi.find('cbc:CalculationRate', ns).text)
                    try_karsiligi = toplam * kur
                else:
                    try_karsiligi = toplam if para_birimi == 'TRY' else 0
            except:
                try_karsiligi = toplam if para_birimi == 'TRY' else 0
            
            veri = {
                'Sipariş Tarihi': root.find('.//cac:OrderReference/cbc:IssueDate', ns).text if root.find('.//cac:OrderReference/cbc:IssueDate', ns) is not None else '',
                'Sipariş No': root.find('.//cac:OrderReference/cbc:ID', ns).text if root.find('.//cac:OrderReference/cbc:ID', ns) is not None else '',
                'Fatura No': root.find('.//cbc:ID', ns).text,
                'Tarih': root.find('.//cbc:IssueDate', ns).text,
                'Satıcı': root.find('.//cac:AccountingSupplierParty//cac:PartyName/cbc:Name', ns).text,
                'Alıcı': root.find('.//cac:AccountingCustomerParty//cac:PartyName/cbc:Name', ns).text,
                'Toplam': toplam,
                'Para Birimi': para_birimi,
                'TRY Karşılığı': try_karsiligi  # Yeni alan
            }
            
            # Kalem detaylarını çekelim
            kalemler = []
            for kalem in root.findall('.//cac:InvoiceLine', ns):
                # Para birimi bilgisini al
                para_birimi = kalem.find('.//cbc:LineExtensionAmount', ns).attrib.get('currencyID', 'TRY')
                
                kalem_veri = {
                    'Sipariş No': veri['Sipariş No'],  # Ana veriyle ilişkilendirmek için
                    'Kalem No': kalem.find('cbc:ID', ns).text,
                    'Ürün/Hizmet': kalem.find('.//cac:Item/cbc:Name', ns).text,
                    'Miktar': float(kalem.find('cbc:InvoicedQuantity', ns).text),
                    'Birim Fiyat': float(kalem.find('.//cac:Price/cbc:PriceAmount', ns).text),
                    'KDV Oranı': float(kalem.find('.//cac:TaxTotal//cbc:Percent', ns).text if kalem.find('.//cac:TaxTotal//cbc:Percent', ns) is not None else 0),
                    'KDV Tutarı': float(kalem.find('.//cac:TaxTotal/cbc:TaxAmount', ns).text),
                    'Toplam Tutar': float(kalem.find('.//cbc:LineExtensionAmount', ns).text),
                    'Para Birimi': para_birimi
                }
                kalemler.append(kalem_veri)
            
            return veri, kalemler
            
        except Exception as e:
            print(f"Hata: {xml_yolu} okunurken hata oluştu - {e}")
            return None

    async def tum_yillari_isle(self):
        try:
            # Tüm zip dosyalarını bul
            zip_dosyalari = list(self.ana_dizin.glob("**/*.zip"))
            toplam_dosya = len(zip_dosyalari)
            islenen_dosya = 0
            toplam_fatura = 0
            
            # İlk durumu bildir
            if self.progress_callback:
                self.progress_callback("", {
                    'toplam_dosya': toplam_dosya,
                    'islenen_dosya': islenen_dosya,
                    'bulunan_fatura': toplam_fatura,
                    'yillik_dagilim': '-'
                }, {})  # Boş detay gönder
            
            for zip_yolu in zip_dosyalari:
                try:
                    hedef_dizin = await self.zip_ac(zip_yolu)
                    if not hedef_dizin:
                        continue
                        
                    # XML dosyalarını bul ve işle
                    xml_dosyalari = list(hedef_dizin.rglob("*.xml"))
                    zip_fatura_sayisi = 0
                    yil_dagilimi = {}
                    
                    for xml_yolu in xml_dosyalari:
                        sonuc = self.xml_oku(xml_yolu)
                        if sonuc:
                            veri, kalemler = sonuc
                            yil = datetime.strptime(veri['Tarih'], '%Y-%m-%d').year
                            
                            # Yıl dağılımını güncelle
                            if yil not in yil_dagilimi:
                                yil_dagilimi[yil] = 0
                            yil_dagilimi[yil] += 1
                            zip_fatura_sayisi += 1
                            
                            # Fatura verilerini sakla
                            if yil not in self.fatura_yillari:
                                self.fatura_yillari[yil] = {'veriler': [], 'kalemler': []}
                            self.fatura_yillari[yil]['veriler'].append(veri)
                            self.fatura_yillari[yil]['kalemler'].extend(kalemler)
                    
                    # İşlenen dosya istatistiklerini güncelle
                    islenen_dosya += 1
                    toplam_fatura += zip_fatura_sayisi
                    
                    # İşlem bittiğinde son durumu gönder
                    if self.progress_callback:
                        self.progress_callback(
                            "",
                            {
                                'toplam_dosya': toplam_dosya,
                                'islenen_dosya': islenen_dosya,
                                'bulunan_fatura': toplam_fatura
                            },
                            {
                                'filename': zip_yolu.name,
                                'fatura_count': zip_fatura_sayisi,
                                'year_distribution': ", ".join(f"{yil}: {sayi}" for yil, sayi in yil_dagilimi.items())
                            }
                        )
                    
                except Exception as e:
                    print(f"Zip işlenirken hata: {zip_yolu} - {e}")
            
            # İşlem bittiğinde son durumu gönder
            if self.progress_callback:
                self.progress_callback(
                    "",
                    {
                        'toplam_dosya': toplam_dosya,
                        'islenen_dosya': islenen_dosya,
                        'bulunan_fatura': toplam_fatura
                    },
                    {
                        'filename': 'Tamamlandı',
                        'fatura_count': toplam_fatura,
                        'year_distribution': 'İşlem tamamlandı'
                    }
                )
            
            # Her yıl için Excel oluştur
            for yil, veriler in self.fatura_yillari.items():
                try:
                    excel_yolu = self.cikti_dizin / f"{yil}_rapor.xlsx"
                    self.excel_olustur(veriler['veriler'], veriler['kalemler'], excel_yolu)
                except Exception as e:
                    print(f"Excel oluşturulurken hata: {e}")
            
        except Exception as e:
            print(f"İşlem sırasında hata: {e}")
            raise
        finally:
            # Temp klasörünü temizle
            try:
                if self.temp_dizin.exists():
                    shutil.rmtree(self.temp_dizin)
                    print("Temp dizini temizlendi")
            except Exception as e:
                print(f"Temp dizini temizlenirken hata: {e}")

    def progress(self, message, stats=None, file_details=None):
        if stats is None:
            stats = {}
        if file_details:
            self.progress_callback(message, stats, file_details)

    def excel_olustur(self, veriler, kalemler, excel_yolu):
        try:
            # Ana veri için DataFrame oluştur ve TRY toplamı sütunu ekle
            df_ana = pd.DataFrame(veriler)
            df_ana['Alıcı Toplam (TRY)'] = df_ana['TRY Karşılığı']  # XML'den gelen TRY karşılığını kullan
            
            # Sütun sırasını düzenle
            sutun_sirasi = [
                'Sipariş Tarihi',
                'Sipariş No',
                'Fatura No',
                'Tarih',
                'Satıcı',
                'Alıcı',
                'Toplam',
                'Para Birimi',
                'Alıcı Toplam (TRY)'
            ]
            df_ana = df_ana[sutun_sirasi]
            
            # Kalemler için DataFrame oluştur
            df_kalemler = pd.DataFrame(kalemler)
            
            # TRY toplamını hesapla
            try_toplam = df_ana['Alıcı Toplam (TRY)'].sum()
            
            # Excel yazıcı oluştur
            with pd.ExcelWriter(excel_yolu, engine='openpyxl') as writer:
                # Ana sayfayı yaz
                df_ana.to_excel(writer, sheet_name='Faturalar', index=False)
                
                # Kalemler sayfasını yaz
                df_kalemler.to_excel(writer, sheet_name='Kalemler', index=False)
                
                # Özet sayfası ekle
                ozet_data = {
                    'Metrik': ['Toplam Fatura Sayısı', 'TRY Cinsinden Toplam'],
                    'Değer': [len(veriler), f"{try_toplam:,.2f} TL"]
                }
                pd.DataFrame(ozet_data).to_excel(writer, sheet_name='Özet', index=False)
                
                # Excel'i otomatik boyutlandır
                for sheet_name in writer.sheets:
                    sayfa = writer.sheets[sheet_name]
                    
                    # Sütun genişliklerini ayarla
                    for column in sayfa.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        # Başlık ve içerik uzunluklarını kontrol et
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                            adjusted_width = (max_length + 2)
                            sayfa.column_dimensions[column_letter].width = adjusted_width
                    
                    # Ana sayfadaki Sipariş No'ya link ekle
                    if sheet_name == 'Faturalar':
                        for idx, row in enumerate(sayfa.iter_rows(min_row=2), start=2):
                            siparis_no = row[1].value  # Sipariş No sütunu
                            if siparis_no:
                                # Detay sayfasında ilgili satırı bul
                                kalemler_sayfa = writer.sheets['Kalemler']
                                for detay_idx, detay_row in enumerate(kalemler_sayfa.iter_rows(min_row=2), start=2):
                                    if detay_row[0].value == siparis_no:  # Detay sayfasındaki Sipariş No
                                        row[1].hyperlink = f"#Kalemler!A{detay_idx}"
                                        row[1].style = "Hyperlink"
                                        break
            
            print(f"Excel başarıyla oluşturuldu: {excel_yolu}")
            print(f"Toplam fatura sayısı: {len(veriler)}")
            print(f"Toplam kalem sayısı: {len(kalemler)}")
            print(f"TRY Cinsinden Toplam: {try_toplam:,.2f} TL")
            
        except Exception as e:
            print(f"Excel oluşturulurken hata: {e}")
            raise 