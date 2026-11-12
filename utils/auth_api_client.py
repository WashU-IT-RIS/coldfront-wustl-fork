#!/usr/bin/env python3

import getpass
import logging
import os
import re
import requests
import sys
import urllib3

import http.client as http_client

from html.parser import HTMLParser
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# see: https://groups.google.com/g/django-users/c/pQbRxuIeOzE

def enable_http_debugging():
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger('requests.packages.urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

class ColdfrontParser(HTMLParser):
    csrf_token = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'input':
            return
        for k, v in attrs:
            if k == 'type':
                if v != 'hidden':
                    break
            if k == 'name':
                if v.lower() != 'csrfmiddlewaretoken':
                    break
            if k == 'value':
                self.csrf_token = v

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass

username = os.environ.get('API_USER', False) or input('Enter WUSTL key: ')
password = os.environ.get('API_PASS', False) or \
    getpass.getpass('Enter Password: ')
coldfront_base_url = (
    os
    .environ 
    .get(
        'COLDFRONT_BASE_URL',
        'https://coldfront-qa.ris.wustl.edu'
    )
    .rstrip('/')
)
with requests.Session() as session:
    loginUrl = f'{coldfront_base_url}/user/login?next='
    loginResp = session.get(
        loginUrl,
        verify=False
    )
    if loginResp.status_code != 200:
        print(loginResp.text)
        sys.exit(1)
    parser = ColdfrontParser()
    parser.feed(loginResp.text)
    session.headers.update({
        'Content-type': 'application/x-www-form-urlencoded',
        'Referer': loginUrl
    })
    loginResp = session.post(
        loginUrl,
        data={
            'csrfmiddlewaretoken': parser.csrf_token,
            'username': username,
            'password': password
        },
        verify=False
    )
    apiResp = session.get(
        f'{coldfront_base_url}/qumulo/api/allocations',
        verify=False
    )
    print(apiResp.text)
sys.exit(0)
