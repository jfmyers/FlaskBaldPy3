# encoding: utf-8

from sqlalchemy.ext.mutable import Mutable
from flask_sqlalchemy import SQLAlchemy

from .model import create_model


db = SQLAlchemy()
Model = create_model(db)


class MutationDict(Mutable, dict):
    '''
    A dictionary that automatically emits change events for SQA
    change tracking.

    Lifted almost verbatim from the SQA docs.
    '''
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutationDict."
        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)
            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def update(self, *args, **kwargs):
        '''
        Updates the current dictionary with kargs or a passed in dict.
        Calls the internal setitem for the update method to maintain
        mutation tracking.
        '''
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."
        dict.__delitem__(self, key)
        self.changed()

    def __getstate__(self):
        '''Get state returns a plain dictionary for pickling purposes.'''
        return dict(self)

    def __setstate__(self, state):
        '''
        Set state assumes a plain dictionary and then re-constitutes a
        Mutable dict.
        '''
        self.update(state)

    def pop(self, *pargs, **kargs):
        """
        Wrap standard pop() to trigger self.changed()
        """
        try:
            result = super(MutationDict, self).pop(*pargs, **kargs)
        except Exception:
            raise
        else:
            self.changed()
            return result

    def popitem(self, *pargs, **kargs):
        """
        Wrap standard popitem() to trigger self.changed()
        """
        try:
            result = super(MutationDict, self).popitem(*pargs, **kargs)
        except Exception:
            raise
        else:
            self.changed()
            return result
