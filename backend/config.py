"""配置文件加载 — 读 .env + mqtt_mapping.yaml"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env
load_dotenv(BASE_DIR / ".env")


class Settings:
    # MQTT
    MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "electricity/facility/stream")
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/electricity.db")

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:8501")

    # Mapping config
    MAPPING_FILE: Path = BASE_DIR / "mqtt_mapping.yaml"


settings = Settings()


def load_mapping() -> dict:
    """加载字段映射配置"""
    with open(settings.MAPPING_FILE, "r") as f:
        config = yaml.safe_load(f)
    return config
