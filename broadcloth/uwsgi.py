import os

from fabric.api import *
from fabric.contrib.files import exists
from fabric.contrib.files import upload_template
from broadcloth.helpers import signal
from broadcloth.helpers import remote

from broadcloth import set_env, register_setup

def setup(**overrides):
    set_env("uwsgi_pidfile", os.path.join(env.shared_path, "pids", "uwsgi.pid"), **overrides)
    set_env("uwsgi_logfile", os.path.join(env.shared_path, "logs", "uwsgi.log"), **overrides)
    set_env("uwsgi_socket", os.path.join(env.shared_path, "sock", "uwsgi.sock"), **overrides)
    set_env("uwsgi_conf_template", os.path.join("config", "servers", "uwsgi.template.yml"), **overrides)
    set_env("uwsgi_conf", os.path.join(env.servers_path, "uwsgi", "conf", "uwsgi.yml"), **overrides)
register_setup(setup)

@task
def start():
    '''Start the uwsgi instance.'''
    if exists(env.uwsgi_pidfile):
        abort("uwsgi pidfile already exists: %(uwsgi_pidfile)s" % env)

    # TODO: ARRRRRG you can't source files in sudo
    # As long as we're using 1.1 built with our custom-build pcre
    # library, we need to tell uwsgi where to find this
    command = [
        "LD_LIBRARY_PATH=/seq/a2e0/tools/util/pcre/pcre-8.30/lib",
        os.path.join(env.servers_path, "bin", "uwsgi"),
        "--yaml %(uwsgi_conf)s" % env
    ]
    with cd(env.current_path):
        with prefix("umask 0002"):
            remote(" ".join(command))
            puts("*** ignore unlink() error - uwsgi quirk in 0.9.9.2 and 1.1")


@task
def asdf():
    for key in env:
        print "%s\t%s" % (key, env[key])

@task
def stop():
    '''Stops the uwsgi instance, if the pidfile is present'''
    signal("INT", env.uwsgi_pidfile)


@task
def restart():
    '''Hard restart of the master uwsgi process'''
    signal("TERM", env.uwsgi_pidfile)

@task
def reload():
    '''Gracefully reload the master uwsgi process and workers'''
    signal("HUP", env.uwsgi_pidfile)

@task
def statistics():
    '''Dump some statistics to the log file'''
    signal("USR1", env.uwsgi_pidfile)

# TODO: log rotation

@task
def update_conf():
    '''Updates the uwsgi conf file on the server, using the template.  Leaves
    a backup file in the uwsgi conf directory with a .bak extension.  Use this
    to roll back if necessary'''
    with prefix("umask 0002"):
        upload_template(env.uwsgi_conf_template,
                        env.uwsgi_conf,
                        context=env,
                        mode=0664)
