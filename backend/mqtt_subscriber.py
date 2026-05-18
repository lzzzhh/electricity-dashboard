"""MQTT Subscriber — paho-mqtt 订阅 + 适配 + 存储"""

import json
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, RawMQTTMessage, Measurement, MarketData, Facility
from .adapter import adapter

# 全局最新状态缓存
latest_state: dict[str, dict] = {}

# 统计
stats = {
    "messages_total": 0,
    "messages_error": 0,
    "last_update": None,
}

# NEM facility 坐标参考（OpenElectricity 真实坐标 + 合理估算）
FACILITY_COORDS = {
    "ADPBA1":   (-35.10, 138.48), "ADPBA1G":  (-35.10, 138.48),
    "ADPBA1L":  (-35.10, 138.48), "ADPPV1":   (-35.10, 138.48),
    "ANGAST1":  (-34.51, 139.05), "ARWF1":    (-37.28, 142.93),
    "BARCALDN": (-23.55, 145.29), "BDL01":    (-37.82, 147.63),
    "BDL02":    (-37.82, 147.63), "BW01":     (-32.40, 150.88),
    "BW02":     (-32.40, 150.88), "BW03":     (-32.40, 150.88),
    "BW04":     (-32.40, 150.88),
}


def on_connect(client, userdata, flags, rc):
    """MQTT 连接成功回调"""
    if rc == 0:
        print(f"[MQTT] Connected to {settings.MQTT_HOST}:{settings.MQTT_PORT}")
        client.subscribe(settings.MQTT_TOPIC)
        print(f"[MQTT] Subscribed to {settings.MQTT_TOPIC}")
    else:
        print(f"[MQTT] Connection failed: rc={rc}")


def on_message(client, userdata, msg):
    """收到 MQTT 消息回调 — 解析 facility power/emissions + market price/demand"""
    try:
        raw_payload = msg.payload.decode("utf-8")
        raw_json = json.loads(raw_payload)

        # 1. 标准化
        canonical = adapter.normalize(raw_json)

        # 2. 存入数据库
        db: Session = SessionLocal()
        try:
            # 2a. 存档原始消息
            raw_record = RawMQTTMessage(topic=msg.topic, payload=raw_payload)
            db.add(raw_record)

            # 2b. 存储 facility 测量数据
            measurement = Measurement(
                timestamp=canonical["timestamp"],
                facility_id=canonical["facility_id"],
                power_mw=canonical["power_mw"],
                emissions_tco2e=canonical["emissions_tco2e"],
            )
            db.add(measurement)

            # 2c. 存储市场数据（电价 + 需求），按 (region, timestamp) 去重
            network_region = canonical.get("network_region")
            if network_region:
                price = raw_json.get("price_aud_per_mwh")
                demand = raw_json.get("demand_mw")
                if price is not None and demand is not None:
                    ts = canonical["timestamp"]
                    existing_market = db.query(MarketData).filter(
                        MarketData.region == network_region,
                        MarketData.timestamp == ts,
                    ).first()
                    if not existing_market:
                        db.add(MarketData(
                            timestamp=ts,
                            region=network_region,
                            price_aud_mwh=float(price),
                            demand_mw=float(demand),
                        ))

            # 2d. 动态注册新出现的 facility（当 unit_code 不在 facilities 表时自动添加）
            fid = canonical["facility_id"]
            existing_fac = db.query(Facility).filter(Facility.facility_id == fid).first()
            if not existing_fac:
                lat, lon = FACILITY_COORDS.get(fid, (0.0, 0.0))
                db.add(Facility(
                    facility_id=fid,
                    facility_name=canonical.get("facility_name") or fid,
                    latitude=lat,
                    longitude=lon,
                    station_type="Power Station",
                    network_region=canonical.get("network_region") or "",
                    fuel_tech=canonical.get("fuel_tech") or "",
                ))

            db.commit()

            # 3. 更新内存缓存
            latest_state[canonical["facility_id"]] = canonical

            # 4. 更新统计
            stats["messages_total"] += 1
            stats["last_update"] = datetime.now(timezone.utc).isoformat()

        except Exception:
            db.rollback()
            stats["messages_error"] += 1
            raise
        finally:
            db.close()

    except Exception as e:
        stats["messages_error"] += 1
        print(f"[MQTT] Error processing message: {e}")


def start_subscriber():
    """启动 MQTT subscriber（在 FastAPI 启动时调用），支持重连"""
    import time
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    if settings.MQTT_USERNAME:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

    # 最多重试 5 次
    for attempt in range(5):
        try:
            client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
            client.loop_start()
            print(f"[MQTT] Connected to {settings.MQTT_HOST}:{settings.MQTT_PORT}")
            return client
        except ConnectionRefusedError:
            print(f"[MQTT] Connection refused, retrying ({attempt+1}/5)...")
            time.sleep(2)

    print("[MQTT] Could not connect after 5 attempts — running without MQTT")
    return client  # Return client anyway, API still works
