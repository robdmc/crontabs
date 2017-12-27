# Crontabs
Crontabs is a small library that makes it simple to schedule python functions to run on a schedule.
Crontabs was inspired by the excellent [schedule](https://github.com/dbader/schedule) library for python,

In addition to having a slightly different API, Crontabs differs from the schedule module in the following
ways.

  * You do not need to provide your own event loop.
  * Job timing is guarenteed not to drift over time.  For example, if you specify to run a job every five minutes,
    you can rest assured that it will always run at 5, 10, 15, etc. passed the hour with no drift.
  * The python functions are all run in child processes.  Not only does this enable asynchronous scheduling,
    it also helps mitigate python memory problems due to the
    [high watermark issue](https://hbfs.wordpress.com/2013/01/08/python-memory-management-part-ii/)


# Installation
```bash
pip install crontabs
```
# Usage

### Schedule a single job
```python
from crontabs import Cron, Tab
from datetime import datetime


def my_job(*args, **kwargs):
    print('args={} kwargs={} running at {}'.format(args, kwargs, datetime.now()))


# Will run with a 5 minute interval synced to the top of the minute
Cron().schedule(
    Tab(name='run_my_job').every(seconds=5).run(my_job, 'my_arg', my_kwarg='hello')
).go()

```

### Schedule multiple jobs
```python
from crontabs import Cron, Tab
from datetime import datetime


def my_job(*args, **kwargs):
    print('args={} kwargs={} running at {}'.format(args, kwargs, datetime.now()))


# All logging messages are sent to sdtout
Cron().schedule(
    # Turn of logging for job that runs every five seconds
    Tab(name='my_fast_job', verbose=False).every(seconds=5).run(my_job, 'fast', seconds=5),

    # Go ahead and let this job emit logging messages
    Tab(name='my_slow_job').every(seconds=20).run(my_job, 'slow', seconds=20),
).go()

```

### Schedule future job to run repeatedly for a fixed amount of time
```python
from crontabs import Cron, Tab
from datetime import datetime


def my_job(*args, **kwargs):
    print('args={} kwargs={} running at {}'.format(args, kwargs, datetime.now()))


Cron().schedule(
    Tab(
        name='future_job'
    ).every(
        seconds=5
    ).starting_at(
        '12/27/2017 16:45'  # This argument can either be parsable text or datetime object.
    ).run(
        my_job, 'fast', seconds=5
    )
# max_seconds starts from the moment go is called.  Pad for future run times accordingly.
).go(max_seconds=60)
```

# Run test suite with
```bash
git clone git@github.com:robdmc/crontabs.git
cd crontabs
pip install -e .[dev]
py.test -s  --cov  -n 8
```
