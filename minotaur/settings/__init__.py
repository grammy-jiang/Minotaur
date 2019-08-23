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
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    VT_co,
)

from minotaur.exceptions import SettingsFrozenException

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
    class FrozenCheck:
        def __call__(self, method):
            def frozen_check(base_settings: BaseSettings, *args, **kwargs):
                if base_settings.is_frozen():
                    raise SettingsFrozenException
                return method(base_settings, *args, **kwargs)

            return frozen_check

    frozen_check = FrozenCheck()

    def __init__(self, settings: Mapping = None, priority="project"):
        self._frozen: bool = False
        self._data: Dict[str, SettingAttributes] = {}
        if settings:
            self.update(settings, priority=priority)
        self._frozen = True

    def __contains__(self, key: object) -> bool:
        return key in self._data

    @frozen_check
    def __delitem__(self, key: KT) -> None:
        del self._data[key]

    def __getitem__(self, key: KT) -> VT_co:
        return self.get(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @frozen_check
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

    @frozen_check
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

    @frozen_check
    def update(
        self, values: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]], **kwargs: VT
    ) -> None:
        def iter_values(
            values_: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]
        ) -> Iterable[Tuple[str, Any]]:
            if isinstance(values_, Mapping):
                return values_.items()
            if isinstance(values_, Iterable):
                return values_
            raise TypeError

        for key, value in iter_values(values):
            self._data.setdefault(key, SettingAttributes()).set(
                value, kwargs.get("priority", "project")
            )
