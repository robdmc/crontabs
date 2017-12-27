#! /usr/bin/env python
from crontabs.crontabs import Cron, Tab
import datetime


def func(n, extra=''):
    print('func {}.{} {}'.format(n, extra, datetime.datetime.now()))


cron = Cron()

tabs = [
    Tab(str(n)).every(seconds=n).run(func, n)
    for n in range(1, 8)
]
cron.tab(tabs)

# cron.tab(
#     [
#         Tab('one').starting_at(datetime.datetime.now()).every(minutes=1).run(func, 1),
#         Tab('two').every(minutes=1).run(func, 1, extra='base'),
#         # Tab('three').every(seconds=2).run(func1),
#         # Tab('four').every(seconds=4).run(func2),
#     ]
# )

cron.go()
