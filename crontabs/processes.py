from Queue import Empty
from multiprocessing import Process, Queue
from time import sleep



import logging
import daiquiri

# daiquiri.setup(level=logging.INFO)
import sys


class SubProcess:
    def __init__(
            self,
            name,
            target,
            q,
            args=None,
            kwargs=None,
    ):

        self.q = q
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

        self._process = Process(
            target=wrapped_target,
            args=[self._target, self.q] + list(self._args),
            kwargs=self._kwargs
        )
        self._process.daemon = True
        self._process.start()
        # logger = daiquiri.getLogger(self._name)
        # logger.info('Starting')


def wrapped_target(target, q, *args, **kwargs):

    class QStdout:
        def __init__(self, q):
            self._q = q

        def write(self, item):
            q.put(item)

    import sys
    sys.stdout = QStdout(q)

    target(*args, **kwargs)


class ProcessMonitor:
    SLEEP_SECONDS = .5

    def __init__(self):

        self._subprocesses = []
        self._is_running = False
        self.q = Queue()

    def add_subprocess(self, name, func, *args, **kwargs):
        sub = SubProcess(
            name,
            target=func,
            q = self.q,
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
            try:
                out = self.q.get(timeout=.1)
                out = out.strip()
                if out:
                    print(out)
                sys.stdout.flush()
            except Empty:
                pass

OKAY HERE IS WHAT IM WORKING ON.  I JUST GOT STDOUT SENT BACK TO MOTHER Process
USING A QUEUE.  I NEED TO DO THE SAME THING FOR STDERR AND CLEAN IT UP.
