import traceback

import daiquiri

try:  # pragma: no cover
    from Queue import Empty
except:  # noqa  pragma: no cover
    from queue import Empty

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
            q_error,
            robust,
            until=None,
            args=None,
            kwargs=None,
    ):
        # set up the io queues
        self.q_stdout = q_stdout
        self.q_stderr = q_stderr
        self.q_error = q_error

        self._robust = robust
        self._until = until

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

        self._has_logged_expiration = False

    @property
    def expired(self):
        expired = False
        if self._until is not None and self._until < datetime.datetime.now():
            expired = True
            if not self._has_logged_expiration:
                self._has_logged_expiration = True
                logger = daiquiri.getLogger(self._name)
                logger.info('Process expired and will no longer run')
        return expired

    def is_alive(self):
        return self._process is not None and self._process.is_alive()

    def start(self):

        self._process = Process(
            target=wrapped_target,
            args=[
                self._target, self.q_stdout, self.q_stderr,
                self.q_error, self._robust, self._name
            ] + list(self._args),
            kwargs=self._kwargs
        )
        self._process.daemon = True
        self._process.start()


class IOQueue:  # pragma: no cover
    """
    Okay, so here is something annoying.  If you spawn a python subprocess, you cannot
    pipe stdout/stderr in the same way you can with the parent process.  People who
    run this library probably want to be able to redirect output to logs.  The best way
    I could figure out to handle this was to monkey patch stdout and stderr in the
    subprocesses to be an instance of this class.  All this does is send write() messages
    to a queue that is monitored by the parent process and prints to parent stdtou/stderr
    """
    def __init__(self, q):
        self._q = q

    def write(self, item):
        self._q.put(item)

    def flush(self):
        pass


def wrapped_target(target, q_stdout, q_stderr, q_error, robust, name, *args, **kwargs):  # pragma: no cover
    """
    Wraps a target with queues replacing stdout and stderr
    """
    import sys
    sys.stdout = IOQueue(q_stdout)
    sys.stderr = IOQueue(q_stderr)

    try:
        target(*args, **kwargs)

    except:  # noqa
        if not robust:
            s = 'Error in tab\n' + traceback.format_exc()
            logger = daiquiri.getLogger(name)
            logger.error(s)
        else:
            raise

        if not robust:
            q_error.put(name)
        raise


class ProcessMonitor:
    TIMEOUT_SECONDS = .05

    def __init__(self):

        self._subprocesses = []
        self._is_running = False
        self.q_stdout = Queue()
        self.q_stderr = Queue()
        self.q_error = Queue()

    def add_subprocess(self, name, func, robust, until, *args, **kwargs):
        sub = SubProcess(
            name,
            target=func,
            q_stdout=self.q_stdout,
            q_stderr=self.q_stderr,
            q_error=self.q_error,
            robust=robust,
            until=until,
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

    def process_error_queue(self, error_queue):
        try:
            error_name = error_queue.get(timeout=self.TIMEOUT_SECONDS)
            if error_name:
                error_name = error_name.strip()
                self._subprocesses = [s for s in self._subprocesses if s._name != error_name]
                logger = daiquiri.getLogger(error_name)
                logger.info('Will not auto-restart because it\'s not robust')

        except Empty:
            pass

    def loop(self, max_seconds=None):
        """
        Main loop for the process. This will run continuously until maxiter
        """
        loop_started = datetime.datetime.now()

        self._is_running = True
        while self._is_running:
            self.process_error_queue(self.q_error)

            if max_seconds is not None:
                if (datetime.datetime.now() - loop_started).total_seconds() > max_seconds:
                    logger = daiquiri.getLogger('crontabs')
                    logger.info('Crontabs reached specified timeout.  Exiting.')
                    break
            for subprocess in self._subprocesses:
                if not subprocess.is_alive() and not subprocess.expired:
                    subprocess.start()

            self.process_io_queue(self.q_stdout, sys.stdout)
            self.process_io_queue(self.q_stderr, sys.stderr)
