# encoding: utf-8

from flask import current_app

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from flask_sqlalchemy import SQLAlchemy

import sys
import re
import sqlalchemy as sa

from sqlalchemy.orm.attributes import (
    instance_state
    )
from sqlalchemy.orm.util import (
    has_identity
)
from .text import camel_to_underscore, pluralize

# the surrogate_pk template that assures that surrogate primary keys
# are all the same and ordered with the pk first in the table
surrogate_pk_template = sa.Column(sa.Integer, nullable=False, primary_key=True)


def get_models(module):
    models_dict = {}
    def assign_attr(item):
        models_dict[item] = getattr(module, item)

    map(assign_attr, dir(module))
    return models_dict


def create_dump_engine(app):
    '''Create a sql engine that just prints SQL using the current dialect to
    STDOUT instead of executing it.
    This is useful especially to see what the DDL statements are for various dialects
    '''
    def dump(sql, *multiparams, **params):
        sys.stdout.write( str(sql.compile(dialect=dump_engine.dialect) ).strip() +"\n")

    def dialect():
        match = re.search(r'^([^\:]*\:\/\/)', app.config['SQLALCHEMY_DATABASE_URI'])
        if match:
            return match.group(1)
        else:
            return "sqlite://"
    dump_engine = sa.create_engine(dialect(), strategy='mock', executor=dump)
    return dump_engine


def create_model(db):

    class Model(db.Model):

        __abstract__  = True

        id            = db.Column(db.Integer, primary_key=True)
        date_created  = db.Column(db.DateTime,  default=db.func.current_timestamp())
        date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                                                  onupdate=db.func.current_timestamp())

        NotFound = sa.orm.exc.NoResultFound
        MultipleFound = sa.orm.exc.MultipleResultsFound

        def is_modified(self):
            '''Check if SQLAlchemy believes this instance is modified.'''
            return instance_state(self).modified

        def clear_modified(self):
            '''
            Unconditionally clear all modified state from the attibutes on
            this instance.
            '''
            return instance_state(self)._commit_all({})

        def is_persisted(self):
            '''
            Check if this instance has ever been persisted. Means it is either
            `detached` or `persistent`.
            '''
            return has_identity(self)

        def flush(self):
            '''
            Syncs all pending SQL changes (including other pending objects) to
            the underlying data store within the current transaction.

            Flush emits all the relevant SQL to the underlying store, but does
            **not** commit the current transaction or close the current
            database session.
            '''
            db.session.flush()
            return self

        def save(self, flush=False):
            '''
            Saves (adds) this instance in the current databse session.

            This does not immediatly persist the data since these operations
            occur within a transaction and the sqlalchemy unit-of-work pattern.
            If something causes a rollback before the session is committed,
            these changes will be lost.

            When flush is `True`, flushes the data to the database immediately
            **within the same transaction**. This does not commit the transaction,
            for that use :py:meth:`~pybald.db.models.Model.commit`)
            '''
            db.session.add(self)
            if flush:
                self.flush()
            return self

        def delete(self, flush=False):
            '''
            Delete this instance from the current database session.

            The object will be deleted from the database at the next commit. If
            you want to immediately delete the object, you should follow this
            operation with a commit to emit the SQL to delete the item from
            the database and commit the transaction.
            '''
            db.session.delete(self)
            if flush:
                self.flush()
            return self

        def commit(self):
            '''
            Commits the entire database session (including other pending objects).

            This emits all relevant SQL to the databse, commits the current
            transaction, and closes the current session (and database connection)
            and returns it to the connection pool. Any data operations after this
            will pull a new database session from the connection pool.
            '''
            db.session.commit()
            return self

        @classmethod
        def get(cls, **where):
            '''
            A convenience method that constructs a load query with keyword
            arguments as the filter arguments and return a single instance.
            '''
            return cls.load(**where).one()

        @classmethod
        def all(cls, **where):
            '''
            Returns a collection of objects that can be filtered for
            specific collections.

            all() without arguments returns all the items of the model type.
            '''
            return cls.load(**where).all()

        @classmethod
        def load(cls, **where):
            '''
            Convenience method to build a sqlalchemy query to return stored
            objects.

            Returns a query object. This query object must be executed to retrieve
            actual items from the database.
            '''
            if where:
                return db.session.query(cls).filter_by(**where)
            else:
                return db.session.query(cls)

        @classmethod
        def filter(cls, *pargs, **kargs):
            '''
            Convenience method that auto-builds the query and passes the filter
            to it.

            Returns a query object.
            '''
            return db.session.query(cls).filter(*pargs, **kargs)

        @classmethod
        def query(cls):
            '''
            Convenience method to return a query based on the current object
            class.
            '''
            return db.session.query(cls)

        # @classmethod
        # def show_create_table(cls):
        #     cls.__table__.create(create_dump_engine(app))

    return Model
