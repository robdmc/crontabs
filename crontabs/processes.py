import multiprocessing
from time import sleep

import signal

import sys


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

    def stop(self):
        """
        Stop the process
        """
        # try stopping the processes
        try:
            self._process.terminate()
        # If an error was raised, the process is dead already
        except:
            pass
        # Regardless of what happened, set the current process to None
        finally:
            self._process = None

    def wait(self):  # pragma: no cover
        """
        Wait for the process to complete
        """
        if self._process:
            self._process.join()


class ProcessMonitor:
    SLEEP_SECONDS = .5

    def __init__(self):

        # Handle interrupts
        self.init_interrupts()

        self._subprocesses = []

    def add_subprocess(self, name, func, *args, **kwargs):
        sub = SubProcess(
            name,
            target=func,
            args=args,
            kwargs=kwargs
        )
        self._subprocesses.append(sub)

    def interrupt_handler(self, sig_num, stack):
        """
        Handle an interrupt signal
        """
        # Determine if we need to exit
        if sig_num in [signal.SIGINT, signal.SIGQUIT, signal.SIGTERM, signal.SIGABRT]:
            self.exit(0)

    def init_interrupts(self):
        """
        Initialize any signals that could interrupt this process
        """

        signals = [
            signal.SIGABRT,
            signal.SIGHUP,
            signal.SIGTERM,
            signal.SIGINT,
            signal.SIGQUIT,
            signal.SIGTRAP,
            signal.SIGUSR2,
        ]
        for sig_num in signals:
            signal.signal(sig_num, self.interrupt_handler)

    def run(self):
        try:
            self.loop()
        finally:
            self.stop_subprocesses()

    def loop(self):
        """
        Main loop for the process. This will run continuously until the max run seconds is reached or an exception
        """
        while True:
            for subprocess in self._subprocesses:
                if not subprocess.is_alive():
                    subprocess.start()
            sleep(self.SLEEP_SECONDS)

    def exit(self, sig_num=0):
        """
        Force the exit of this process with a sig num
        """

        # Stop the sub processes
        self.stop_subprocesses()

        # Exit the system
        sys.exit(0)

    def stop_subprocesses(self):
        """
        Stop all the sub processes
        """
        # Stop all sub processes
        for sub_process in self._subprocesses:
            sub_process.stop()
