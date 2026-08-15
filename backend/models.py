from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
from database import Base

class ReferenceRange(Base):
    __tablename__ = "reference_ranges"

    id = Column(Integer, primary_key=True, index=True)
    biomarker_name = Column(String, unique=True, index=True, nullable=False)
    alias_names = Column(String, nullable=True)  # Comma-separated strings for parser mapping
    min_normal = Column(Float, nullable=False)
    max_normal = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    panel_name = Column(String, nullable=False)  # E.g., "CBC", "Blood Sugar", "Lipid Profile"
    description = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Onboarding Profile details
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    biological_sex = Column(String, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    chronic_conditions = Column(String, nullable=True)  # Comma-separated list
    primary_health_goal = Column(String, nullable=True)
    is_onboarded = Column(Boolean, default=False, nullable=False)

    reports = relationship("UploadedReport", back_populates="user", cascade="all, delete-orphan")

class UploadedReport(Base):
    __tablename__ = "uploaded_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    patient_summary = Column(String, nullable=True)
    disease_risks = Column(String, nullable=True)  # JSON-serialized list of risks
    language = Column(String, default="English", nullable=False)

    user = relationship("User", back_populates="reports")
    metrics = relationship("ReportMetric", back_populates="report", cascade="all, delete-orphan")

class ReportMetric(Base):
    __tablename__ = "report_metrics"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("uploaded_reports.id"), nullable=False)
    biomarker_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    min_normal = Column(Float, nullable=False)
    max_normal = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # "Low", "Normal", "High"
    confidence = Column(Float, default=0.95, nullable=True)
    is_low_confidence = Column(Boolean, default=False, nullable=True)
    is_critical = Column(Boolean, default=False, nullable=True)
    critical_reason = Column(String, nullable=True)
    description = Column(String, nullable=True)

    report = relationship("UploadedReport", back_populates="metrics")

