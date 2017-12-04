# encoding: utf-8

import jwt
import json
import logging
import time

from datetime import datetime as date, timedelta as timedelta
from flask import request, current_app, redirect
from functools import wraps

from .response import APIError, APIUnauthorized


def create_jwt(secret, payload={}, exp=date.utcnow() + timedelta(days=7),
               iat=date.utcnow(), algorithm='HS256'):
    payload.update({
        'exp': exp,
        'iat': iat
    })
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_jwt(token, secret, audience=None, algorithm='HS256'):
    if not audience:
        jwt.decode(token, secret, algorithm=algorithm, leeway=7200)
    return jwt.decode(token, secret, audience=audience, algorithm=algorithm, leeway=7200)


def get_jwt_claims(jwt_key='Authorization'):
    secret = current_app.config.get('JWT_CLIENT_SECRET')
    audience = current_app.config.get('JWT_CLIENT_AUDIENCE')

    if not secret:
        return None

    jwtoken = request.headers.get(jwt_key, request.cookies.get(jwt_key))
    logging.info("jwtoken: {0}".format(jwtoken))
    if not jwtoken:
        return None

    try:
        jwt_claims = decode_jwt(jwtoken, secret, audience=audience)
    except (jwt.ExpiredSignatureError, jwt.DecodeError):
        logging.info("JWT signature error")
        return None

    sub = jwt_claims.get('sub')
    if not sub:
        return None

    return jwt_claims


def user_required(orig_func=None, jwt_key='Authorization', redirect_url=None, code=302):

    def requirement(orig_func):
        '''Requirement decorator.'''
        @wraps(orig_func)
        def replacement(*pargs, **kargs):
            jwt_claims = get_jwt_claims(jwt_key=jwt_key)
            if not jwt_claims:
                if redirect_url:
                    if type(redirect_url) != str:
                        return redirect(redirect_url(request), code=code)
                    return redirect(redirect_url, code=code)
                else:
                    raise APIUnauthorized("User authentication is required to access this resource.")
            return orig_func(*pargs, **kargs)

        return replacement

    if not orig_func:
        return requirement
    else:
        return requirement(orig_func)


def get_auth_id(jwt_key='Authorization'):
    '''Get the current logged-in users auth id'''
    try:
        jwt_claims = get_jwt_claims(jwt_key=jwt_key)
    except (APIError, APIUnauthorized):
        return None

    if not jwt_claims:
        return None

    return jwt_claims.get('sub')
