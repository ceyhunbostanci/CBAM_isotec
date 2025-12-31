import os
from datetime import date, datetime
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .db import SessionLocal, engine, Base
from .models import User, Period, Energy, Product, Upload
from .auth import hash_password, verify_password, sign_session, current_user_id
from .invoice_parse import extract_text_from_pdf, guess_energy_from_text
from .cbam_excel import fill_cbam_template
from .pdf_report import build_pdf

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "change-me")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/data/uploads")
TEMPLATE_PATH = os.getenv("CBAM_TEMPLATE_PATH", "/app/data/templates/cbam_template.xlsx")

os.makedirs(UPLOAD_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ISOTEC CBAM Platform (MVP)")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_user(request: Request, db: Session) -> User:
    uid = current_user_id(request, APP_SECRET_KEY)
    if not uid:
        raise HTTPException(status_code=401)
    user = db.get(User, uid)
    if not user or not user.is_active:
        raise HTTPException(status_code=401)
    return user

def seed_admin(db: Session):
    admin = db.query(User).filter(User.email == "admin@isotec.local").first()
    if not admin:
        admin = User(
            email="admin@isotec.local",
            password_hash=hash_password("ChangeMe123!"),
            full_name="Admin",
            role="admin",
        )
        db.add(admin)
        db.commit()

@app.on_event("startup")
def _startup():
    with SessionLocal() as db:
        seed_admin(db)

@app.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db)):
    try:
        require_user(request, db)
        return RedirectResponse("/dashboard", status_code=302)
    except Exception:
        return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Hatalı e-posta veya şifre."}, status_code=400)
    resp = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie("session", sign_session(APP_SECRET_KEY, user.id), httponly=True, samesite="lax")
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("session")
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    periods = db.query(Period).order_by(Period.year.desc(), Period.quarter.desc()).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "periods": periods})

@app.post("/period/create")
def create_period(request: Request,
                  year: int = Form(...),
                  quarter: int = Form(...),
                  start_date: str = Form(...),
                  end_date: str = Form(...),
                  db: Session = Depends(get_db)):
    user = require_user(request, db)
    p = Period(
        year=year,
        quarter=quarter,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
    )
    db.add(p)
    db.commit()
    # attach energy row
    e = Energy(period_id=p.id)
    db.add(e)
    db.commit()
    return RedirectResponse(f"/period/{p.id}", status_code=302)

@app.get("/period/{period_id}", response_class=HTMLResponse)
def period_view(period_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)
    energy = period.energy
    products = period.products
    uploads = period.uploads
    return templates.TemplateResponse("period.html", {"request": request, "user": user, "period": period, "energy": energy, "products": products, "uploads": uploads})

@app.post("/period/{period_id}/installation")
def update_installation(period_id: int, request: Request,
                        installation_name: str = Form(...),
                        installation_name_en: str = Form(...),
                        street_number: str = Form(...),
                        economic_activity: str = Form(...),
                        post_code: str = Form(""),
                        po_box: str = Form(""),
                        city: str = Form(...),
                        country: str = Form(...),
                        unlocode: str = Form(...),
                        latitude: str = Form(...),
                        longitude: str = Form(...),
                        data_quality: str = Form(""),
                        default_values_justification: str = Form(""),
                        quality_assurance: str = Form(""),
                        db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)
    period.installation_name = installation_name
    period.installation_name_en = installation_name_en
    period.street_number = street_number
    period.economic_activity = economic_activity
    period.post_code = post_code
    period.po_box = po_box
    period.city = city
    period.country = country
    period.unlocode = unlocode
    period.latitude = latitude
    period.longitude = longitude
    period.data_quality = data_quality
    period.default_values_justification = default_values_justification
    period.quality_assurance = quality_assurance
    db.commit()
    return RedirectResponse(f"/period/{period_id}", status_code=302)

@app.post("/period/{period_id}/energy")
def update_energy(period_id: int, request: Request,
                  electricity_kwh: float = Form(0.0),
                  natural_gas_sm3: float = Form(0.0),
                  db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)
    if not period.energy:
        period.energy = Energy(period_id=period.id)
        db.add(period.energy)
    period.energy.electricity_kwh = electricity_kwh
    period.energy.natural_gas_sm3 = natural_gas_sm3
    period.energy.updated_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/period/{period_id}#energy", status_code=302)

@app.post("/period/{period_id}/product/add")
def add_product(period_id: int, request: Request,
                cn_code: str = Form(...),
                cn_name: str = Form(""),
                aggregated_category: str = Form(""),
                product_name: str = Form(...),
                production_t: float = Form(0.0),
                direct_see: float = Form(0.0),
                indirect_see: float = Form(0.0),
                db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)
    p = Product(period_id=period.id, cn_code=cn_code, cn_name=cn_name, aggregated_category=aggregated_category,
                product_name=product_name, production_t=production_t, direct_see=direct_see, indirect_see=indirect_see)
    db.add(p)
    db.commit()
    return RedirectResponse(f"/period/{period_id}#products", status_code=302)

@app.post("/period/{period_id}/upload")
async def upload_file(period_id: int, request: Request,
                      kind: str = Form("evidence"),
                      file: UploadFile = File(...),
                      db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)

    # store
    safe_name = file.filename.replace("..","").replace("/","_").replace("\\","_")
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    stored = os.path.join(UPLOAD_DIR, f"{period_id}_{kind}_{ts}_{safe_name}")
    content = await file.read()
    with open(stored, "wb") as f:
        f.write(content)

    up = Upload(period_id=period_id, kind=kind, original_name=file.filename, stored_path=stored)
    db.add(up)
    db.commit()

    # auto-parse for PDF invoices (MVP)
    if kind in ("electricity", "gas") and stored.lower().endswith(".pdf"):
        txt = extract_text_from_pdf(stored)
        kwh, gas = guess_energy_from_text(txt)
        if period.energy is None:
            period.energy = Energy(period_id=period.id)
            db.add(period.energy)
        if kwh and kind == "electricity":
            period.energy.electricity_kwh = float(kwh)
        if gas and kind == "gas":
            period.energy.natural_gas_sm3 = float(gas)
        db.commit()

    return RedirectResponse(f"/period/{period_id}#uploads", status_code=302)

@app.get("/period/{period_id}/export/excel")
def export_excel(period_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)
    products = period.products

    out_dir = "/app/data/exports"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"ISOTEC_CBAM_{period.year}_Q{period.quarter}.xlsx")
    fill_cbam_template(TEMPLATE_PATH, period, products, out_path)
    return FileResponse(out_path, filename=os.path.basename(out_path))

@app.get("/period/{period_id}/export/pdf")
def export_pdf(period_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    period = db.get(Period, period_id)
    if not period:
        raise HTTPException(404)
    products = period.products
    energy = period.energy

    out_dir = "/app/data/exports"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"ISOTEC_CBAM_{period.year}_Q{period.quarter}.pdf")
    build_pdf(out_path, period, products, energy)
    return FileResponse(out_path, filename=os.path.basename(out_path))
