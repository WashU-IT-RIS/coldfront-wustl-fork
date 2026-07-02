#!/usr/bin/env python3

import ldap3
import subprocess
import sys

from argparse import ArgumentParser
from utils.coldfront_ad_utils import ColdfrontAdUtils

service_group_map = {
    'Compute1': 'compute',
    'Compute2': 'compute2',
    'Storage': 'storage',
    'Storage1': 'storage1',
    'Storage2': 'storage2',
    'Storage3': 'storage3',
}
ap = ArgumentParser(
    description='RIS Services User Reporting Tool'
)
ap.add_argument(
    '-d',
    '--department',
    default=False,
    dest='department',
    help='Filter results by department',
    required=False,
    type=str
)
ap.add_argument(
    '-s',
    '--service',
    choices=list(service_group_map.keys()),
    default='all',
    dest='service',
    help='Generate a user list for a specific service (default: all services)',
    required=False,
    type=str
)
args = ap.parse_args()
if args.service == 'all':
    for service_name, group_name in service_group_map.items():
        group_members = subprocess.run(
            [
                'getent',
                'group',
                group_name
            ],
            capture_output=True
        )
else:
    group_members = subprocess.run(
        [
            'getent',
            'group',
            service_group_map.get(args.service)
        ],
        capture_output=True
    )
# example "getent group storage" output:
# storage:*:7151593:bmulligan,gunnar,ris-svc-sys-tester...
group_list = str(group_members).rstrip('\n').split(':')[3].split(',')
cau = ColdfrontAdUtils()
department_users = set()
if args.department is not False:
    department_users_resp = cau.get_department_users(args.department)
    for dept_user in department_users_resp:
        uid = dept_user.get('attributes', {}).get('sAMAccountName')
        dept = dept_user.get('attributes', {}).get('wustlEduHRPrimeDeptName')
        if uid:
            department_users.add(uid)
for member in sorted(group_list):
    if args.department is False:
        print(member)
    elif member in department_users:
        print(member)
sys.exit(0)
