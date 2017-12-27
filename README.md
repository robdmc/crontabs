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


# Usage
### Scheduling a job to run every five seconds starting on the minute.
```python
from crontabs import Cron, Tab
from datetime import datetime

def my_job(*args, **kwargs):
    print('args={} kwargs={} running at {}'.format(args, kwargs, datetime.now()))

Cron().schedule(
    Tab(name='run_my_job').every(seconds=5).run(my_job, 'my_arg', my_kwarg='hello')
).go()

```

