from collections import Counter
from crontabs import Cron, Tab
from unittest import TestCase
import datetime
import time
import sys

from dateutil.parser import parse

Tab._SILENCE_LOGGER = True

# Run tests with
# py.test -s  crontabs/tests/test_example.py::TestSample::test_base_case
# Or for parallel tests
# py.test -s  --cov  -n 2


class ExpectedException(Exception):
    pass


class PrintCatcher(object):  # pragma: no cover  This is a testing utility that doesn't need to be covered
    def __init__(self, stream='stdout'):
        self.text = ''
        if stream not in {'stdout', 'stderr'}:  # pragma: no cover  this is just a testing utitlity
            raise ValueError('stream must be either "stdout" or "stderr"')
        self.stream = stream

    def write(self, text):
        self.text += text

    def flush(self):
        pass

    def __enter__(self):
        if self.stream == 'stdout':
            sys.stdout = self
        else:
            sys.stderr = self
        return self

    def __exit__(self, *args):
        if self.stream == 'stdout':
            sys.stdout = sys.__stdout__
        else:
            sys.stderr = sys.__stderr__


def time_logger(name):  # pragma: no cover
    print('{} {}'.format(name, datetime.datetime.now()))


def time__sleepy_logger(name):  # pragma: no cover
    time.sleep(3)
    print('{} {}'.format(name, datetime.datetime.now()))


def error_raisor(name):
    raise ExpectedException('This exception is expected in tests. Don\'t worry about it.')


class TestCrontabs(TestCase):

    def test_non_robust_error(self):
        tab = Tab(
            'one_sec', verbose=False, robust=False
        ).every(seconds=1).run(
            error_raisor, 'one_sec')

        with self.assertRaises(ExpectedException):
            tab._loop(max_iter=1)

    def test_robust_error(self):
        tab = Tab(
            'one_sec', verbose=False
        ).every(seconds=1).run(
            error_raisor, 'one_sec')
        tab._loop(max_iter=1)

    def test_tab_loop_sleepy(self):
        tab = Tab(
            'one_sec', verbose=False
        ).every(seconds=1).run(
            time__sleepy_logger, 'one_sec')
        with PrintCatcher() as catcher:
            tab._loop(max_iter=7)
        self.assertEqual(catcher.text.count('one_sec'), 2)

    def test_tab_loop_anchored(self):
        now = datetime.datetime.now() + datetime.timedelta(seconds=1)
        tab = Tab(
            'one_sec', verbose=False
        ).every(seconds=1).starting(
            now).run(
            time_logger, 'one_sec')
        with PrintCatcher() as catcher:
            tab._loop(max_iter=3)
        self.assertEqual(catcher.text.count('one_sec'), 3)

    def test_tab_loop(self):
        tab = Tab(
            'one_sec', verbose=False).every(seconds=1).run(
            time_logger, 'one_sec')
        with PrintCatcher() as catcher:
            tab._loop(max_iter=3)

        self.assertEqual(catcher.text.count('one_sec'), 3)

    def test_incomplete(self):
        with self.assertRaises(ValueError):
            Cron().schedule(Tab('a').run(time_logger, 'bad')).go()

    def test_bad_starting(self):
        with self.assertRaises(ValueError):
            Tab('a').starting(2.345)
            # Cron().schedule(Tab('a').starting(2.345))

    def test_bad_every(self):
        with self.assertRaises(ValueError):
            Tab('a').every(second=1, minute=3)
            # Cron().schedule(Tab('a').every(second=1, minute=3))

    def test_bad_interval(self):
        with self.assertRaises(ValueError):
            Tab('a').every(bad=11)
            # Cron().schedule(Tab('a').every(bad=11))

    def test_base_case(self):
        cron = Cron()
        cron.schedule(
            Tab('two_sec', verbose=False).every(seconds=2).run(time_logger, 'two_sec'),
            Tab('three_sec', verbose=False).every(seconds=3).run(time_logger, 'three_sec')
        )
        with PrintCatcher(stream='stdout') as stdout_catcher:
            cron.go(max_seconds=6)

        base_lookup = {
            'three_sec': 3,
            'two_sec': 2,
        }

        lines = list(stdout_catcher.text.split('\n'))

        # make sure times fall int right slots
        for line in lines:
            if line:
                words = line.split()
                name = words[0]
                time = parse('T'.join(words[1:]))
                self.assertEqual(time.second % base_lookup[name], 0)

        # make sure the tasks were run the proper number of times
        counter = Counter()
        for line in lines:
            if line:
                counter.update({line.split()[0]: 1})

        self.assertEqual(counter['two_sec'], 3)
        self.assertEqual(counter['three_sec'], 2)

    def test_anchored_case(self):
        cron = Cron()
        starting = datetime.datetime.now()
        cron.schedule(
            Tab('three_sec', verbose=False).starting(starting).every(seconds=3).run(time_logger, 'three_sec'),
            Tab('three_sec_str', verbose=False).starting(
                starting.isoformat()).every(seconds=3).run(time_logger, 'three_sec_str'),
        )
        with PrintCatcher(stream='stdout') as stdout_catcher:
            cron.go(max_seconds=3.5)

        # make sure times fall int right slots
        lines = list(stdout_catcher.text.split('\n'))
        for line in lines:
            if line:
                words = line.split()
                time = parse('T'.join(words[1:]))
                elapsed = (time - starting).total_seconds()
                self.assertTrue(elapsed > 2)
                self.assertTrue(elapsed < 3)

    def test_excluding(self):
        # Test base case
        cron = Cron()
        cron.schedule(
            Tab('base_case', verbose=True).every(seconds=1).run(time_logger, 'base_case'),
            Tab('d+').every(seconds=1).during(lambda t: True).run(time_logger, 'd+'),
            Tab('d-').every(seconds=1).during(lambda t: False).run(time_logger, 'd-'),
            Tab('e+').every(seconds=1).excluding(lambda t: True).run(time_logger, 'e+'),
            Tab('e-').every(seconds=1).excluding(lambda t: False).run(time_logger, 'e-'),
        )

        with PrintCatcher(stream='stdout') as stdout_catcher:
            cron.go(max_seconds=1.5)

        self.assertTrue('d+' in stdout_catcher.text)
        self.assertFalse('d-' in stdout_catcher.text)
        self.assertFalse('e+' in stdout_catcher.text)
        self.assertTrue('e-' in stdout_catcher.text)


class TestRobustness(TestCase):
    def test_robust_case(self):

        then = datetime.datetime.now()

        def timed_error():  # pragma: no cover
            now = datetime.datetime.now()
            if then + datetime.timedelta(seconds=3) < now < then + datetime.timedelta(seconds=6):
                print('timed_error_failure')
                raise ExpectedException('This exception is expected in tests. Don\'t worry about it.')
            else:
                print('timed_error_success')

        cron = Cron()
        cron.schedule(
            Tab('one_sec', verbose=False).every(seconds=1).run(time_logger, 'running_time_logger'),
            Tab('two_sec', verbose=False, robust=True).every(seconds=1).run(timed_error)
        )
        with PrintCatcher(stream='stdout') as catcher:
            cron.go(max_seconds=10)

        success_count = catcher.text.count('timed_error_success')
        failure_count = catcher.text.count('timed_error_failure')
        time_logger_count = catcher.text.count('running_time_logger')
        self.assertEqual(success_count, 7)
        self.assertEqual(failure_count, 3)
        self.assertEqual(time_logger_count, 10)

    def test_non_robust_case(self):

        then = datetime.datetime.now()

        def timed_error():
            now = datetime.datetime.now()
            if then + datetime.timedelta(seconds=3) < now < then + datetime.timedelta(seconds=6):
                print('timed_error_failure')
                raise ExpectedException('This exception is expected in tests. Don\'t worry about it.')
            else:
                print('timed_error_success')

        cron = Cron()
        cron.schedule(
            Tab('one_sec', verbose=False).every(seconds=1).run(time_logger, 'running_time_logger'),
            Tab('two_sec', verbose=False, robust=False).every(seconds=1).run(timed_error)
        )
        with PrintCatcher(stream='stdout') as catcher:
            cron.go(max_seconds=10)

        success_count = catcher.text.count('timed_error_success')
        failure_count = catcher.text.count('timed_error_failure')
        time_logger_count = catcher.text.count('running_time_logger')
        self.assertEqual(success_count, 3)
        self.assertEqual(failure_count, 1)
        self.assertEqual(time_logger_count, 10)
