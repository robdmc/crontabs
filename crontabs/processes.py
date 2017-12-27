from Queue import Empty
from multiprocessing import Process, Queue
import datetime
import sys


class SubProcess:
    def __init__(
            self,
            name,
            target,
            q_stdout,
            q_stderr,
            args=None,
            kwargs=None,
    ):
        # set up the io queues
        self.q_stdout = q_stdout
        self.q_stderr = q_stderr

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
            args=[self._target, self.q_stdout, self.q_stderr] + list(self._args),
            kwargs=self._kwargs
        )
        self._process.daemon = True
        self._process.start()

class IOQueue:  # pragma: no cover
    def __init__(self, q):
        self._q = q

    def write(self, item):
        self._q.put(item)

def wrapped_target(target, q_stdout, q_stderr, *args, **kwargs):  # pragma: no cover
    """
    Wraps a target with queues replacing stdout and stderr
    """
    import sys
    sys.stdout = IOQueue(q_stdout)
    sys.stderr = IOQueue(q_stderr)

    target(*args, **kwargs)


class ProcessMonitor:
    TIMEOUT_SECONDS = .05

    def __init__(self):

        self._subprocesses = []
        self._is_running = False
        self.q_stdout = Queue()
        self.q_stderr = Queue()

    def add_subprocess(self, name, func, *args, **kwargs):
        sub = SubProcess(
            name,
            target=func,
            q_stdout = self.q_stdout,
            q_stderr = self.q_stderr,
            args=args,
            kwargs=kwargs
        )
        self._subprocesses.append(sub)

    def process_io_queue(self, q, stream):
        try:
            out = q.get(timeout=self.TIMEOUT_SECONDS)
            out = out.strip()
            if out:
                stream.write(out + '\n')
                stream.flush()
        except Empty:
            pass

    def loop(self, max_seconds=None):
        """
        Main loop for the process. This will run continuously until maxiter
        """
        loop_started =  datetime.datetime.now()

        self._is_running = True
        while self._is_running:
            if max_seconds is not None:
                if (datetime.datetime.now() - loop_started).total_seconds() > max_seconds:
                    break
            for subprocess in self._subprocesses:
                if not subprocess.is_alive():
                    subprocess.start()

            self.process_io_queue(self.q_stdout, sys.stdout)
            self.process_io_queue(self.q_stderr, sys.stderr)
