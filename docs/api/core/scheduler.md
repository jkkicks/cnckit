# Scheduler

The scheduler module coordinates job execution between the machine and queue.

## SchedulerState

::: cnckit.core.scheduler.SchedulerState
    options:
      show_root_heading: true
      heading_level: 3

## Scheduler

::: cnckit.core.scheduler.Scheduler
    options:
      show_root_heading: true
      heading_level: 3
      members:
        - __init__
        - state
        - current_job
        - events
        - start
        - stop
        - pause
        - tick
        - run_forever
