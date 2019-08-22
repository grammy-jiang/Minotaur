"""
Exceptions for this project
"""


class SettingsFrozenException(Exception):
    """
    raise this exception when a frozen settings object is trying to be modified
    """
    pass
