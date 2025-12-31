# ISOTEC CBAM Reporting Platform (MVP)

Bu proje, ISOTEC Enerji için AB'nin CBAM (Carbon Border Adjustment Mechanism) raporlama
gereksinimlerini otomatikleştirmeyi amaçlayan basit bir MVP uygulamasıdır. FastAPI
tabanlı bir arka uç servisi ile gelen ürün verilerini CBAM şablonuna işler ve
kurumsal formatta bir PDF raporu üretir.

## Başlangıç

### Gereksinimler

- [Docker](https://www.docker.com/) ve [Docker Compose](https://docs.docker.com/compose/install/) yüklü olmalıdır.
- Proje kök dizininde `cbam_platform` klasörü olmalı (bu depo).

### Kurulum

1. Depoyu indirin veya bu klasör içindeki dosyaları yerel makinenize kopyalayın.
2. Terminal veya PowerShell'de proje kök dizinine gidin (``cbam_platform`` klasörünün bir üst dizini).
3. Aşağıdaki komutla servisleri başlatın:

   ```bash
   docker compose up --build
   ```

4. Docker imajı inşa edildikten sonra API `http://localhost:8088` adresinde çalışır
   olacak. Arayüz olarak auto‑generated OpenAPI/Swagger dokümanına
   `http://localhost:8088/docs` adresinden ulaşabilirsiniz.

### Kullanım

Rapor oluşturmak için `/reports` uç noktasına POST isteği gönderilir. Örnek
payload:

```json
{
  "quarter": "2025-Q3",
  "products": [
    {
      "cn_code": "7604",
      "name": "Alüminyum Profil",
      "production_ton": 200.0,
      "direct_see": 0.45,
      "indirect_see": 1.20
    },
    {
      "cn_code": "7308",
      "name": "Çelik Konstrüksiyon",
      "production_ton": 150.0,
      "direct_see": 1.10,
      "indirect_see": 0.50
    }
  ]
}
```

İstek başarılı olduğunda aşağıdaki gibi bir yanıt döner:

```json
{
  "report_id": "5b7a1ca1-8f94-45be-9655-b2b1c3c455c2",
  "excel": "/reports/5b7a1ca1-8f94-45be-9655-b2b1c3c455c2.xlsx",
  "pdf": "/reports/5b7a1ca1-8f94-45be-9655-b2b1c3c455c2.pdf"
}
```

Oluşturulan dosyalar `backend/reports` dizininde saklanır ve HTTP üzerinden
erişilebilir değildir; bunları host sistemde paylaşılan `reports` klasöründen
indirebilirsiniz.

## Yapı

- `backend/main.py` – FastAPI uygulaması ve API uç noktaları.
- `backend/cbam_excel.py` – Excel şablonunun doldurulmasından sorumlu yardımcı fonksiyonlar.
- `backend/cbam_pdf.py` – PDF raporunun üretilmesini sağlayan yardımcı fonksiyonlar.
- `backend/templates/cbam_template.xlsx` – AB Komisyonu'nun yayınladığı CBAM
  Communication Template dosyasının kopyası. Excel raporları bu şablon üzerinden
  oluşturulur.
- `docker-compose.yml` ve `backend/Dockerfile` – Konteynerin nasıl inşa edileceğini ve
  çalıştırılacağını tanımlar.

## Sonraki Adımlar

Bu MVP yalnızca ürün özet tablosunu doldurmaktadır. Gelecek sürümlerde:

- Tesis ve üretim bilgileri gibi diğer sekmelerin otomatik doldurulması,
- Yüklenen PDF/Excel faturalarından veri çıkarımı (OCR),
- Çoklu kullanıcı ve rol yönetimi,
- Arşivleme, versiyonlama ve doğrulama kontrolleri,
- Web tabanlı bir kullanıcı arayüzü oluşturulması,

planlanmaktadır.