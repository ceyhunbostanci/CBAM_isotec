from sqlalchemy import Column, Integer, String, Date, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="user")  # admin | user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Period(Base):
    __tablename__ = "periods"
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)  # 1..4
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Installation info (minimum set; expandable)
    installation_name = Column(String, default="ISOTEC Enerji San. ve Tic. Ltd. Şti.")
    installation_name_en = Column(String, default="ISOTEC Enerji San. ve Tic. Ltd. Şti.")
    street_number = Column(String, default="Çerkeşli OSB")
    economic_activity = Column(String, default="Solar mounting systems manufacturing")
    post_code = Column(String, default="")
    po_box = Column(String, default="")
    city = Column(String, default="Dilovası, Kocaeli")
    country = Column(String, default="Turkey")
    unlocode = Column(String, default="TRIST")
    latitude = Column(String, default="40.9")
    longitude = Column(String, default="29.1")

    # Quality statements (CBAM template C_Emissions&Energy)
    data_quality = Column(Text, default="")
    default_values_justification = Column(Text, default="")
    quality_assurance = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)

    energy = relationship("Energy", back_populates="period", uselist=False, cascade="all, delete-orphan")
    products = relationship("Product", back_populates="period", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="period", cascade="all, delete-orphan")

class Energy(Base):
    __tablename__ = "energy"
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False, unique=True)
    electricity_kwh = Column(Float, default=0.0)
    natural_gas_sm3 = Column(Float, default=0.0)
    scope1_tco2e = Column(Float, default=0.0)
    scope2_tco2e = Column(Float, default=0.0)
    scope3_tco2e = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("Period", back_populates="energy")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    cn_code = Column(String, nullable=False)
    cn_name = Column(String, default="")
    aggregated_category = Column(String, default="")  # Iron or steel products / Aluminium products / ...
    product_name = Column(String, nullable=False)
    production_t = Column(Float, default=0.0)  # tons in the quarter
    direct_see = Column(Float, default=0.0)    # tCO2e/t
    indirect_see = Column(Float, default=0.0)  # tCO2e/t

    period = relationship("Period", back_populates="products")

class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    kind = Column(String, default="evidence")  # electricity | gas | evidence
    original_name = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    period = relationship("Period", back_populates="uploads")
