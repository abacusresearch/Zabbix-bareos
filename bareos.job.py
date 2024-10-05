#! /usr/bin/env python3
import sys
import bareos.bsock
import argparse
import time
import datetime
import re
import yaml

sys.stderr = open('/tmp/bareos.job.py.err.log','a')

configfile = '/etc/zabbix/zabbix_bareos.yml'

with open(configfile, 'r') as ymlfile:
    config = yaml.load(ymlfile, yaml.SafeLoader)

user = config['user']
password = bareos.bsock.Password(config['password'])
host = config.get('host', "localhost")
port = config.get('port', 9101)

def create_console():
    with open('/tmp/bareos.job.py.console.log', 'a', encoding="utf-8") as logf:
        logf.write("==== %s ====\n" % datetime.datetime.today().ctime())
    console = bareos.bsock.DirectorConsoleJson(
        address=host, port=port, name=user, password=password
    )
    with open('/tmp/bareos.job.py.console.log', 'a', encoding="utf-8") as logf:
        logf.write("  console: %s\n" % "OK" if console is not None else "ERR")
    return console


def last_status(args):
    with open('/tmp/bareos.job.py.log', 'a', encoding="utf-8") as logf:
        logf.write("==== %s ====\n" % datetime.datetime.today().ctime())
        logf.write("  job %s\n" % args.job)
    console = create_console()
    with open('/tmp/bareos.job.py.log', 'a', encoding="utf-8") as logf:
        logf.write("  console: %s\n" % "OK" if console is not None else "ERR")
    last_job = console.call('llist job="{}" last'.format(args.job))
    with open('/tmp/bareos.job.py.log', 'a', encoding="utf-8") as logf:
        logf.write("  last_job: %s\n" % "OK" if last_job is not None else "ERR")
        logf.write("  jobstatus [%s]\n" % last_job["jobs"][0]["jobstatus"])
    print((last_job["jobs"][0]["jobstatus"]))


def last_size(args):
    console = create_console()
    last_job = console.call('llist job="{}" jobstatus=T last'.format(args.job))
    print((last_job["jobs"][0]["jobbytes"]))


def get_time(args):
    console = create_console()
    t = console.call("time")["time"]
    dt = datetime.datetime(
        int(t["year"]),
        int(t["month"]),
        int(t["day"]),
        int(t["hour"]),
        int(t["minute"]),
        int(t["second"]),
    )
    print((int(time.mktime(dt.timetuple()))))


def get_total_jobs(args):
    console = create_console()
    total_jobs = console.call('.sql query="SELECT COUNT(Job) FROM Job;"')
    try:
        if total_jobs["query"][0].get("count"):
            print((total_jobs["query"][0]["count"]))
        else:
            print((total_jobs["query"][0]["count(job)"]))
    except KeyError:
        print((-1))


def get_job_estimate(args):
    console = bareos.bsock.DirectorConsole(
        address=host, port=port, name=user, password=password
    )
    # console.send("estimate job={}".format(args.job))
    estimate = console.call('estimate job="{}"'.format(args.job))
    m = re.search("bytes=([0-9,]+)", re.sub(",", "", estimate))
    print((int(m.group(1))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    last_status_parser = subparsers.add_parser("last_status")
    last_status_parser.add_argument("job")
    last_status_parser.set_defaults(func=last_status)

    last_size_parser = subparsers.add_parser("last_size")
    last_size_parser.add_argument("job")
    last_size_parser.set_defaults(func=last_size)

    get_time_parser = subparsers.add_parser("get_time")
    get_time_parser.add_argument("null", nargs="?")
    get_time_parser.set_defaults(func=get_time)

    get_total_jobs_parser = subparsers.add_parser("get_total_jobs")
    get_total_jobs_parser.add_argument("null", nargs="?")
    get_total_jobs_parser.set_defaults(func=get_total_jobs)

    get_job_estimate_parser = subparsers.add_parser("get_job_estimate")
    get_job_estimate_parser.add_argument("job")
    get_job_estimate_parser.set_defaults(func=get_job_estimate)

    args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()
        parser.exit()
