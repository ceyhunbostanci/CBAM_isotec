from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime
from .models import Period, Product, Energy
from typing import List, Optional

def build_pdf(out_path: str, period: Period, products: List[Product], energy: Optional[Energy]) -> str:
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20*mm, h-25*mm, "ISOTEC - CBAM İletişim Raporu")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, h-32*mm, "EU REGULATION 2023/1773 UYUMLU (MVP)")
    c.line(20*mm, h-35*mm, w-20*mm, h-35*mm)

    # Period
    c.setFont("Helvetica", 10)
    c.drawRightString(w-20*mm, h-25*mm, f"Dönem: {period.year}-Q{period.quarter}")
    c.drawRightString(w-20*mm, h-32*mm, f"Tarih: {datetime.now().strftime('%d.%m.%Y')}")

    # Installation box
    y = h-55*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, "1. TESİS BİLGİLERİ (INSTALLATION)")
    y -= 8*mm

    c.setFont("Helvetica", 10)
    lines = [
        ("Firma", period.installation_name),
        ("Adres", period.street_number + " / " + period.city),
        ("Ülke", period.country),
        ("UNLOCODE", period.unlocode),
        ("Koordinatlar", f"{period.latitude} N, {period.longitude} E"),
    ]
    x1, x2 = 20*mm, 110*mm
    for i,(k,v) in enumerate(lines):
        c.drawString(x1, y - i*6*mm, f"{k}: {v}")

    y -= 45*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, "2. GÖMÜLÜ EMİSYON ÖZETİ (SUMMARY OF GOODS)")
    y -= 8*mm

    c.setFont("Helvetica-Bold", 9)
    headers = ["CN Code", "Ürün", "Üretim (t)", "Direct SEE", "Indirect SEE", "Total SEE"]
    colx = [20*mm, 45*mm, 105*mm, 130*mm, 155*mm, 180*mm]
    for hx, hh in zip(colx, headers):
        c.drawString(hx, y, hh)
    y -= 4*mm
    c.line(20*mm, y, w-20*mm, y)
    y -= 6*mm

    c.setFont("Helvetica", 9)
    total_s1=0.0
    total_s2=0.0
    total_s3=0.0
    for p in products[:12]:
        total = (p.direct_see or 0) + (p.indirect_see or 0)
        c.drawString(colx[0], y, p.cn_code)
        c.drawString(colx[1], y, (p.product_name or "")[:35])
        c.drawRightString(colx[2]+15*mm, y, f"{(p.production_t or 0):.3f}")
        c.drawRightString(colx[3]+10*mm, y, f"{(p.direct_see or 0):.6f}")
        c.drawRightString(colx[4]+10*mm, y, f"{(p.indirect_see or 0):.6f}")
        c.drawRightString(colx[5]+10*mm, y, f"{total:.6f}")
        y -= 6*mm
        total_s1 += (p.production_t or 0)*(p.direct_see or 0)
        total_s2 += (p.production_t or 0)*(p.indirect_see or 0)

    y -= 6*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, "3. EMİSYON KIRILIMI")
    y -= 10*mm
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Scope 1 (Doğrudan): {total_s1:.3f} tCO2e")
    y -= 6*mm
    c.drawString(20*mm, y, f"Scope 2 (Elektrik): {total_s2:.3f} tCO2e")
    y -= 6*mm
    c.drawString(20*mm, y, f"Scope 3 (Hammadde): {total_s3:.3f} tCO2e (MVP: hesaplama eklenecek)")
    y -= 12*mm

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(20*mm, y, "Not: Bu PDF MVP çıktısıdır. Nihai sürümde tüm CBAM template sekmeleriyle birebir uyumlanacaktır.")
    c.showPage()
    c.save()
    return out_path
