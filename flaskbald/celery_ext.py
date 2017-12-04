# encoding: utf-8

import flask
from celery import Celery
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

from .db_ext import db


class FlaskCelery(Celery):

    # def __init__(self, *args, **kwargs):

    #     super(FlaskCelery, self).__init__(*args, **kwargs)
    #     if 'app' in kwargs:
    #         self.init_app(kwargs['app'])

    #     self.patch_task()

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
                else:
                    with _celery.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        self.config_from_object(app.config)
        self.patch_task()


def flaskbald_task(**kargs):
    """
    Wrapper for Celery @task decorator to ensure DB sessions are
    properly closed once tasks execution has completed.
    """
    def requirement(task_function):

        @celery.task(**kargs)
        @wraps(task_function)
        def replacement(*pargs, **kargs):
            task_result = None
            # try:
            task_result = task_function(*pargs, **kargs)
            db.session.commit()
            # except SQLAlchemyError:
                # db.session.rollback()
                # raise SQLAlchemyError("Session Rolled Back")
            # finally:
            db.session.close()
            db.session.remove()
            return task_result

        return replacement

    return requirement


celery = FlaskCelery()
