from unittest.case import TestCase
from unittest.mock import patch

from minotaur.settings import (
    SETTING_PRIORITIES,
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

    def test_empty_setting_attributes(self) -> None:
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

        self.assertIsNone(
            setting_attributes.set(
                self.settings_user_value, self.settings_user_priority
            )
        )
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
