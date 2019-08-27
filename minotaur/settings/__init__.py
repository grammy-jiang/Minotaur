"""
Settings class

The class to save settings from the default, user, project, environment variables and
passing from command line arguments
"""
from __future__ import annotations

import heapq
import logging
import os
from collections import namedtuple
from collections.abc import MutableMapping
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from typing import (
    KT,
    VT,
    Any,
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

import yaml

from minotaur.exceptions import SettingsFrozenException

logging.basicConfig(format="%(asctime) %(levelname) %(message)s")
logger = logging.getLogger(__name__)  # pylint: disable = invalid-name

DEFAULT_SETTINGS = "minotaur.settings.default_settings"

SETTING_PRIORITIES: Dict[str, int] = {
    "default": 0,
    "user": 10,
    "project": 20,
    "env": 30,
    "cmd": 40,
}


def get_settings_priority(priority: str) -> int:
    """
    A function to get priority rank
    :param priority:
    :type priority
    :return:
    :rtype: int
    """
    try:
        return SETTING_PRIORITIES[priority]
    except KeyError as err:
        logger.exception("Setting priority %s is not existed.", priority)
        raise err


class SettingAttributes:
    """
    A container to save all priorities of a setting
    """

    setting_attributes = namedtuple("SettingAttributes", ["rank", "priority", "value"])

    def __init__(self, value: Any = None, priority: str = None):
        self._heap: List[Tuple[int, str, Any]] = []
        self.set(value, priority)

    def set(self, value: Any = None, priority: str = None) -> None:
        """
        Set a value with certain priority
        :param value:
        :type value: Any
        :param priority:
        :type priority: str
        :return:
        :rtype:
        """
        if not priority:
            return
        rank: int = get_settings_priority(priority)
        heapq.heappush(self._heap, self.setting_attributes(rank, priority, value))

    def _get(self, property_: str) -> Optional[Any]:
        max_values: List = heapq.nlargest(1, self._heap)

        return getattr(max_values[0], property_) if max_values else None

    def get(self) -> Any:
        """
        Get the highest priority setting value
        :return:
        :rtype: Any
        """
        return self._get("value")

    def get_priority(self) -> Optional[str]:
        """
        Get the highest priority
        :return:
        :rtype: Optional[str]
        """
        return self._get("priority")


class BaseSettings(MutableMapping):
    """
    A class with fundamental attributes of Settings
    """

    class FrozenCheck:  # pylint: disable = too-few-public-methods
        """
        A decorator for Settings frozen status check
        """

        def __call__(self, method):
            def frozen_check(base_settings: BaseSettings, *args, **kwargs):
                if base_settings.is_frozen():
                    raise SettingsFrozenException
                return method(base_settings, *args, **kwargs)

            return frozen_check

    frozen_check = FrozenCheck()

    def __init__(self, settings: Mapping = None, priority: str = "project"):
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
        """
        Get the highest priority of the given key
        :param k:
        :type k: KT
        :return:
        :rtype: Optional[str]
        """
        return self._data[k].get_priority()

    def is_frozen(self) -> bool:
        """
        Check if this instance is frozen
        :return:
        :rtype: bool
        """
        return self._frozen

    @frozen_check
    def set(self, key: KT, value: VT, priority: str = "project") -> None:
        """
        Set the value of the given key with the given priority
        :param key:
        :type key: KT
        :param value:
        :type value: VT
        :param priority:
        :type priority: str
        :return:
        """
        self._data.setdefault(key, SettingAttributes()).set(value, priority)

    @contextmanager
    def unfreeze(self) -> Generator[BaseSettings, None, None]:
        """
        A context manager to unfreeze this instance and keep the previous frozen status
        """
        status: bool = self._frozen
        self._frozen = False
        try:
            yield self
        finally:
            self._frozen = status

    @frozen_check
    def update(  # pylint: disable = arguments-differ
            self, values: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]], **kwargs: VT
    ) -> None:
        """
        Update this instance with the given values
        :param values:
        :type values: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]
        :param kwargs:
        :type kwargs: VT
        :return:
        """

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


def get_user_config(config: str = ".minotaur.yaml") -> Optional[Path]:
    """
    Get the user configuration file path
    :param config:
    :type config: str
    :return:
    :rtype: Optional[Path]
    """
    path_config: Path = Path.home() / config
    if path_config.is_file():
        return path_config
    logger.info("The user settings file %s does not exist.", path_config)
    return None


class Settings(BaseSettings):  # pylint: disable = too-many-ancestors
    """
    The class to store all settings
    """

    def __init__(
            self,
            settings: Mapping = None,
            priority: str = "project",
            config: str = ".minotaur.yaml",
    ):
        super(Settings, self).__init__(settings, priority)

        with self.unfreeze():
            self.update_from_module(DEFAULT_SETTINGS, "default")

            path_config: Path = get_user_config(config)
            if path_config:
                with path_config.open() as f:  # pylint: disable = invalid-name
                    dict_config: Dict[str, Any] = yaml.safe_load(f.read())
                self.update(dict_config, priority="user")

            for k, v in os.environ.items():  # pylint: disable = invalid-name
                if k.startswith("MINOTAUR_"):
                    self.set(k.replace("MINOTAUR_", "", 1), v, "env")

    def update_from_module(self, module: str, priority: str = "project") -> None:
        """
        Update this instance with the given module content
        :param module:
        :type module: str
        :param priority:
        :type priority: str
        :return:
        """
        module = import_module(module)
        for key in dir(module):
            if key.isupper():
                self.set(key, getattr(module, key), priority)
