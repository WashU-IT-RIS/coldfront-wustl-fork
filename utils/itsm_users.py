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

def resolve_project_directories(comment):
    dir_projects = comment.get('dir_projects', False)
    projects = comment.get('projects', False)
    if not any(
        [x for x in [dir_projects, projects] if type(x) == type(dict())]
    ):
        return None
    return_dict = {}
    if type(dir_projects) == type(dict()):
        return_dict = dir_projects
    if type(projects) == type(dict()):
        if len(return_dict) > 0:
            for key, val in projects.items():
                if key not in projects:
                    return_dict[key] = val
        else:
            return_dict = projects
    return return_dict

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
        'acl_group_members,comment'
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
ad_utils = ColdfrontAdUtils()
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
    comment_data = service.get('comment', '{}')
    if comment_data is None:
        continue
    comment = json.loads(comment_data)
    project_directories = resolve_project_directories(comment)
    if project_directories is None:
        continue
    for directory_name, directory_data in project_directories.items():
        rwro = []
        rw = directory_data.get('rw', [])
        ro = directory_data.get('ro', [])
        if rw is not None:
            rwro.extend(rw)
        if ro is not None:
            rwro.extend(ro)
        print(f'Got some project directory users: {rwro}')
        for uid in rwro:
            resolved_id = ad_utils.resolve_id(uid)
            if resolved_id['id_is_user']:
                storage_users.add(uid)
            elif resolved_id['id_is_group']:
                storage_users.update(resolved_id['data'])
            else:
                print(f'WARNING: skipping non-user, non-group ID: {uid}')
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
# sys.exit(0)
with open('./Storage1-AllocationPIs.csv', 'w') as pia:
    for allocation in storage_pis:
        pia.write(f'{allocation["storage_name"]},{allocation["pi"]}\n')
with open('./Storage1-UserList.csv', 'w') as sus:
    for user in storage_users:
        sus.write(f'{user}\n')
sys.exit(0)
