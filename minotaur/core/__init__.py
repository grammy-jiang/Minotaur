"""
The core classes and functions of this package
"""
from __future__ import annotations

from asyncio.events import get_event_loop
from logging import Logger, getLogger
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from minotaur.settings import Settings


class Minotaur:
    """
    This class is the core class to control everything
    """

    name = "minotaur.core.Minotaur"

    def __init__(self, settings: Settings):
        self.settings: Settings = settings
        self.logger: Logger = getLogger(self.name)

        self.scheduler = AsyncIOScheduler()
        # TODO: initial pipelines with pipeline middlewares

        # TODO: initial readers with reader middlewares

    async def execute(self):
        """

        :return:
        """
        # TODO: ask date from readers
        # TODO: push date to pipelines
        print(dict(self.settings))

    def add_job(self, job: Callable = None, *args, **kwargs):
        """
        register this instance to scheduler
        :return:
        """

        if job is None:
            job = self.execute
        self.scheduler.add_job(
            self.execute, trigger="interval", args=args, kwargs=kwargs, seconds=3
        )

    def start(self):
        self.scheduler.start()

        try:
            loop = get_event_loop()
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self.scheduler.shutdown()
