from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")


class Target(Base):
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    ip = Column(String, nullable=False)
    interval = Column(Integer, default=60)
    ping_count = Column(Integer, default=4)
    last_loss = Column(Float, default=0.0)
    is_online = Column(Boolean, default=True)


class History(Base):
    __tablename__ = "history"
    
    id = Column(Integer, primary_key=True, index=True)
    target_name = Column(String, index=True, nullable=False)
    avg_latency = Column(Float, default=0.0)
    loss = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=False)


class Setting(Base):
    __tablename__ = "settings"
    
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)


class PDFReport(Base):
    __tablename__ = "pdf_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    generated_at = Column(DateTime, nullable=False)
    file_path = Column(String, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    target_name = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    loss = Column(Float, nullable=False)
    acknowledged = Column(Boolean, default=False)
