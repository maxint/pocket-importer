# coding: utf-8

import os
import requests


class PocketAPI(object):
    """ Python API for http://getpocket.com
    """
    def __init__(self, consumer_key, access_token=None, port=8899):
        self.consumer_key = consumer_key
        self.port = port
        self.access_token = access_token
        self.username = None

    def _post(self, sub_path, json, **kwargs):
        json = json or dict()
        json['consumer_key'] = self.consumer_key
        if self.access_token:
            json['access_token'] = self.access_token
        r = requests.post('https://getpocket.com/' + sub_path,
                          headers={'X-Accept': 'application/json'},
                          json=json,
                          timeout=kwargs.pop('timeout', 2),
                          **kwargs)
        return r

    def authorize(self):
        redirect_uri = 'http://127.0.0.1:{}'.format(self.port)

        # Step 1: Obtain a request token
        r = self._post('v3/oauth/request', json=dict(redirect_uri=redirect_uri))
        request_token = r.json()['code']

        # Step 2: Redirect user to Pocket to continue authorization
        fmt = r'https://getpocket.com/auth/authorize?request_token={}&redirect_uri={}'
        url = fmt.format(request_token, redirect_uri)
        from oauth_callback import http_authorise
        http_authorise(url, oauth_key=None, port=8899)

        # Step 3: Convert a request token into a Pocket access token
        r = self._post('v3/oauth/authorize', json=dict(code=request_token))
        response_js = r.json()
        self.access_token = response_js['access_token']
        self.username = response_js['username']

    def add(self, url, title=None, tags=None, tweet_id=None, **kwargs):
        """See http://getpocket.com/developer/docs/v3/add"""
        r = self._post('v3/add', json=dict(url=url, title=title,
                                           tags=tags, tweet_id=tweet_id), **kwargs)
        return r.json()

    def get(self, params, **kwargs):
        """See http://getpocket.com/developer/docs/v3/retrieve"""
        r = self._post('v3/get', json=params, **kwargs)
        return r.json()

    def send(self, actions, **kwargs):
        """See http://getpocket.com/developer/docs/v3/modify"""
        assert isinstance(actions, list)
        r = self._post('v3/send', json=dict(actions=actions), **kwargs)
        return r.json()


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
    pocket = PocketAPI(consumer_key, access_token=access_token)
    if access_token is None:
        pocket.authorize()
        json.dump(dict(access_token=pocket.access_token,
                       consumer_key=consumer_key),
                  open(cache_key_path, 'wb'), indent=2)

    return pocket


if __name__ == '__main__':
    p = create_pocket_from_cache()
    print p.get(dict(count=10))
