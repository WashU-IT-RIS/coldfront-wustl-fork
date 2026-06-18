#!/usr/bin/env python3

import json
import os
import requests
import sys
import urllib3

from getpass import getpass
from requests.auth import HTTPBasicAuth

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
        'attribute=name,status,sponsor,technical_contact,billing_contact,'
        'acl_group_members'
    ),
    auth=(username, password),
    verify=False
)
service_data = resp.json().get('data', [])
if len(service_data) == 0:
    print('User data unavailable')
    sys.exit(1)
storage_pis = list()
storage_users = set()
for service in service_data:
    if str(service.get('status', None)).lower() != 'active':
        continue
    # print(json.dumps(service))
    storage_pis.append({
        'pi': clean_id(service.get('sponsor', 'N/A')),
        'storage_name': service.get('name', 'N/A')
    })
    for user in str(service.get('acl_group_members', '')).split(','):
        storage_users.add(clean_id(user))
    # Examples:
    # {
    #   "name": "/vol/rdcw-fs2/tychele2",
    #   "status": "active",
    #   "sponsor": "tychele",
    #   "technical_contact": "tychele@wustl.edu",
    #   "billing_contact": null,
    #   "acl_group_members": "tychele",
    #   "_service_provision": 15001199
    # }
    # {
    #   "name": "compute-khengen",
    #   "status": "active",
    #   "sponsor": "khengen",
    #   "technical_contact": "thuet",
    #   "billing_contact": "khengen",
    #   "acl_group_members": "WG-banksi,aidans,bryan.h,bzachary,c.dumoulin,chopra.r,d.s.wu,f.prescott,farris.c,g.tolossa,jacob.amme,e.halla,elisa.pappagallo,emilyshen,fosque,j.a.meza,jimmy.zhong,k.levi,k.ronayne,kbhaskarannair,kathleen.lund,khengen,l.yuqi,mcgregor,n.somia,s.funderburk,sahara.ensley,samantha.z,sbrunwa,song.zixuan,vrsinha,xu.yifan",
    #   "_service_provision": 15000414
    # }
with open('./Storage1-AllocationPIs.csv', 'w') as pia:
    for allocation in storage_pis:
        pia.write(f'{allocation["storage_name"]},{allocation["pi"]}\n')
with open('./Storage1-UserList.csv', 'w') as sus:
    for user in storage_users:
        sus.write(f'{user}\n')
sys.exit(0)
