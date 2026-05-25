"""数据库模型 — SQLAlchemy + SQLite"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Index, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

from .config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Facility(Base):
    """发电单元元数据（NEM dispatch unit）"""
    __tablename__ = "facilities"

    facility_id = Column(String, primary_key=True)
    facility_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    station_type = Column(String)
    network_region = Column(String)
    fuel_tech = Column(String)


class RawMQTTMessage(Base):
    """原始 MQTT 消息存档（调试/回放）"""
    __tablename__ = "raw_mqtt_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String)
    payload = Column(String)  # JSON string
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Measurement(Base):
    """标准化时间序列数据（发电出力 + 碳排放）"""
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    facility_id = Column(String, ForeignKey("facilities.facility_id"), nullable=False)
    power_mw = Column(Float)
    emissions_tco2e = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("idx_measurements_facility_time", "facility_id", "timestamp"),)


class MarketData(Base):
    """区域市场数据（电价 + 需求）"""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    region = Column(String, nullable=False)
    price_aud_mwh = Column(Float)
    demand_mw = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_market_region_time", "region", "timestamp"),
        Index("idx_market_region_time_unique", "region", "timestamp", unique=True),
    )


class IntegratedEnergyStateYear(Base):
    """Assignment 1 集成数据 — 州/年级别的能源+经济汇总"""
    __tablename__ = "integrated_energy_state_year"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(4), nullable=False)
    year = Column(Integer, nullable=False)
    total_generation_mwh = Column(Float)
    total_emissions_tco2e = Column(Float)
    total_businesses = Column(Float)  # DuckDB BIGINT → SQLite REAL (NaN-safe)
    small_businesses = Column(Float)
    renewable_project_count = Column(Float)
    total_renewable_capacity_mw = Column(Float)

    __table_args__ = (
        Index("idx_integrated_state_year", "state", "year", unique=True),
    )


class RenewableProject(Base):
    """Assignment 1 可再生能源项目（含地理编码）"""
    __tablename__ = "renewable_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String)
    state = Column(String(4))
    postcode = Column(Float)
    capacity_mw = Column(Float)
    fuel_source = Column(String)
    project_date = Column(String)
    status = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    display_name = Column(String)
    match_quality = Column(String)

    __table_args__ = (
        Index("idx_renewable_state", "state"),
        Index("idx_renewable_status", "status"),
    )


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
