"""Assignment 1 → Assignment 2 数据迁移
从 DuckDB 读取 A1 数据，写入 SQLite (electricity.db)

Usage:
    python -m backend.migrate_a1
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import (
    SessionLocal,
    init_db,
    IntegratedEnergyStateYear,
    RenewableProject,
)


def safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def migrate_state_year(duck_path: Path, db: Session) -> int:
    """迁移 integrated_energy_state_year"""
    con = duckdb.connect(str(duck_path), read_only=True)
    db.query(IntegratedEnergyStateYear).delete()

    rows = con.execute(
        "SELECT state, year, total_generation_mwh, total_emissions_tco2e, "
        "total_businesses, small_businesses, renewable_project_count, "
        "total_renewable_capacity_mw "
        "FROM integrated_energy_state_year ORDER BY state, year"
    ).fetchall()

    for row in rows:
        db.add(IntegratedEnergyStateYear(
            state=str(row[0]).strip(),
            year=int(row[1]),
            total_generation_mwh=safe_float(row[2]),
            total_emissions_tco2e=safe_float(row[3]),
            total_businesses=safe_float(row[4]),
            small_businesses=safe_float(row[5]),
            renewable_project_count=safe_float(row[6]),
            total_renewable_capacity_mw=safe_float(row[7]),
        ))

    db.commit()
    con.close()
    return len(rows)


def migrate_renewable_projects(duck_path: Path, db: Session) -> int:
    """迁移 geocoded renewable projects"""
    con = duckdb.connect(str(duck_path), read_only=True)
    db.query(RenewableProject).delete()

    rows = con.execute(
        "SELECT project_name, state, postcode, capacity_mw, fuel_source, "
        "project_date, status, nominatim_fallback_latitude, "
        "nominatim_fallback_longitude, nominatim_fallback_display_name, "
        "nominatim_fallback_match_quality "
        "FROM renewable_projects_geocoded_nominatim_fallback "
        "ORDER BY state, project_name"
    ).fetchall()

    for row in rows:
        db.add(RenewableProject(
            project_name=str(row[0]) if row[0] else None,
            state=str(row[1]).strip() if row[1] else None,
            postcode=safe_float(row[2]),
            capacity_mw=safe_float(row[3]),
            fuel_source=str(row[4]) if row[4] else None,
            project_date=str(row[5]) if row[5] else None,
            status=str(row[6]) if row[6] else None,
            latitude=safe_float(row[7]),
            longitude=safe_float(row[8]),
            display_name=str(row[9]) if row[9] else None,
            match_quality=str(row[10]) if row[10] else None,
        ))

    db.commit()
    con.close()
    return len(rows)


def run():
    duck_path = settings.DUCKDB_ASSIGNMENT1_PATH
    if not duck_path.exists():
        print(f"[migrate] DuckDB not found: {duck_path}")
        return

    init_db()
    db = SessionLocal()
    try:
        n1 = migrate_state_year(duck_path, db)
        n2 = migrate_renewable_projects(duck_path, db)
        print(f"[migrate] Done: {n1} state-year rows + {n2} projects")
    finally:
        db.close()


if __name__ == "__main__":
    run()
