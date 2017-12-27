# Crontabs.  Scheduling Made Simple
Crontabs is a small library that makes it simple to schedule python functions to run on a schedule.
Crontabs was inspired by the excellent schedule library for python, https://github.com/dbader/schedule

In addition to haveing a slightly different API than the schedule module, Crontabs differes in two other
significant ways.

  * You do not need to provide your own event loop.
  * Job timing is guarenteed not to drift over time.  For example, if you specify to run a job every five minutes,
    you can rest assured that it will always run at 5, 10, 15, etc. passed the hour with no drift.
  * The python functions are all run in child processes.  Not only does this enable asynchronous scheduling,
    it also helps mitigate python memory problems due to the
    [high watermark issue] (https://hbfs.wordpress.com/2013/01/08/python-memory-management-part-ii/)
    
