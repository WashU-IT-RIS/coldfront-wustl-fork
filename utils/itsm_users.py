#!/usr/bin/env python3

import json
import os
import requests
import sys
import urllib3

from getpass import getpass
from requests.auth import HTTPBasicAuth
from utils.coldfront_ad_utils import ColdfrontAdUtils

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_id(userid):
    return userid.split('@')[0].strip()

creds =  os.environ.get('ITSM_CREDS', None)
if creds is None:
    username = input('Enter ITSM username: ')
    password = getpass('Enter ITSM password: ')
else:
    username, password = creds.split('/')
resp = requests.get(
    (
        'https://itsm.ris.wustl.edu:8443/v2/rest/attr/info/service_provision?'
        'attribute=name,status,sponsor'
    ),
    auth=(username, password),
    verify=False
)
service_data = resp.json().get('data', [])
if len(service_data) == 0:
    print('User data unavailable')
    sys.exit(1)
storage_pis = list()
ad_utils = ColdfrontAdUtils()
for service in service_data:
    if str(service.get('status', None)).lower() != 'active':
        continue
    # print(json.dumps(service))
    storage_pis.append({
        'pi': clean_id(service.get('sponsor', 'N/A')),
        'storage_name': service.get('name', 'N/A')
    })
with open('./Storage1-AllocationPIs.csv', 'w') as pia:
    pia.write('Allocation Name,Sponsor/PI\n')
    for allocation in storage_pis:
        pia.write(f'{allocation["storage_name"]},{allocation["pi"]}\n')
sys.exit(0)
