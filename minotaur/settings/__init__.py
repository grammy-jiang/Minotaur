from __future__ import annotations

import heapq
import logging
from collections import namedtuple
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SETTING_PRIORITIES: Dict[str, int] = {
    "default": 0,
    "user": 10,
    "project": 20,
    "env": 30,
    "cmd": 40,
}


def get_settings_priority(priority: str) -> int:
    try:
        return SETTING_PRIORITIES[priority]
    except KeyError as err:
        logger.error("Setting priority %s is not existed", priority)
        raise err


class SettingAttributes:
    setting_attributes = namedtuple("SettingAttributes", ["rank", "priority", "value"])

    def __init__(self, value: Any = None, priority: str = None):
        self._heap: List = []
        self.set(value, priority)

    def set(self, value: Any = None, priority: str = None) -> None:
        if not priority:
            return
        rank: int = get_settings_priority(priority)
        heapq.heappush(self._heap, self.setting_attributes(rank, priority, value))

    def _get(self, property_: str):
        max_values: List = heapq.nlargest(1, self._heap)
        if max_values:
            return getattr(max_values[0], property_)
        return

    def get(self) -> Any:
        return self._get("value")

    def get_priority(self) -> Optional[str]:
        return self._get("priority")
