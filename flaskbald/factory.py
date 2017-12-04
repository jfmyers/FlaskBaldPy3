# encoding: utf-8

import os
import jinja2

from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
from flask_errormail import mail_on_500
from flask_mail import Mail
from flask_sslify import SSLify

from .db_ext import db
from .celery_ext import celery
from .response import APINotFound, api_action
from .log import default_debug_log

ALLOWED_HOSTS = 'ALLOWED_HOSTS'
ALL_HOSTS = '*'


def load_config(app, config_file=None, env='development'):
    if not config_file:
        return app

    app.config.from_pyfile(config_file)
    if not app.config.get(ALLOWED_HOSTS):
        app.config.update({ALLOWED_HOSTS: ALL_HOSTS})

    return app


def setup_templates(app, custom_template_paths=[]):
    base_template_dir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'default_templates'
    )

    template_paths = [
        app.jinja_loader,
        jinja2.FileSystemLoader(base_template_dir)]

    if custom_template_paths:
        for cp in custom_template_paths:
            template_paths.append(jinja2.FileSystemLoader(cp))

    app.jinja_loader = jinja2.ChoiceLoader(template_paths)
    return app


def register_blue_prints(app, blue_prints):
    for module in blue_prints:
        app.register_blueprint(module)
    return app


def setup_debug_log(app):
    (app.config.get('DEBUG', False) == True and default_debug_log())
    return app


def error_endpoints(app, custom_error_endpoints=False):
    if custom_error_endpoints is True:
        return app

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def not_found(error):
        return render_template('500.html'), 500

    return app


def before_handler(app, custom_handler, custom_handler_args, custom_handler_kargs):

    if custom_handler:
        @app.before_request
        def before_request():
            custom_handler(*custom_handler_args, **custom_handler_kargs)

        return app

    @app.before_request
    def before_request():
        origin_request = request.from_values()
        if app.config[ALLOWED_HOSTS] != ALL_HOSTS and origin_request.host not in app.config[ALLOWED_HOSTS]:
            if app.config.get('DEBUG', app.config.get('debug')):
                return APINotFound(message="Invalid host: '{0}'".format(origin_request.host))
            else:
                return APINotFound()

    return app


def after_handler(app, custom_handler, custom_handler_args, custom_handler_kargs, db_enabled):

    if custom_handler:
        @app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', '*')
            response.headers.add('Access-Control-Allow-Methods', '*')
            custom_handler_kargs['response'] = response
            return custom_handler(*custom_handler_args, **custom_handler_kargs)

        return app

    @app.after_request
    def after_request(response):
        if db_enabled:
            # Commit the session
            db.session.commit()

            # Close the session
            db.session.close()

            # Remove the session
            db.session.remove()

        # Return the response object
        return response

    return app


def init_db(app):
    db.init_app(app)
    return app


def setup_routes(app):
    routes = {}
    print('{:40s} {:45s} {}'.format(
            'Function', 'Valid Methods', 'Route'
    ))
    for rule in app.url_map.iter_rules():
        routes[rule.endpoint] = {
            'url': rule.rule if rule.rule else None,
            'methods': rule.methods if rule.methods else [],
            'args': {arg:arg for arg in rule.arguments} if rule.arguments else {}
        }

        methods = rule.methods #[m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
        print('{:40s} {:45s} {}'.format(
            rule.endpoint,
            ' '.join(methods),
            rule.rule
        ))

    app.config['routes'] = routes
    return app


def create_app(config_file, blueprints=[], custom_error_endpoints=False,
               custom_template_paths=[], custom_before_handler=None,
               custom_before_handler_args=[], custom_before_handler_kargs={},
               custom_after_handler=None, custom_after_handler_args=[],
               custom_after_handler_kargs={}, template_folder=None,
               cors=True, ssl_only=True, db_enabled=True, static_url_path=None,
               static_folder=None):

    if config_file is None:
        raise(Exception("Hey, 'config_files' cannot be 'None'!"))

    flask_init_options = {}
    if template_folder:
        flask_init_options['template_folder'] = template_folder
    if static_url_path:
        flask_init_options['static_url_path'] = static_url_path
    if static_folder:
        flask_init_options['static_folder'] = static_folder

    app = Flask(__name__, **flask_init_options)
    app = load_config(app, config_file)

    if ssl_only is True and app.config.get("DEBUG") is False:
        sslify = SSLify(app)

    app = setup_templates(app, custom_template_paths)
    app = setup_debug_log(app)
    app = register_blue_prints(app, blueprints)
    app = error_endpoints(app, custom_error_endpoints)
    app = before_handler(app, custom_before_handler, custom_before_handler_args, custom_before_handler_kargs)
    app = after_handler(app, custom_after_handler, custom_after_handler_args, custom_after_handler_kargs, db_enabled)
    if db_enabled:
        app = init_db(app)
    app = setup_routes(app)

    if cors is True:
        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

    if app.config.get('DEBUG') is False:
        mail = Mail(app)
        mail_on_500(app, app.config.get('ADMINS'))

    return app


def create_celery_app(app):
    celery.init_app(app)
    return celery
