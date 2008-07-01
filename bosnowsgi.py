#!/usr/bin/env python

import os
import sys
import yaml

from optparse import OptionParser
from cherrypy.wsgiserver import CherryPyWSGIServer

class NoServerFound(Exception):
    pass

class ImproperlyConfigured(Exception):
    pass

class WSGIServerProcess(object):
    """
    A simple wrapper around starting and stopping a CherryPy WSGI process.
    """
    def __init__(self, dispatcher, host, port, daemonize=False, pidfile=None):
        self.host = host
        self.port = port
        self.daemonize = daemonize
        self.pidfile = pidfile
    
    def start(self):
        """
        Starts the WSGI server.
        """
        server = CherryPyWSGIServer((self.host, self.port), self.dispatcher)
        if self.daemonize:
            daemonize()
        try:
            server.start()
        except KeyboardInterrupt:
            # likely not a daemonize so make sure to shutdown properly.
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
    try:
        config = load_config(os.path.expanduser("~/.bosnowsgirc"))[name]
    except KeyError:
        raise NoServerFound, "No server named '%s'" % name
    dispatcher_path = config.get("dispatcher")
    if not dispatcher_path:
        raise ImproperlyConfigured, "'%s' does not have a dispatcher" % name
    dispatcher = load_dispatcher(dispatcher_path)
    host = config.get("host", "127.0.0.1")
    if not host:
        raise ImproperlyConfigured, "'%s' does not have a host key" % name
    port = config.get("port")
    defaults = {"host": host, "port": port}
    defaults.update(kwargs)
    try:
        defaults["port"] = int(defaults["port"])
    except ValueError:
        raise ImproperlyConfigured, "'%s' has a malformed port" % name
    return WSGIServerProcess(dispatcher, **defaults)

def main():
    """
    Handles the main bit of the program. Called when ran standalone from the
    command-line.
    """
    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port")
    options, args = parser.parse_args()
    try:
        name = args[0]
    except IndexError:
        print "you must specify a server"
        raise SystemExit
    try:
        command = args[1]
    except IndexError:
        print "no command given"
    params = {}
    if options.port:
        params["port"] = options.port
    try:
        server = load_wsgi_server(name, **params)
    except (NoServerFound, ImproperlyConfigured), ex:
        print ex.message
        raise SystemExit
    if command == "start":
        print "starting %s (%s:%d)" % (name, server.host, server.port)
        server.start()
    elif command == "stop":
        if not server.pidfile:
            print "'%s' does not have a pidfile" % name
            raise SystemExit
        pid = open(server.pidfile, "r").read()
        print "stopping %s (%s)" % (name, pid)
        server.stop(pid)
    else:
        print "unknown command '%s'" % command

if __name__ == "__main__":
    main()
