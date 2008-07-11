#!/usr/bin/env python

import os
import sys
import yaml

from optparse import OptionParser

try:
    from cherrypy.wsgiserver import CherryPyWSGIServer
except ImportError:
    from wsgiserver import CherryPyWSGIServer

class ImproperlyConfigured(Exception):
    pass

class WSGIServerProcess(object):
    """
    A simple wrapper around starting and stopping a CherryPy WSGI process.
    """
    def __init__(self, dispatcher, host, port, daemonize=False, pidfile=None,
                 env={}, wsgi_env={}):
        self.dispatcher = dispatcher
        self.host = host
        self.port = port
        self.daemonize = daemonize
        self.pidfile = pidfile
        self.env = env
        self.wsgi_env = wsgi_env
    
    def start(self):
        """
        Starts the WSGI server.
        """
        server = CherryPyWSGIServer((self.host, self.port), self.dispatcher)
        server.environ.update(self.wsgi_env)
        if self.daemonize:
            daemonize()
        if self.pidfile:
            print "writing pid (%s)" % self.pidfile
            writepid(self.pidfile)
        # setup the process environment
        for var, value in self.env.items():
            os.environ[var] = value
        try:
            server.start()
        except KeyboardInterrupt:
            # likely not a daemon so make sure to shutdown properly.
            server.stop()
    
    def stop(self, pid):
        """
        Given ``pid`` (a process ID) gracefully terminate the process.
        """
        pass

def daemonize():
    """
    Detach from the terminal and continue as a daemon.
    """
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent again.
    os.umask(077)
    null = os.open("/dev/null", os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)

def writepid(pid_file):
    """
    Write the process ID to disk.
    """
    fp = open(pid_file, "w")
    fp.write(str(os.getpid()))
    fp.close()

def load_config(config_file):
    """
    Loads the given ``config_file`` and returns a dictionary of its contents.
    """
    return yaml.load(open(config_file, "r"))

def load_dispatcher(path):
    """
    Given a module path, e.g. "django.core.handlers.wsgi.WSGIHandler" return
    the WSGIHandler object.
    """
    dot = path.rindex(".")
    dispatcher_mod, dispatcher_callable = path[:dot], path[dot+1:]
    mod = __import__(dispatcher_mod, {}, {}, [""])
    return getattr(mod, dispatcher_callable)

def load_wsgi_server(name, **kwargs):
    """
    Given a ``name`` return an instance of ``WSGIServerProcess``.
    """
    config = kwargs.pop("config", {})
    dispatcher_path = config.get("dispatcher")
    if not dispatcher_path:
        raise ImproperlyConfigured, "'%s' does not have a dispatcher" % name
    dispatcher = load_dispatcher(dispatcher_path)
    host = kwargs.pop("host", config.get("host", "127.0.0.1"))
    try:
        port = int(kwargs.pop("port", config.get("port")))
    except TypeError:
        # None is used for the port meaning it was not given
        raise ImproperlyConfigured, "no port specified for '%s'" % name
    except ValueError:
        raise ImproperlyConfigured, "'%s' has a malformed port" % name
    defaults = {"env": config.get("env", {}),
                "wsgi_env": config.get("wsgi_env", {})}
    defaults.update(kwargs)
    return WSGIServerProcess(dispatcher, host, port, **defaults)

def parse_parameters():
    """
    Parses the parameters passed in over the command-line using optparse.
    Returns a dictionary mapping options to their values.
    """
    params = {}
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-h", "--host", dest="host")
    parser.add_option("-p", "--port", dest="port")
    parser.add_option("-d", "--daemon", dest="daemon", action="store_true")
    options, args = parser.parse_args(sys.argv[3:])
    if options.host:
        params["host"] = options.host
    if options.port:
        params["port"] = options.port
    params["daemonize"] = options.daemon
    return params

def main():
    """
    Handles the main bit of the program. Called when ran standalone from the
    command-line.
    """
    if len(sys.argv[1:]) < 2:
        sys.exit("you must specify a server name and command.")
    name, command = sys.argv[1:3]
    params = parse_parameters()
    try:
        config = load_config(os.path.expanduser("~/.wsgirc"))
    except IOError, ex:
        sys.exit("cannot find .wsgirc file: %s" % ex)
    try:
        server_config = config["servers"][name]
    except KeyError:
        sys.exit("no server named '%s'" % name)
    pid_path = config.get("pid-path")
    if not pid_path:
        root_pid_path = "."
    else:
        root_pid_path = os.path.expanduser(config["pid-path"])
    params["pidfile"] = os.path.join(root_pid_path, "%s.pid" % name)
    try:
        server = load_wsgi_server(name, config=server_config, **params)
    except ImproperlyConfigured, ex:
        sys.exit(ex.message)
    if command == "start":
        print "starting %s (%s:%d)" % (name, server.host, server.port)
        server.start()
    elif command == "stop":
        if not server.pidfile:
            sys.exit("'%s' does not have a pidfile" % name)
        pid = open(server.pidfile, "r").read()
        print "stopping %s (%s)" % (name, pid)
        server.stop(pid)
    else:
        sys.exit("unknown command '%s'" % command)

if __name__ == "__main__":
    main()
