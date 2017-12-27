import datetime
import time
import traceback

import daiquiri
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from fleming import fleming
from crontabs.processes import ProcessMonitor

import logging
daiquiri.setup(level=logging.INFO)


class Cron:
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
            self.monitor.add_subprocess(tab._name, tab._get_target())

        try:
            self.monitor.loop(max_seconds=max_seconds)
        except KeyboardInterrupt:  # pragma: no cover
            pass


class Tab:
    _SILENCE_LOGGER = False
    def __init__(self, name, robust=True, verbose=True):
        self._name = name
        self._robust = robust
        self._verbose = verbose
        self._starting_at = None
        self._every_kwargs = None
        self._func = None
        self._func_args = None
        self._func_kwargs = None

    def starting_at(self, datetime_or_str):
        """
        Set the starting time for the cron job.  If not specified, the starting time will always
        be the beginning of the interval that is current when the cron is started.

        :param datetime_or_str: a datetime object or a string that dateutil.parser can understand
        :return: self
        """
        if isinstance(datetime_or_str, str):
            self._starting_at = parse(datetime_or_str)
        elif isinstance(datetime_or_str, datetime.datetime):
            self._starting_at = datetime_or_str
        else:
            raise ValueError('.starting_at() method can only take strings or datetime objects')
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

        out_kwargs = {}
        for key in kwargs.keys():
            out_key = allowed_key_map.get(key.lower())
            if out_key is None:
                raise ValueError('Allowed time names are {}'.format(sorted(allowed_key_map.keys())))
            out_kwargs[out_key] = kwargs[key]

        return out_kwargs

    def _loop(self, max_iter=None):
        if not self._SILENCE_LOGGER:  # pragma: no cover don't want to clutter tests
            logger = daiquiri.getLogger(self._name)
            logger.info('Starting')
        # fleming and dateutil have arguments that just differ by ending in an "s"
        fleming_kwargs = self._every_kwargs
        relative_delta_kwargs = {}

        # build the relative delta kwargs
        for k, v in self._every_kwargs.items():
            relative_delta_kwargs[k + 's'] = v

        # if a starting time was given use the floored second of that time as the previous time
        if self._starting_at is not None:
            previous_time = fleming.floor(self._starting_at, second=1)

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

                if self._verbose and not self._SILENCE_LOGGER:  # pragma: no cover
                    logger.info('Running')

                # run the function
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

    def _get_target(self):
        """
        returns a callable with no arguments designed
        to be the target of a Subprocess
        """
        if None in [self._func, self._func_kwargs, self._func_kwargs, self._every_kwargs]:
            raise ValueError('You must call the .every() and .run() methods on every tab.')
        return self._loop
