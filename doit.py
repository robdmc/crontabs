#! /usr/bin/env python
# flake8: noqa

from crontabs import Cron, Tab
from datetime import datetime

def my_job(*args, **kwargs):
    print('args={} kwargs={} running at {}'.format(args, kwargs, datetime.now()))


Cron().schedule(
    Tab(
        name='future_job'
    ).every(
        seconds=5
    ).starting(
        '12/27/2017 16:55'
    ).run(
        my_job, 'fast', seconds=5
    )
).go(max_seconds=60)


# from crontabs.crontabs import Cron, Tab
# import datetime
#
#
# def func(n, extra=''):
#     print('func {}.{} {}'.format(n, extra, datetime.datetime.now()))
#
#
# cron = Cron()
#
# tabs = [
#     Tab(str(n)).every(seconds=n).run(func, n)
#     for n in range(1, 8)
# ]
# cron.schedule(tabs)
#
# # cron.tab(
# #     [
# #         Tab('one').starting(datetime.datetime.now()).every(minutes=1).run(func, 1),
# #         Tab('two').every(minutes=1).run(func, 1, extra='base'),
# #         # Tab('three').every(seconds=2).run(func1),
# #         # Tab('four').every(seconds=4).run(func2),
# #     ]
# # )
#
# cron.go()
