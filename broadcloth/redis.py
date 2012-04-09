import os

from fabric.api import *
from fabric.contrib.files import exists
from fabric.contrib.files import upload_template
from broadcloth.helpers import signal
from broadcloth.helpers import remote
from broadcloth import set_env, register_setup

def setup(**overrides):
    set_env("redis_pidfile", os.path.join(env.shared_path, "pids", "redis.pid"), **overrides)
    set_env("redis_port", 6379, **overrides)
    set_env("redis_logfile", os.path.join(env.shared_path, "logs", "redis.log"), **overrides)
    set_env("redis_dbdir", os.path.join(env.servers_path, "redis", "db"), **overrides)
    set_env("redis_conf_template", os.path.join("config", "servers", "redis.template.conf"), **overrides)
    set_env("redis_conf", os.path.join(env.servers_path, "redis", "conf", "redis.conf"), **overrides)
register_setup(setup)


@task
def start():
    '''Start the redis-server instance.'''
    if exists(env.redis_pidfile):
        abort("redis-server pidfile already exists: %(redis_pidfile)s" % env)
        
    command = [
        os.path.join(env.servers_path, "bin", "redis-server"),
        env.redis_conf
    ]
    with cd(env.current_path):
        remote(" ".join(command))


@task
def stop():
    '''Stops the redis-server instance, if the pidfile is present'''
    signal("TERM", env.redis_pidfile)


@task
def restart():
    '''Hard restart of the master redis-server process'''
    stop()
    start()

# TODO: log rotation

@task
def update_conf():
    '''Updates the redis conf file on the server, using the template.  Leaves
    a backup file in the redis conf directory with a .bak extension.'''
    with prefix("umask 0002"):
        upload_template(env.redis_conf_template,
                        env.redis_conf,
                        context=env,
                        mode=0664)
        


def redis_cli(commands = []):
    if type(commands) == type(''):
        commands = commands.split(' ')
    commands.insert(0, os.path.join(env.servers_path, "bin", "redis-cli"))
    return " ".join(commands)

@task
def cli():
    with prefix("TERM=dumb"):
        run(redis_cli())


@task
def flush():
    '''Clears the entire contents of the production cache.'''
    run(redis_cli("flushall"))


