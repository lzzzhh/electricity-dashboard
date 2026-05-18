"""JSON 适配层 — 外部 MQTT JSON → Canonical Schema"""

import json
from typing import Any, Optional
from datetime import datetime, timezone
from .config import load_mapping

# Canonical Schema 字段列表
CANONICAL_FIELDS = [
    "timestamp",
    "facility_id",
    "facility_name",
    "network_region",
    "fuel_tech",
    "power_mw",
    "emissions_tco2e",
]

REQUIRED_FIELDS = {"timestamp", "facility_id", "power_mw", "emissions_tco2e"}


class Adapter:
    """灵活的 JSON 字段适配器"""

    def __init__(self):
        config = load_mapping()
        self.field_map = config.get("mapping", {})
        self.unit_conversion = config.get("unit_conversion", {})
        self._build_lookup()

    def _build_lookup(self):
        """构建反向查找表：外部字段名 → canonical 字段名"""
        self.lookup = {}
        for canonical, aliases in self.field_map.items():
            for alias in aliases:
                self.lookup[alias.lower()] = canonical

    def normalize(self, raw_json: dict) -> dict:
        """
        将外部 MQTT JSON 转换为 Canonical Schema。

        Args:
            raw_json: 队友发来的原始 MQTT payload（dict）

        Returns:
            标准化后的 dict（Canonical Schema）
        """
        # 先用小写 key 做匹配（大小写不敏感）
        raw_lower = {k.lower(): v for k, v in raw_json.items()}

        result = {}
        for canonical in CANONICAL_FIELDS:
            for ext_field, value in raw_lower.items():
                mapped = self.lookup.get(ext_field)
                if mapped == canonical and value is not None:
                    result[canonical] = value
                    break

        # 必填字段校验
        missing = REQUIRED_FIELDS - set(result.keys())
        if missing:
            raise ValueError(
                f"Canonical Schema 缺少必填字段: {missing}. "
                f"Raw keys: {list(raw_json.keys())}"
            )

        # 时间戳标准化
        result["timestamp"] = self._normalize_timestamp(result["timestamp"])

        # 单位转换
        if "power" in raw_lower.get("unit", "").lower() and "kw" in raw_lower.get("unit", "").lower():
            result["power_mw"] = float(result["power_mw"]) * self.unit_conversion.get("power_kw_to_mw", 0.001)
        result["power_mw"] = float(result["power_mw"])
        result["emissions_tco2e"] = float(result["emissions_tco2e"])

        return result

    def _normalize_timestamp(self, ts: Any) -> str:
        """标准化时间戳为 ISO 8601"""
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        return str(ts)


# 全局单例
adapter = Adapter()
