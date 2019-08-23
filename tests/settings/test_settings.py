from collections import Iterator
from typing import Any, Dict
from unittest.case import TestCase
from unittest.mock import patch

from minotaur.settings import (
    SETTING_PRIORITIES,
    BaseSettings,
    SettingAttributes,
    get_settings_priority,
)


class SettingsFunctionsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.setting_default: str = "default"
        cls.setting_customize: str = "customize"

    def test_get_settings_priority(self) -> None:
        priority: int = get_settings_priority(self.setting_default)
        self.assertEqual(priority, SETTING_PRIORITIES[self.setting_default])

        with self.assertRaises(KeyError):
            priority: int = get_settings_priority(self.setting_customize)

        SETTING_PRIORITIES[self.setting_customize]: int = 25
        priority: int = get_settings_priority(self.setting_customize)
        self.assertEqual(priority, SETTING_PRIORITIES[self.setting_customize])


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
        del self.base_settings["test_default_1"]
        self.assertNotIn("test_default_1", self.base_settings)

    def test_getitem(self):
        self.assertEqual(self.base_settings["test_default_1"], "default_1")
        with self.assertRaises(KeyError):
            value: Any = self.base_settings["test_default_3"]

    def test_iter(self):
        iter_base_settings = iter(self.base_settings)
        self.assertIsInstance(iter_base_settings, Iterator)

    def test_len(self):
        base_settings = BaseSettings()
        self.assertEqual(len(base_settings), 0)

        self.assertEqual(len(self.base_settings), len(self.settings_default))

    def test_setitem(self):
        self.base_settings["test_default_1"] = "project_1"
        self.assertEqual(self.base_settings["test_default_1"], "project_1")
        self.assertEqual(self.base_settings.get_priority("test_default_1"), "project")

        self.base_settings["test_default_3"] = "default_3"
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

        self.base_settings.set("test_default_3", "default_3", "customize")
        self.assertEqual(self.base_settings.get_priority("test_default_3"), "customize")

    def test_is_frozen(self):
        self.assertTrue(self.base_settings.is_frozen())

        self.base_settings._frozen = False
        self.assertFalse(self.base_settings.is_frozen())

    @patch.dict(SETTING_PRIORITIES, {**SETTING_PRIORITIES, "customize": 25})
    def test_set(self):
        self.assertNotIn("test_default_3", self.base_settings)
        self.assertIsNone(
            self.base_settings.set("test_default_3", "default_3", "customize")
        )
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
        self.assertIsNone(
            self.base_settings.update(self.settings_customize, priority="customize")
        )
        self.assertIn("test_customize_1", self.base_settings)
        self.assertIs(
            self.base_settings["test_customize_1"],
            self.settings_customize["test_customize_1"],
        )
        self.assertIs(self.base_settings.get_priority("test_customize_1"), "customize")
