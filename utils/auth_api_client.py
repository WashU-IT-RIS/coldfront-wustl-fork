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

class ColdfrontParser(HTMLParser):
    csrf_token = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'input':
            return
        # print(f'Encountered a start tag: {tag}')
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
        # print(f'Encountered an end tag {tag}')
        pass

    def handle_data(self, data):
        # print(f'Encountered data {data}')
        pass

# see: https://groups.google.com/g/django-users/c/pQbRxuIeOzE
# curl -v -k -u 'user:pass' -e 'https://coldfront.ris.wustl.edu/user/login' 'https://coldfront.ris.wustl.edu/user/login' >/dev/null

# http_client.HTTPConnection.debuglevel = 1
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger('requests.packages.urllib3')
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

username = os.environ.get('API_USER', False)
if not username:
    user = input('Enter WUSTL key: ')
password = os.environ.get('API_PASS', False)
if not password:
    password = getpass.getpass('Enter Password: ')
with requests.Session() as session:
    loginUrl = 'https://coldfront.ris.wustl.edu/user/login?next='
    loginResp = session.get(
        loginUrl,
        verify=False
    )
    if loginResp.status_code != 200:
        print(loginResp.text)
        sys.exit(1)
    parser = ColdfrontParser()
    parser.feed(loginResp.text)
    # if parser.csrf_token:
        # print(f'Found token {parser.csrf_token}')
    # if session.cookies:
        # print(f'Session had cookies: {session.cookies}')
    session.headers.update({
        'Content-type': 'application/x-www-form-urlencoded',
        'Referer': loginUrl
    })
    # print(f'Pre-post session headers: {session.headers}')
    # print(f'Pre-post session cookies: {session.cookies}')
    loginResp = session.post(
        loginUrl,
        # data=f'csrfmiddlewaretoken={parser.csrf_token}&username={username}&password={password}'
        data={
            'csrfmiddlewaretoken': parser.csrf_token,
            'username': username,
            'password': password
        }
    )
    # print(f'Here is your "login" response code: {loginResp.status_code}')
    # print(f'Here is your "login" response headers: {loginResp.headers}')
    # print(f'Here is your "login" response page: {loginResp.text}')
    # print(f'Here are your session cookies: {session.cookies}')
    # print(f'Here are your login response cookies: {loginResp.cookies}')
    apiResp = session.get(
        'https://coldfront.ris.wustl.edu/qumulo/api/allocations',
        verify=False
    )
    print(apiResp.text)
# tokenheader = loginresp.headers.get('set-cookie', false)
# print(loginresp.headers)
# print(loginresp.text)
# sys.exit(0)
# if not tokenheader:
#     print(f'login failed: {loginresp.text}')
#     sys.exit(1)
# token = tokenheader.split('; ')[0].split('=')[-1]
# print(token)
# apiresp = requests.get(
#     'https://coldfront.ris.wustl.edu/qumulo/api/allocations',
#     auth=httpbasicauth(username, password),
#     headers={'authorization': f'token {token}'},
#     verify=false
#     )
# print(apiresp.headers)
# print(apiresp.text)
sys.exit(0)
