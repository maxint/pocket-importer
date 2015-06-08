# coding: utf-8

import os
import requests
from functools import wraps


def method_wrapper(fn):

    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        arg_names = list(fn.__code__.co_varnames)
        arg_names.remove('self')
        kwargs.update(dict(zip(arg_names, args)))

        url = self.api_endpoints[fn.__name__]
        payload = dict([
            (k, v) for k, v in kwargs.items()
            if v is not None
        ])

        return self._post(url, payload)

    return wrapped


class PocketException(Exception):
    """
    Base class for all pocket exceptions
    http://getpocket.com/developer/docs/errors
    """
    description = r""
    pass


class InvalidQueryException(PocketException):
    description = r"Invalid request, please make sure you follow the documentation for proper syntax"
    pass


class AuthException(PocketException):
    description = r"Problem authenticating the user"
    pass


class RateLimitException(PocketException):
    """
    http://getpocket.com/developer/docs/rate-limits
    """
    description = r"User was authenticated, but access denied due to lack of permission or rate limiting"
    pass


class ServerMaintenanceException(PocketException):
    description = r"Pocket's sync server is down for scheduled maintenance."
    pass


EXCEPTIONS = {
    400: InvalidQueryException,
    401: AuthException,
    403: RateLimitException,
    503: ServerMaintenanceException,
}


class Pocket(object):
    """ Python API for http://getpocket.com
    """
    api_endpoints = dict(
        (method, 'v3/%s' % method)
        for method in "add,send,get".split(",")
    )

    def __init__(self, consumer_key, access_token=None):
        self.consumer_key = consumer_key
        self.access_token = access_token
        self.username = None

    def _post(self, sub_path, payload, **kwargs):
        assert isinstance(payload, dict)
        payload['consumer_key'] = self.consumer_key
        if self.access_token:
            payload['access_token'] = self.access_token
        r = requests.post('https://getpocket.com/' + sub_path,
                          headers={'X-Accept': 'application/json'},
                          json=payload,
                          **kwargs)
        ''':type r: requests.Response'''
        if r.status_code > 399:
            exception_cls = EXCEPTIONS.get(r.status_code, PocketException)
            raise exception_cls('%s. %s' % (exception_cls.description, r.headers.get('X-Error')))
        return r

    def authorize(self, port=8899):
        redirect_uri = 'http://127.0.0.1:{}'.format(port)

        # Step 1: Obtain a request token
        r = self._post('v3/oauth/request', payload=dict(redirect_uri=redirect_uri))
        request_token = r.json()['code']

        # Step 2: Redirect user to Pocket to continue authorization
        url = ('https://getpocket.com/auth/authorize?'
               'request_token={}&redirect_uri={}'.format(request_token, redirect_uri))
        http_authorise(url, port=port)

        # Step 3: Convert a request token into a Pocket access token
        r = self._post('v3/oauth/authorize', payload=dict(code=request_token))
        response_js = r.json()
        self.access_token = response_js['access_token']
        self.username = response_js['username']

    @method_wrapper
    def add(self, url, title=None, tags=None, tweet_id=None):
        """See http://getpocket.com/developer/docs/v3/add"""

    @method_wrapper
    def get(self, state=None, favorite=None, tag=None, contentType=None,
            sort=None, detailType=None, search=None, domain=None, since=None,
            count=None, offset=None):
        """See http://getpocket.com/developer/docs/v3/retrieve"""

    @method_wrapper
    def send(self, actions):
        """See http://getpocket.com/developer/docs/v3/modify"""


def get_temp_path(name):
    import tempfile
    return os.path.join(tempfile.gettempdir(), name)


def create_pocket_from_cache(consumer_key=None, cache_key_path=None):
    import json

    cache_key_path = cache_key_path or get_temp_path('__pocket_key.json')
    try:
        d = json.load(open(cache_key_path))
        access_token = d['access_token']
        consumer_key = d['consumer_key']
    except (IOError, ValueError, KeyError):
        access_token = None

    consumer_key = consumer_key or r'42042-fbf4887c38c189741b71f268'
    pocket = Pocket(consumer_key, access_token=access_token)
    if access_token is None:
        pocket.authorize()
        json.dump(dict(access_token=pocket.access_token,
                       consumer_key=consumer_key),
                  open(cache_key_path, 'wb'), indent=2)

    return pocket


def http_authorise(url, oauth_key=None, port=8888):
    import webbrowser
    import BaseHTTPServer
    import urlparse

    webbrowser.open(url)

    class ServerRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        code = None
        key = oauth_key

        def echo_html(self, content):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(content)
            self.wfile.close()

        def do_GET(self):
            if ServerRequestHandler.key is not None:
                qs = urlparse.parse_qs(urlparse.urlsplit(self.path).query)
                if ServerRequestHandler.key in qs:
                    ServerRequestHandler.code = qs[self.key][0]
            else:
                ServerRequestHandler.code = True
            if ServerRequestHandler.code:
                self.echo_html('''<html>
    <head>
    <meta charset="utf-8"/>
    <title>OK</title>
    </head>
    <body>Succeed.</body>
    </html> ''')

    httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', port), ServerRequestHandler)
    httpd.handle_request()
    while ServerRequestHandler.code is None:
        pass
    httpd.server_close()

    return ServerRequestHandler.code


if __name__ == '__main__':
    p = create_pocket_from_cache()
    print p.get(count=1).json()
