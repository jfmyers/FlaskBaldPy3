# encoding: utf-8
import json

from flask import request, Response, current_app, render_template
from webob import Response
from functools import wraps

from .template import template_functions


def action(orig_func):
    '''
    Return rendered template with environment data and template functions.
    '''
    @wraps(orig_func)
    def replacement(*args, **kargs):
        handler_response = orig_func(*args, **kargs)
        if type(handler_response) is tuple or type(handler_response) is list:
            current_app.jinja_env.globals.update(**template_functions)
            template = handler_response[0]
            data = handler_response[1]
            if not data or type(data) is not dict:
                data = dict()

            data.update({
                'config': current_app.config,
                'ENV': current_app.config.get("ENV"),
                "HOST_URL": request.host
            })
            return render_template(template, **data)
        else:
            return handler_response

    return replacement


def action_v2(orig_func):
    '''
    Return rendered template with environment data and template functions and optionally set cookies.
    '''
    @wraps(orig_func)
    def replacement(*args, **kargs):
        handler_response = orig_func(*args, **kargs)
        if type(handler_response) is tuple or type(handler_response) is list:
            current_app.jinja_env.globals.update(**template_functions)
            template = handler_response[0]
            data = handler_response[1]
            if not data or type(data) is not dict:
                data = dict()

            try:
                cookies = handler_response[2]
            except:
                cookies = None

            data.update({
                'config': current_app.config,
                'ENV': current_app.config.get("ENV"),
                "HOST_URL": request.host
            })

            if cookies and type(cookies) == dict:
                resp = current_app.make_response(render_template(template, **data))
                for cookie_key, cookie_value in cookies.iteritems():
                    resp.set_cookie(cookie_key, value=cookie_value)
                return resp
            else:
                return render_template(template, **data)
        else:
            return handler_response

    return replacement


def json_response(body, status, status_code=200, jwt_cookie=None):
    '''
    Return response JSON encoded with proper headers.
    '''
    resp = Response(json.dumps({"status": "success", "data": body}),
                    status=status, content_type="application/json",
                    charset='utf-8')

    # resp = Response(json.dumps({"status": "success", "data": body}))
    # resp.status_code = status_code
    # resp.status = status
    # resp.headers['Content-Type'] = "application/json; charset=utf-8"
    # resp.headers['Access-Control-Expose-Headers'] = 'Access-Control-Allow-Origin'
    # resp.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'

    if jwt_cookie:
        resp.set_cookie(key="jwt", value=jwt_cookie.get('token'),
                        httponly=True)
        # resp.set_cookie('jwt', jwt_cookie.get('token'), httponly=True)

    resp.headers.update({
        # 'Access-Control-Allow-Origin': '*',
        'Access-Control-Expose-Headers': 'Access-Control-Allow-Origin',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
    })

    return resp


def api_action(orig_func=None, set_jwt_cookie=False):
    """
    Decorator that wraps an action in API goodness.

    The orig_func is expected to return any JSON-serializable python data
    structure, or raise any ApiException (which will be wrapped in a
    standard JSON structure).

    """
    def actual_decorator(orig_func):
        @wraps(orig_func)
        # @cross_origin()
        def replacement(*args, **kargs):
            try:
                handler_response = orig_func(*args, **kargs)
            except APIError as api_error_response:
                return api_error_response

            # return the response or reformat for proper response
            if isinstance(handler_response, Response):
                return handler_response
            else:
                jwt_cookie = None
                if set_jwt_cookie and handler_response.get('token'):
                    jwt_cookie = {'token': handler_response.get('token')}
                return json_response(handler_response, status='200 OK', jwt_cookie=jwt_cookie)
        return replacement


    if not orig_func:
        def waiting_for_func(orig_func):
            return actual_decorator(orig_func)
        return waiting_for_func
    else:
        return actual_decorator(orig_func)


def request_data():
    '''
    Retrieve the data from this Flask app's context,
    decode and return as Python dict.
    '''
    from flask import request
    data = request.get_data()
    if data is None:
        data = {}
    else:
        try:
            data = json.loads(data)
        except ValueError:
            data = {}
    return data


class APIError(Exception):

    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class APIPaymentRequired(APIError):
    status_code = 402


class APINotFound(APIError):
    status_code = 404


class APIBadRequest(APIError):
    status_code = 400


class APIUnauthorized(APIError):
    status_code = 401


class APIResourceConflict(APIError):
    status_code = 409


class APIUserUnsubscribed(APIUnauthorized):
    """
    Indicates that the targeted User account is no longer
    subscribed to an API service

    (Inherits 401/Unauthorized status)
    """
    pass


class APIRequiredParameter(APIBadRequest):
    pass
