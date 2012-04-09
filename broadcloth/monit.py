import os

from fabric.api import env, task, run, cd, prefix
from fabric.contrib.files import exists
from fabric.contrib.files import upload_template
from broadcloth.helpers import signal
from broadcloth.helpers import remote

from broadcloth import set_env, register_setup

def setup(**overrides):
    set_env("monit_root", os.path.join(env.servers_path, 'monit'), **overrides)
    set_env("monit_conf_template", os.path.join("config", "servers",
                                                 "monitrc.template"), **overrides)
    set_env("monit_conf", os.path.join(env.servers_path, 'monit', 'etc', 'monitrc'), **overrides)
register_setup(setup)

default_location = "http://mmonit.com/monit/dist/monit-5.3.2.tar.gz"

@task
def install(source=None):
    # TODO: support source being a local file- test for file exists,
    # then assume url
    if not source:
        source = default_location

    # move to fabfile?
    src_dir = os.path.join(env.servers_path, 'src')
    install_to = env.monit_root
    
    with prefix("umask 0002"):
        run("mkdir -p %s" % src_dir)
        run("mkdir -p %s" % install_to)

        archive = os.path.basename(source)

        with cd(src_dir):
            run("curl -O %s" % source)
            run("tar -xzf %s" % archive)
            
        src_dir = os.path.join(src_dir, archive[:-len('.tar.gz')])
        with cd(src_dir):
            run("./configure --prefix=%s" % install_to)
            run("make")
            run("make install")

        with cd(os.path.join(env.servers_path, 'bin')):
            run("ln -s %s" % os.path.join(env.monit_root, 'bin', 'monit'))


@task
def start():
    monit()

@task
def stop():
    monit("quit")

@task
def status():
    monit("status")


def monit(command=None):
    with prefix("umask 0002"):
        c = [os.path.join(env.monit_root, 'bin', 'monit')]
        if command:
            c.append(command)
        remote(' '.join(c))


@task
def update_conf():
    with prefix("umask 0002"):
        run("mkdir -p %s" % os.path.dirname(env.monit_conf))
        remote("mv %(monit_conf)s{,.bak}" % env)
        upload_template(env.monit_conf_template,
                        env.monit_conf,
                        context=env,
                        backup=False,
                        mode=0664)
        remote("mv %(monit_conf)s %(monit_conf)s.tmp" % env)
        remote("cp %(monit_conf)s.tmp %(monit_conf)s" % env)
        remote("rm %(monit_conf)s.tmp" % env)
        remote("chmod 700 %(monit_conf)s" % env)





