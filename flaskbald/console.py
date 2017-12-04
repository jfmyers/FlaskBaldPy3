#!/usr/bin/env python
# encoding: utf-8
import code
import readline
import atexit
import os

from .db_ext import db

class Console(code.InteractiveConsole):
    ''' console including history buffer per project.'''
    def __init__(self, project_name, package_name=None, app=None,
                 models=None, additional_symbols=None):
        if additional_symbols is None:
            additional_symbols = {}

        self.project_name = project_name
        if not package_name:
            package_name = self.project_name

        self.app = app

        # add the application to the console namespace
        console_symbols = {'app': app, 'db': db}
        console_symbols.update(models)

        # add webob Req/Resp objects to the console for convenience
        # console_symbols.update({"Request": webob.Request,
        #                         "Response": webob.Response})
        # console_symbols.update({"c": Client(app=app)})
        console_symbols.update(additional_symbols)

        histfile = os.path.expanduser("~/.flaskbald-{0}-console-history".format(
                                                                 project_name))

        code.InteractiveConsole.__init__(self, locals=console_symbols,
                                                filename="<console>")
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        readline.write_history_file(histfile)

    def run(self):
        '''Start the console with the project, controllers,
        and models defined in the console's namespace.'''
        with self.app.app_context():
            self.interact('''Welcome to the Flask-Bald interactive console\n'''
                          ''' ** project: {0} **'''.format(self.project_name))


def start_console(app, options=None):
    '''Start a console with a particular app.

    :param app: wsgi application passed in
    :param options: an object or named tuple containing the options for the
                    web server such as host and port. Generally an argparser
                    object is passed in for command line invokation

    A pybald application must be configured before starting a console.
    '''
    import pybald
    from pybald.db import models
    # now the models registry is loaded and the additional_symbols
    # added so models are available in the console
    # if no models are configured, return empty symbols
    try:
        symbols = dict([(model.__name__, model) for model in
                        models.Model.registry])
    except RuntimeError:
        symbols = {}
    else:
        symbols['models'] = models
        symbols['db'] = pybald.context.db
    # create a pybald console around it
    console = Console(project_name=pybald.context.config.project_name or
                      pybald.context.name, app=app,
                      additional_symbols=symbols)
    console.run()
