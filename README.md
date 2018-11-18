# Securite
A web-based website CRON security scanner using Wapiti (http://wapiti.sourceforge.net/)

Requirements:
 * redis-server
 * python-rq
 * rq-scheduler

Additional Python Libraries:
 * flask
 * rq
 * redis
 * json2html
 * jinja2

The report generator works using rq worker, rqscheduler and redis-server, so you have to run them in separate consoles while executing run_project.py.