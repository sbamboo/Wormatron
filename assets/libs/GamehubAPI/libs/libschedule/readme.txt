Libschedule is a scheduling library made by Simon Kalmi Claesson
Version: 1.0
ReleaseDate: 2023-07-28

UNIX:
  On unix systems if shedules does not run, please run unixSetup.py as a sudo-user or run:
  $ sudo usermod -a -G crontab $USER
  $ sudo service cron start
  to ensure that cron is running
  you might also have to run:
  $ chmod +x <scriptYouScheduled>

Information Agent:
  To get information about currently running tasks run info.py

For internal use:
  Schedule with:
    File: schedule.py
    Func: parse_interval_and_generate_schedule
  Unschedule with:
    File: unschedule.py
    Func: remove_scheduled_task

For cli use:
  Run cliWrapper.py
  (Look at clihelp.txt or run 'cliWrapper.py -h' for help)

Dependencies (pip):
    crontab: pip install python-crontab
    json:    pip install pyjson

    tabulate: pip install tabulate (This is only for info.py)

Other files:
  tasks.json: Internal list of tasks, DONT TUTCH!
  _winSchedule.py: Helper file containg code to generate the XML format needed for the windows Task Scheduler