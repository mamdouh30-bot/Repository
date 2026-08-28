
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    whatsapp_token = Column(Text, nullable=True)
    whatsapp_phone_id = Column(String, nullable=True)
    telegram_token = Column(Text, nullable=True)
    company_info = Column(Text, default="")
    products_info = Column(Text, default="")
    plan = Column(String, default="basic")  # basic, growth, empire
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    is_trial = Column(Boolean, default=True)
    messages_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    trial_ends_at = Column(DateTime, nullable=True)

class MessageLog(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True)
    platform = Column(String)
    customer_id = Column(String)
    inbound = Column(Text)
    outbound = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
