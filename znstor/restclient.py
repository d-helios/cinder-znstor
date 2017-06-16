# -*- coding: utf-8 -*-
"""Rest client for restapi module.
"""

import sys
import logging
from requests.auth import HTTPBasicAuth
import requests

# TODO: set debug level from cinder driver
LOGLEVEL = logging.ERROR

LOG = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
LOG.addHandler(out_hdlr)
LOG.setLevel(LOGLEVEL)


class RestClientURL(object):
    """znstor rest client"""

    def __init__(self, **kwargs):
        """Initialize a REST client
        :key management_address: Storage management interface (ip or dns)
        :key api_version: Storage RestApi version (only v1 supported)
        :key pool: zpoolID
        :key domain: znstor domainID, actually is first level dataset in pool.
        :key timeout: request timeout. Default is 180 seconds.
        :key user: znstor user
        :key passwd: znstor password
        """

        self.management_address = kwargs.get('management_address', '127.0.0.1:10987')
        self.api_version = kwargs.get('api_version', 'v1')
        self.pool = kwargs.get('pool', 'tank')
        self.domain = kwargs.get('domain', 'default')
        self.timeout = kwargs.get('timeout', 180)
        self.mng_user = kwargs.get('user', 'znstor')
        self.mng_passwd = kwargs.get('passwd', 'nevada')
        self.basic_auth = HTTPBasicAuth(self.mng_user, self.mng_passwd)

        self.schema = kwargs.get('schema', 'http://')
        self.headers = {'Content-Type': 'application/json',
                        'User-Agent': 'znstor-RESTClient'}

    def projects_base_path(self):
        """build rest url path"""
        return """{protocol}{management_address}/api/{version}\
/storage/domains/{domain}/pools/{pool}/projects""".format(
            protocol=self.schema,
            management_address=self.management_address,
            version=self.api_version,
            domain=self.domain,
            pool=self.pool
        )

    def hosts_base_path(self):
        """build rest url path"""
        return "{protocol}{management_address}/api/{version}/storage/hosts".format(
            protocol=self.schema,
            management_address=self.management_address,
            version=self.api_version,
        )

    def targets_base_path(self):
        """build rest url path"""
        return "{protocol}{management_address}/api/{version}/storage/targets".format(
            protocol=self.schema,
            management_address=self.management_address,
            version=self.api_version,
        )

    def request(self, path, method, body=None):
        """Make an HTTP request and return the result
        :param path: Path used with the initialized URL to make a request
        :param method: HTTP request type (GET, POST, PUT, DELETE)
        :param body: HTTP body of request
        """

        HTTPBasicAuth(self.mng_user, self.mng_passwd)

        LOG.debug('PATH: %s, METHOD: %s, BODY: %s' % (path, method, body))

        response = requests.request(method=method,
                                    url=path,
                                    timeout=self.timeout,
                                    json=body,
                                    headers=self.headers,
                                    auth=self.basic_auth)

        return response

    def get(self, path):
        """get method"""
        return self.request(path, 'GET', '')

    def put(self, path, body=''):
        """put method"""
        return self.request(path, 'PUT', body)

    def post(self, path, body=''):
        """post method"""
        return self.request(path, 'POST', body)

    def delete(self, path, body=''):
        """delete method"""
        return self.request(path, 'DELETE', body)
