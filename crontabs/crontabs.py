"""
Module for manageing crontabs interface
"""
import datetime
import functools
import time
import traceback
import warnings

import daiquiri
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from fleming import fleming
from .processes import ProcessMonitor

import logging
daiquiri.setup(level=logging.INFO)


class Cron:
    @classmethod
    def get_logger(self, name='crontab_log'):
        logger = daiquiri.getLogger(name)
        return logger

    def __init__(self):
        """
        A Cron object runs many "tabs" of asynchronous tasks.
        """
        self.monitor = ProcessMonitor()
        self._tab_list = []

    def schedule(self, *tabs):
        self._tab_list = list(tabs)
        return self

    def go(self, max_seconds=None):
        for tab in self._tab_list:
            target = tab._get_target()
            self.monitor.add_subprocess(tab._name, target, tab._robust, tab._until)
        try:
            self.monitor.loop(max_seconds=max_seconds)
        except KeyboardInterrupt:  # pragma: no cover
            pass


class Tab:
    _SILENCE_LOGGER = False

    def __init__(self, name, robust=True, verbose=True, memory_friendly=False):
        """
        Schedules a Tab entry in the cron runner
        :param name:  Every tab must have a string name
        :param robust:  A robust tab will be restarted if an error occures
                        A non robust tab will not be restarted, but all other
                        non-errored tabs should continue running
        :param verbose: Set the verbosity of log messages.
        :memory friendly: If set to true, each iteration will be run in separate process
        """
        if not isinstance(name, str):
            raise ValueError('Name argument must be a string')

        self._name = name
        self._robust = robust
        self._verbose = verbose
        self._starting = None
        self._every_kwargs = None
        self._func = None
        self._func_args = None
        self._func_kwargs = None
        self._exclude_func = lambda t: False
        self._during_func = lambda t: True
        self._memory_friendly = memory_friendly
        self._until = None
        self._lasting_delta = None

    def _log(self, msg):
        if self._verbose and not self._SILENCE_LOGGER:  # pragma: no cover
            logger = daiquiri.getLogger(self._name)
            logger.info(msg)

    def _process_date(self, datetime_or_str):
        if isinstance(datetime_or_str, str):
            return parse(datetime_or_str)
        elif isinstance(datetime_or_str, datetime.datetime):
            return datetime_or_str
        else:
            raise ValueError('.starting() and until() method can only take strings or datetime objects')

    def starting(self, datetime_or_str):
        """
        Set the starting time for the cron job.  If not specified, the starting time will always
        be the beginning of the interval that is current when the cron is started.

        :param datetime_or_str: a datetime object or a string that dateutil.parser can understand
        :return: self
        """
        self._starting = self._process_date(datetime_or_str)
        return self

    def starting_at(self, datetime_or_str):
        warnings.warn('.starting_at() is depricated.  Use .starting() instead')
        return self.starting(datetime_or_str)

    def until(self, datetime_or_str):
        """
        Run the tab until the specified time is reached.  At that point, deactivate the expired
        tab so that it no longer runs.

        :param datetime_or_str: a datetime object or a string that dateutil.parser can understand
        :return: self
        """
        self._until = self._process_date(datetime_or_str)
        return self

    def lasting(self, **kwargs):
        """
        Run the tab so that it lasts this long.  The argument structure is exactly the same
        as that of the .every() method
        """
        relative_delta_kwargs = {k if k.endswith('s') else k + 's': v for (k, v) in kwargs.items()}
        self._lasting_delta = relativedelta(**relative_delta_kwargs)
        return self

    def excluding(self, func, name=''):
        """
        Pass a function that takes a timestamp for when the function should execute.
        It inhibits running when the function returns True.
        Optionally, add a name to the exclusion.  This name will act as an explanation
        in the log for why the exclusion was made.
        """
        self._exclude_func = func
        self._exclude_name = name

        return self

    def during(self, func, name=''):
        """
        Pass a function that takes a timestamp for when the function should execute.
        It will only run if the function returns true.
        Optionally, add a name.  This name will act as an explanation in the log for why
        any exclusions were made outside the "during" specification.
        """
        self._during_func = func
        self._during_name = name

        return self

    def every(self, **kwargs):
        """
        Specify the interval at which you want the job run.  Takes exactly one keyword argument.
        That argument must be one named one of [second, minute, hour, day, week, month, year] or
        their plural equivalents.

        :param kwargs: Exactly one keyword argument
        :return: self
        """
        if len(kwargs) != 1:
            raise ValueError('.every() method must be called with exactly one keyword argument')

        self._every_kwargs = self._clean_kwargs(kwargs)

        return self

    def run(self, func, *func_args, **func__kwargs):
        """
        Specify the function to run at the scheduled times

        :param func:  a callable
        :param func_args:  the args to the callable
        :param func__kwargs: the kwargs to the callable
        :return:
        """
        self._func = func
        self._func_args = func_args
        self._func_kwargs = func__kwargs
        return self

    def _clean_kwargs(self, kwargs):
        allowed_key_map = {
            'seconds': 'second',
            'second': 'second',
            'minutes': 'minute',
            'minute': 'minute',
            'hours': 'hour',
            'hour': 'hour',
            'days': 'day',
            'day': 'day',
            'weeks': 'week',
            'week': 'week',
            'months': 'month',
            'month': 'month',
            'years': 'year',
            'year': 'year',
        }

        kwargs = {k if k.endswith('s') else k + 's': v for (k, v) in kwargs.items()}

        out_kwargs = {}
        for key in kwargs.keys():
            out_key = allowed_key_map.get(key.lower())
            if out_key is None:
                raise ValueError('Allowed time names are {}'.format(sorted(allowed_key_map.keys())))
            out_kwargs[out_key] = kwargs[key]

        return out_kwargs

    def _is_uninhibited(self, time_stamp):
        can_run = True
        msg = 'inhibited: '
        if self._exclude_func(time_stamp):
            if self._exclude_name:
                msg += self._exclude_name
            can_run = False

        if can_run and not self._during_func(time_stamp):
            if self._during_name:
                msg += self._during_name
            can_run = False

        if not can_run:
            self._log(msg)

        return can_run

    def _loop(self, max_iter=None):
        if not self._SILENCE_LOGGER:  # pragma: no cover don't want to clutter tests
            logger = daiquiri.getLogger(self._name)
            logger.info('Starting {}'.format(self._name))
        # fleming and dateutil have arguments that just differ by ending in an "s"
        fleming_kwargs = self._every_kwargs
        relative_delta_kwargs = {}

        # build the relative delta kwargs
        for k, v in self._every_kwargs.items():
            relative_delta_kwargs[k + 's'] = v

        # if a starting time was given use the floored second of that time as the previous time
        if self._starting is not None:
            previous_time = fleming.floor(self._starting, second=1)

        # otherwise use the interval floored value of now as the previous time
        else:
            previous_time = fleming.floor(datetime.datetime.now(), **fleming_kwargs)

        # keep track of iterations
        n_iter = 0
        # this is the infinite loop that runs the cron.  It will only be stopped when the
        # process is killed by its monitor.
        while True:
            n_iter += 1
            if max_iter is not None and n_iter > max_iter:
                break
            # everything is run in a try block so errors can be explicitly handled
            try:
                # push forward the previous/next times
                next_time = previous_time + relativedelta(**relative_delta_kwargs)
                previous_time = next_time

                # get the current time
                now = datetime.datetime.now()

                # if our job ran longer than an interval, we will need to catch up
                if next_time < now:
                    continue

                # sleep until the computed time to run the function
                sleep_seconds = (next_time - now).total_seconds()
                time.sleep(sleep_seconds)

                # See what time it is on wakeup
                timestamp = datetime.datetime.now()

                # If passed until date, break out of here
                if self._until is not None and timestamp > self._until:
                    break

                # If not inhibited, run the function
                if self._is_uninhibited(timestamp):
                    self._log('Running {}'.format(self._name))
                    self._func(*self._func_args, **self._func_kwargs)

            except KeyboardInterrupt:  # pragma: no cover
                pass

            except:  # noqa
                # only raise the error if not in robust mode.
                if self._robust:
                    s = 'Error in tab\n' + traceback.format_exc()
                    logger = daiquiri.getLogger(self._name)
                    logger.error(s)
                else:
                    raise
        self._log('Finishing {}'.format(self._name))

    def _get_target(self):
        """
        returns a callable with no arguments designed
        to be the target of a Subprocess
        """
        if None in [self._func, self._func_kwargs, self._func_kwargs, self._every_kwargs]:
            raise ValueError('You must call the .every() and .run() methods on every tab.')

        if self._memory_friendly:  # pragma: no cover  TODO: need to find a way to test this
            target = functools.partial(self._loop, max_iter=1)
        else:  # pragma: no cover  TODO: need to find a way to test this
            target = self._loop

        if self._lasting_delta is not None:
            self._until = datetime.datetime.now() + self._lasting_delta

        return target
