"""FastAPI 主入口 — MQTT Subscriber + REST API"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db, SessionLocal, Facility
from .mqtt_subscriber import start_subscriber
from .api import router


def seed_facilities():
    """如果 facilities 表为空，导入 NEM dispatch unit 元数据"""
    db = SessionLocal()
    try:
        count = db.query(Facility).count()
        if count == 0:
            facilities = [
                ("ADPBA1",   -34.82, 138.52,  "Adelaide Desalination Plant B1",   "SA",  "load"),
                ("ADPBA1G",  -34.82, 138.52,  "Adelaide Desalination Plant B1G",  "SA",  "load"),
                ("ADPBA1L",  -34.82, 138.52,  "Adelaide Desalination Plant B1L",  "SA",  "load"),
                ("ADPPV1",   -34.78, 138.55,  "Adelaide Solar PV",                "SA",  "solar"),
                ("ANGAST1",  -34.51, 139.05,  "Angaston Gas Turbine",             "SA",  "gas_ocgt"),
                ("ARWF1",    -37.28, 143.02,  "Ararat Wind Farm",                 "VIC", "wind"),
                ("BARCALDN", -23.55, 145.29,  "Barcaldine Solar Farm",            "QLD", "solar"),
                ("BDL01",    -32.48, 149.04,  "Bodangora Wind Farm Unit 1",       "NSW", "wind"),
                ("BDL02",    -32.48, 149.04,  "Bodangora Wind Farm Unit 2",       "NSW", "wind"),
                ("BW01",     -36.85, 149.38,  "Boco Rock Wind Farm Unit 1",       "NSW", "wind"),
                ("BW02",     -36.85, 149.38,  "Boco Rock Wind Farm Unit 2",       "NSW", "wind"),
                ("BW03",     -36.85, 149.38,  "Boco Rock Wind Farm Unit 3",       "NSW", "wind"),
                ("BW04",     -36.85, 149.38,  "Boco Rock Wind Farm Unit 4",       "NSW", "wind"),
            ]
            for fid, lat, lon, name, region, fuel in facilities:
                f = Facility(facility_id=fid, facility_name=name, latitude=lat, longitude=lon,
                             station_type="Power Station", network_region=region, fuel_tech=fuel)
                db.add(f)
            db.commit()
            print(f"[Backend] Seeded {len(facilities)} facilities")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭时的生命周期管理"""
    # 启动：初始化数据库 + MQTT subscriber（facility 由 MQTT 消息动态注册）
    print("[Backend] Initializing database...")
    init_db()
    # seed_facilities()  # 已弃用：facility 元数据由 MQTT publisher 推送时自动注册
    try:
        print("[Backend] Starting MQTT subscriber...")
        start_subscriber()
    except Exception as e:
        print(f"[Backend] MQTT subscriber unavailable: {e}")
        print("[Backend] Running in offline mode (CSV data only)")
    print(f"[Backend] API ready at http://{settings.API_HOST}:{settings.API_PORT}")
    yield
    # 关闭（不需要额外操作）


app = FastAPI(title="Electricity Dashboard Backend", lifespan=lifespan)

# CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
def root():
    return {"app": "Electricity Dashboard Backend", "status": "running"}
