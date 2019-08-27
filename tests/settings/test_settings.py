import os
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional
from unittest.case import TestCase
from unittest.mock import patch

from minotaur.exceptions import SettingsFrozenException
from minotaur.settings import (
    SETTING_PRIORITIES,
    BaseSettings,
    SettingAttributes,
    Settings,
    get_settings_priority,
    get_user_config,
    logger,
)


class SettingsFunctionsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.setting_default: str = "default"
        cls.setting_customize: str = "customize"

    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        del self.tempdir

    def test_get_settings_priority(self) -> None:
        priority: int = get_settings_priority(self.setting_default)
        self.assertEqual(priority, SETTING_PRIORITIES[self.setting_default])

        with self.assertLogs(logger, "ERROR"):
            with self.assertRaises(KeyError):
                priority: int = get_settings_priority(self.setting_customize)
        # TODO: add assert for logger message

        SETTING_PRIORITIES[self.setting_customize]: int = 25
        priority: int = get_settings_priority(self.setting_customize)
        self.assertEqual(priority, SETTING_PRIORITIES[self.setting_customize])

    def test_get_user_config(self):
        # not find the user config
        with patch.object(
            Path, "home", return_value=Path(self.tempdir.name)
        ), self.assertLogs(logger, "INFO") as cm:
            user_config: Optional[Path] = get_user_config()
            self.assertEqual(
                cm.output,
                [
                    f"INFO:minotaur.settings:The user settings file {Path.home() / '.minotaur.yaml'} does not exist."
                ],
            )

        # find the user config
        with patch.object(
            Path, "home", return_value=Path(os.getcwd()) / "tests/samples"
        ):
            user_config: Optional[Path] = get_user_config()
            self.assertEqual(user_config, Path.home() / ".minotaur.yaml")


class SettingAttributesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings_default_priority: str = "default"
        cls.settings_default_value: str = "test_default"

        cls.settings_user_priority: str = "user"
        cls.settings_user_value: str = "test_user"

        cls.settings_project_priority: str = "project"
        cls.settings_project_value: str = "test_project"

        cls.settings_customize_priority: str = "customize"
        cls.settings_customize_rank: int = 25
        cls.settings_customize_value: str = "test_customize"

    def test_setting_attributes_empty(self) -> None:
        setting_attributes: SettingAttributes = SettingAttributes()
        self.assertIsNone(setting_attributes.get())
        self.assertIsNone(setting_attributes.get_priority())

    @patch.dict(SETTING_PRIORITIES, {**SETTING_PRIORITIES, "customize": 25})
    def test_setting_attributes(self) -> None:
        setting_attributes: SettingAttributes = SettingAttributes(
            self.settings_default_value, self.settings_default_priority
        )
        self.assertEqual(setting_attributes.get(), self.settings_default_value)
        self.assertEqual(
            setting_attributes.get_priority(), self.settings_default_priority
        )

        self.assertIsNone(
            setting_attributes.set(
                self.settings_project_value, self.settings_project_priority
            )
        )
        self.assertEqual(setting_attributes.get(), self.settings_project_value)
        self.assertEqual(
            setting_attributes.get_priority(), self.settings_project_priority
        )

        setting_attributes.set(self.settings_user_value, self.settings_user_priority)
        self.assertEqual(setting_attributes.get(), self.settings_project_value)
        self.assertEqual(
            setting_attributes.get_priority(), self.settings_project_priority
        )

        self.assertIsNone(
            setting_attributes.set(
                self.settings_customize_value, self.settings_customize_priority
            )
        )
        self.assertEqual(setting_attributes.get(), self.settings_customize_value)
        self.assertEqual(
            setting_attributes.get_priority(), self.settings_customize_priority
        )


class BaseSettingsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings_default: Dict[str, str] = {
            "test_default_1": "default_1",
            "test_default_2": "default_2",
        }
        cls.settings_user: Dict[str, str] = {
            "test_user_1": "user_1",
            "test_user_2": "user_2",
        }
        cls.settings_project: Dict[str, str] = {
            "test_project_1": "project_1",
            "test_project_2": "project_2",
        }
        cls.settings_customize: Dict[str, str] = {
            "test_customize_1": "customize_1",
            "test_customize_2": "customize_2",
        }

    def setUp(self) -> None:
        self.base_settings = BaseSettings(self.settings_default, priority="default")

    def tearDown(self) -> None:
        del self.base_settings

    def test_init(self):
        base_settings = BaseSettings()
        self.assertDictEqual(base_settings._data, {})
        self.assertTrue(base_settings._frozen)

        self.assertEqual(len(self.base_settings), len(self.settings_default))
        for key, value in self.settings_default.items():
            self.assertEqual(self.base_settings[key], value)

    def test_contains(self):
        self.assertIn("test_default_1", self.base_settings)
        self.assertNotIn("test_customize_1", self.base_settings)

    def test_delitem(self):
        self.assertIn("test_default_1", self.base_settings)
        with self.base_settings.unfreeze() as bs:
            del bs["test_default_1"]
        self.assertNotIn("test_default_1", self.base_settings)

    def test_getitem(self):
        self.assertEqual(self.base_settings["test_default_1"], "default_1")
        with self.assertRaises(KeyError):
            _: Any = self.base_settings["test_default_3"]

    def test_iter(self):
        iter_base_settings = iter(self.base_settings)
        self.assertIsInstance(iter_base_settings, Iterator)

    def test_len(self):
        base_settings = BaseSettings()
        self.assertEqual(len(base_settings), 0)

        self.assertEqual(len(self.base_settings), len(self.settings_default))

    def test_setitem(self):
        with self.base_settings.unfreeze() as bs:
            bs["test_default_1"] = "project_1"
        self.assertEqual(self.base_settings["test_default_1"], "project_1")
        self.assertEqual(self.base_settings.get_priority("test_default_1"), "project")

        with self.base_settings.unfreeze() as bs:
            bs["test_default_3"] = "default_3"
        self.assertEqual(self.base_settings["test_default_3"], "default_3")

        self.assertEqual(self.base_settings.get_priority("test_default_3"), "project")

    def test_get(self):
        self.assertEqual(self.base_settings.get("test_default_1"), "default_1")

        self.assertNotIn("test_default_3", self.base_settings)
        self.assertEqual(
            self.base_settings.get("test_default_3", "default_3"), "default_3"
        )
        with self.assertRaises(KeyError):
            self.base_settings.get("test_default_4")

    @patch.dict(SETTING_PRIORITIES, {**SETTING_PRIORITIES, "customize": 25})
    def test_get_priority(self):
        self.assertEqual(self.base_settings.get_priority("test_default_1"), "default")

        self.assertNotIn("test_default_3", self.base_settings)
        with self.assertRaises(KeyError):
            self.base_settings.get_priority("test_default_3")

        with self.base_settings.unfreeze() as bs:
            bs.set("test_default_3", "default_3", "customize")
        self.assertEqual(self.base_settings.get_priority("test_default_3"), "customize")

    def test_is_frozen(self):
        self.assertTrue(self.base_settings.is_frozen())

        self.base_settings._frozen = False
        self.assertFalse(self.base_settings.is_frozen())

    @patch.dict(SETTING_PRIORITIES, {**SETTING_PRIORITIES, "customize": 25})
    def test_set(self):
        self.assertNotIn("test_default_3", self.base_settings)
        with self.base_settings.unfreeze() as bs:
            self.assertIsNone(bs.set("test_default_3", "default_3", "customize"))
        self.assertEqual(self.base_settings["test_default_3"], "default_3")
        self.assertEqual(self.base_settings.get_priority("test_default_3"), "customize")

    def test_unfreeze(self):
        self.assertTrue(self.base_settings.is_frozen())
        with self.base_settings.unfreeze() as base_settings:
            self.assertIs(base_settings, self.base_settings)
            self.assertFalse(self.base_settings.is_frozen())

        self.assertTrue(self.base_settings.is_frozen())

    @patch.dict(SETTING_PRIORITIES, {**SETTING_PRIORITIES, "customize": 25})
    def test_update(self):
        # test for mapping object
        with self.base_settings.unfreeze() as bs:
            self.assertIsNone(bs.update(self.settings_customize, priority="customize"))
        self.assertIn("test_customize_1", self.base_settings)
        self.assertIs(
            self.base_settings["test_customize_1"],
            self.settings_customize["test_customize_1"],
        )
        self.assertIs(self.base_settings.get_priority("test_customize_1"), "customize")

        # test for iterable object
        with self.base_settings.unfreeze() as bs:
            self.assertIsNone(
                bs.update(list(self.settings_project.items()), priority="project")
            )
        self.assertIn("test_project_1", self.base_settings)
        self.assertEqual(self.base_settings["test_project_1"], "project_1")
        self.assertEqual(self.base_settings.get_priority("test_project_1"), "project")

        with self.assertRaises(TypeError):
            with self.base_settings.unfreeze() as bs:
                bs.update(1)

    def test_frozen_check(self):
        with self.assertRaises(SettingsFrozenException):
            del self.base_settings["test_default_1"]


class SettingsTest(TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        del self.tempdir

    # TODO: mock DEFAULT_SETTINGS instead of update_from_module
    def test_init_empty(self):
        with patch.object(Settings, "update_from_module", return_value=None), patch(
            "minotaur.settings.get_user_config", return_value=None
        ), patch.object(os.environ, "items", return_value={}):
            settings = Settings()
            self.assertEqual(len(settings), 0)

    def test_init(self):
        with patch(
            "minotaur.settings.get_user_config",
            return_value=Path(os.getcwd()) / "tests/samples/.minotaur.yaml",
        ), patch.object(
            os.environ, "items", return_value={"MINOTAUR_SENTRY_DSN": "DSN"}.items()
        ):
            settings = Settings()

        # user config
        self.assertIn("TEST_USER", settings)
        self.assertEqual(settings["TEST_USER"], 1)
        self.assertEqual(settings.get_priority("TEST_USER"), "user")

        # env config
        self.assertIn("SENTRY_DSN", settings)
        self.assertEqual("DSN", settings["SENTRY_DSN"])
        self.assertEqual(settings.get_priority("SENTRY_DSN"), "env")

    def test_update_from_module(self):
        with patch.object(
            Path, "home", return_value=Path(os.getcwd()) / "tests/samples"
        ):
            settings = Settings()

        with settings.unfreeze():
            settings.update_from_module("tests.samples.settings")

        self.assertIn("TEST_PROJECT", settings)
        self.assertEqual("project_setting", settings["TEST_PROJECT"])
        self.assertEqual(settings.get_priority("TEST_PROJECT"), "project")
