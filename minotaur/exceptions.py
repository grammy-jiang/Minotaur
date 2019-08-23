"""
Exceptions for this project
"""


class MinotaurException(Exception):
    """
    The base exception used in this package
    """


class SettingsFrozenException(MinotaurException):
    """
    raise this exception when a frozen settings object is trying to be modified
    """
