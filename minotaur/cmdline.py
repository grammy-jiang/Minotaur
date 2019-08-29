"""
Run Minotaur from command line
"""
from __future__ import annotations

from argparse import ArgumentParser, Namespace
from itertools import chain
from typing import KT, VT, Iterable, Mapping, Tuple, Union

from minotaur.core import Minotaur
from minotaur.settings import Settings


def parse_arguments() -> Namespace:
    """

    :return:
    :rtype: Namespace
    """
    parser: ArgumentParser = ArgumentParser(description="Minotaur daemon")

    parser.add_argument(
        "-s",
        "--settings",
        action="append",
        help="pass the settings to Minotaur",
        nargs="*",
        type=lambda x: x.split("="),
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="show the version of Minotaur"
    )

    return parser.parse_args()


def get_settings(
    settings: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]], priority: str = "project"
) -> Settings:
    """

    :param settings:
    :type settings: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]
    :param priority:
    :type priority: str
    :return:
    :rtype: Settings
    """
    settings = Settings(settings, priority)
    # TODO: update settings with the project configuration
    return settings


def configure_logging(settings: Settings) -> None:
    """

    :param settings:
    :type settings: Settings
    :return:
    """
    pass


def execute(
    *args, settings: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]] = None, **kwargs
) -> None:
    """

    :param args:
    :param settings:
    :type settings: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]
    :param kwargs:
    :return:
    """
    args: Namespace = parse_arguments()
    args.settings = dict(chain.from_iterable(args.settings))
    if settings:
        args.settings.update(settings)

    settings_: Settings = get_settings(args.settings, "cmd")

    configure_logging(settings_)

    minotaur = Minotaur(settings_)
    minotaur.add_job()
    minotaur.start()


if __name__ == "__main__":
    try:
        execute()
    except Exception as exc:
        raise exc
