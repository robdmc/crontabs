import multiprocessing
from time import sleep

import signal

import sys





import logging

import daiquiri

daiquiri.setup(level=logging.INFO)


atexit.register(exit_func)

class SubProcess:
    def __init__(
            self,
            name,
            target,
            args=None,
            kwargs=None,
    ):
        # Setup the name of the sub process
        self._name = name

        # Save the target of the process
        self._target = target

        # Save the args to the process
        self._args = args or set()

        # Setup a reference to the process
        self._process = None

        # Save the kwargs to the process
        self._kwargs = kwargs or {}

    def is_alive(self):
        return self._process is not None and self._process.is_alive()

    def start(self):
        self._process = multiprocessing.Process(
            target=self._target,
            args=self._args,
            kwargs=self._kwargs
        )
        self._process.daemon = True
        self._process.start()
        logger = daiquiri.getLogger(self._name)
        logger.info('Starting')


class ProcessMonitor:
    SLEEP_SECONDS = .5

    def __init__(self):

        self._subprocesses = []
        self._is_running = False

    def add_subprocess(self, name, func, *args, **kwargs):
        sub = SubProcess(
            name,
            target=func,
            args=args,
            kwargs=kwargs
        )
        self._subprocesses.append(sub)

    def run(self):
        self.loop()

    def loop(self):
        """
        Main loop for the process. This will run continuously until the max run seconds is reached or an exception
        """
        self._is_running = True
        while self._is_running:
            for subprocess in self._subprocesses:
                if not subprocess.is_alive():
                    subprocess.start()
            sleep(self.SLEEP_SECONDS)
