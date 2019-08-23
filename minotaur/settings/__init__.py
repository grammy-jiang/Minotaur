from __future__ import annotations

import heapq
import logging
from collections import defaultdict, namedtuple
from collections.abc import MutableMapping
from contextlib import contextmanager
from typing import (
    KT,
    VT,
    Any,
    Callable,
    DefaultDict,
    Dict,
    Generator,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    VT_co,
)

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

    def _get(self, property_: str) -> Optional[Any]:
        max_values: List = heapq.nlargest(1, self._heap)

        return getattr(max_values[0], property_) if max_values else None

    def get(self) -> Any:
        return self._get("value")

    def get_priority(self) -> Optional[str]:
        return self._get("priority")


class BaseSettings(MutableMapping):
    def __init__(self, settings: Mapping = None, priority="project"):
        self._frozen: bool = False
        self._data: Dict[str, SettingAttributes] = {}
        if settings:
            self.update(settings, priority)
        self._frozen = True

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __delitem__(self, key: KT) -> None:
        del self._data[key]

    def __getitem__(self, key: KT) -> VT_co:
        return self.get(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: KT, value: VT) -> None:
        self.set(key, value)

    def get(self, key: KT, default: Any = None) -> Any:
        try:
            value: Any = self._data[key].get()
        except KeyError as err:
            if default is not None:
                return default
            raise err
        else:
            return value

    def get_priority(self, k: KT) -> Optional[str]:
        return self._data[k].get_priority()

    def is_frozen(self) -> bool:
        return self._frozen

    def set(self, key: KT, value: VT, priority: str = "project") -> None:
        self._data.setdefault(key, SettingAttributes()).set(value, priority)

    @contextmanager
    def unfreeze(self) -> Generator[BaseSettings, None, None]:
        status: bool = self._frozen
        self._frozen = False
        try:
            yield self
        finally:
            self._frozen = status

    def update(
        self, __m: Mapping[KT, VT], priority: str = "project", **kwargs: VT
    ) -> None:
        for key, value in __m.items():
            self._data.setdefault(key, SettingAttributes()).set(value, priority)
