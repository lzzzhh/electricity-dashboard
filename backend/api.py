"""REST API — facilities, timeseries, summary, stats, market data"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db, Facility, Measurement, MarketData

router = APIRouter()


@router.get("/api/facilities")
def get_facilities(db: Session = Depends(get_db)):
    """返回所有 facility metadata"""
    facilities = db.query(Facility).all()
    return [
        {
            "facility_id": f.facility_id,
            "facility_name": f.facility_name,
            "latitude": f.latitude,
            "longitude": f.longitude,
            "station_type": f.station_type,
            "network_region": f.network_region,
            "fuel_tech": f.fuel_tech,
        }
        for f in facilities
    ]


@router.get("/api/facilities/latest")
def get_latest(db: Session = Depends(get_db)):
    """返回每个 facility 的最新 power + emissions（仅返回有元数据的 facility）"""
    # 子查询：每个 facility 的最大 timestamp
    subq = (
        db.query(
            Measurement.facility_id,
            func.max(Measurement.timestamp).label("max_ts"),
        )
        .join(Facility, Measurement.facility_id == Facility.facility_id)  # 只取有元数据的
        .group_by(Measurement.facility_id)
        .subquery()
    )
    rows = (
        db.query(Measurement)
        .join(subq, (Measurement.facility_id == subq.c.facility_id) & (Measurement.timestamp == subq.c.max_ts))
        .all()
    )
    return [
        {
            "facility_id": m.facility_id,
            "timestamp": m.timestamp,
            "power_mw": m.power_mw,
            "emissions_tco2e": m.emissions_tco2e,
        }
        for m in rows
    ]


@router.get("/api/facilities/{facility_id}/timeseries")
def get_timeseries(
    facility_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """返回指定 facility 的时间序列"""
    query = db.query(Measurement).filter(Measurement.facility_id == facility_id)
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    measurements = query.order_by(Measurement.timestamp).all()
    return [
        {
            "timestamp": m.timestamp,
            "power_mw": m.power_mw,
            "emissions_tco2e": m.emissions_tco2e,
        }
        for m in measurements
    ]


@router.get("/api/summary")
def get_summary(
    group_by: str = Query("region", pattern="^(region|fuel_tech|facility)$"),
    metric: str = Query("power_mw", pattern="^(power_mw|emissions_tco2e)$"),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """按 region/fuel_tech/facility 聚合"""
    col = getattr(Measurement, metric)

    if group_by == "facility":
        query = db.query(Measurement.facility_id, func.avg(col).label("value")).group_by(
            Measurement.facility_id
        )
    else:
        # "region" 映射到 Facility.network_region
        field_name = "network_region" if group_by == "region" else group_by
        field = getattr(Facility, field_name)
        query = (
            db.query(field, func.avg(col).label("value"))
            .join(Facility, Measurement.facility_id == Facility.facility_id)
            .group_by(field)
        )

    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)

    return [{"group": row[0], "value": round(float(row[1]), 2)} for row in query.all()]


@router.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """返回系统统计（从数据库查询）"""
    facility_count = db.query(Facility).count()
    message_count = db.query(Measurement).join(Facility, Measurement.facility_id == Facility.facility_id).count()
    market_count = db.query(MarketData).count()
    last_measurement = (
        db.query(Measurement.timestamp)
        .join(Facility, Measurement.facility_id == Facility.facility_id)
        .order_by(Measurement.timestamp.desc())
        .first()
    )
    last_market = db.query(MarketData.timestamp).order_by(MarketData.timestamp.desc()).first()
    return {
        "facilities_total": facility_count,
        "measurements_total": message_count,
        "market_records": market_count,
        "last_measurement_ts": last_measurement[0] if last_measurement else None,
        "last_market_ts": last_market[0] if last_market else None,
    }


# ══════════════════════════════════════════
# Market data endpoints
# ══════════════════════════════════════════

@router.get("/api/market/regions")
def get_regions(db: Session = Depends(get_db)):
    """返回所有 NEM 区域"""
    regions = db.query(MarketData.region).distinct().all()
    return [r[0] for r in regions]


@router.get("/api/market/latest")
def get_market_latest(db: Session = Depends(get_db)):
    """返回每个区域的最新电价 + 需求"""
    subq = (
        db.query(
            MarketData.region,
            func.max(MarketData.timestamp).label("max_ts"),
        )
        .group_by(MarketData.region)
        .subquery()
    )
    rows = (
        db.query(MarketData)
        .join(subq, (MarketData.region == subq.c.region) & (MarketData.timestamp == subq.c.max_ts))
        .all()
    )
    return [
        {
            "region": m.region,
            "timestamp": m.timestamp,
            "price_aud_mwh": m.price_aud_mwh,
            "demand_mw": m.demand_mw,
        }
        for m in rows
    ]


@router.get("/api/market/timeseries")
def get_market_timeseries(
    region: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """返回指定区域的电价 + 需求时间序列。region=None 时返回所有区域汇总"""
    query = db.query(MarketData)
    if region:
        query = query.filter(MarketData.region == region)
    if start_time:
        query = query.filter(MarketData.timestamp >= start_time)
    if end_time:
        query = query.filter(MarketData.timestamp <= end_time)
    rows = query.order_by(MarketData.region, MarketData.timestamp).all()
    return [
        {
            "region": m.region,
            "timestamp": m.timestamp,
            "price_aud_mwh": m.price_aud_mwh,
            "demand_mw": m.demand_mw,
        }
        for m in rows
    ]
