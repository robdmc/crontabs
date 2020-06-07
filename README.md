# Crontabs
Think of crontabs as a quick-and-dirty solution you can throw into one-off python scripts to execute tasks on a cron-like schedule.

Crontabs is a small pure-python library that was inspired by the excellent [schedule](https://github.com/dbader/schedule) library for python.

In addition to having a slightly different API, crontabs differs from the schedule module in the following
ways.

  * You do not need to provide your own event loop.
  * Job timing is guaranteed not to drift over time.  For example, if you specify to run a job every five minutes,
    you can rest assured that it will always run at 5, 10, 15, etc. passed the hour with no drift.
  * The python functions are all run in child processes.  Although not currently implemented, there are plans to update
    subprocess management to help mitigate python memory problems due to the
    [high watermark issue](https://hbfs.wordpress.com/2013/01/08/python-memory-management-part-ii/)

# Why Crontabs
Python has no shortage of [cron-like job scheduling libraries](https://pypi.python.org/pypi?%3Aaction=search&term=cron), so why create yet another.  The honest answer is that I couldn't find one that met a simple list of criteria.
* **Simple installation with no configuration.** An extremely robust and scalable solution to this problem already exists.  [Celery](http://www.celeryproject.org/). But for quick and dirty work, I didn't want the hastle of setting up and configuring a broker, which celery requires to do its magic.  For simple jobs, I just wanted to pip install and go.
* **Human readable interface.**  I loved the interface provided by the [schedule](https://github.com/dbader/schedule) library and wanted something similarly intuitive to use.
* **Memory safe for long running jobs.** Celery workers can suffer from severe memory bloat due to the way Python manages memory.  As of 2017, the recommended solution for this was to periodically restart the workers.  Crontabs runs each job in a subprocess.  The strategy for doing this will soon be updated to ensure memory bloat is not an issue.
* **Simple solution for cron-style workflow and nothing more.**  I was only interested in supporting cron-like functionality, and wasn't interested in all the other capabilities and guarantees offered by a real task-queue solution like celery.
* **Suggestions for improvement welcome.** If you encounter a bug or have an improvement that remains within the scope listed above, please feel free to open an issue (or even better... a PR).

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


# Will run with a 5 second interval synced to the top of the minute
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
    # Turn off logging for job that runs every five seconds
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
    ).starting(
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
py.test -s -n 8   # Might need to change the -n amount to pass
```

___
Projects by [robdmc](https://www.linkedin.com/in/robdecarvalho).
* [Pandashells](https://github.com/robdmc/pandashells) Pandas at the bash command line
* [Consecution](https://github.com/robdmc/consecution) Pipeline abstraction for Python
* [Behold](https://github.com/robdmc/behold) Helping debug large Python projects
* [Crontabs](https://github.com/robdmc/crontabs) Simple scheduling library for Python scripts
* [Switchenv](https://github.com/robdmc/switchenv) Manager for bash environments
