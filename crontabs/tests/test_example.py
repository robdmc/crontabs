from collections import Counter
from crontabs import Cron, Tab
from unittest import TestCase
import datetime
import sys

from dateutil.parser import parse

Tab._SILENCE_LOGGER = True


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



# Run tests with
# py.test -s  crontabs/tests/test_example.py::TestSample::test_base_case
# Or for parallel tests
# py.test -s  --cov  -n 2

class TestSample(TestCase):
    def test_base_case(self):
        cron = Cron()
        cron.tab(
            [
                Tab('two_sec', verbose=False).every(seconds=2).run(time_logger, 'two_sec'),
                Tab('three_sec', verbose=False).every(seconds=3).run(time_logger, 'three_sec')
            ]
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

    def test_other_case(self):
        cron = Cron()
        cron.tab(
            [
                Tab('two_sec', verbose=False).every(seconds=2).run(time_logger, 'two_sec'),
                Tab('three_sec', verbose=False).every(seconds=3).run(time_logger, 'three_sec')
            ]
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

