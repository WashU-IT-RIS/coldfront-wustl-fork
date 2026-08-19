#!/usr/bin/env python3

import os
import re
import sys

from argparse import ArgumentParser
from coldfront_ad_utils import ColdfrontAdUtils

ap = ArgumentParser(
    description='RIS Storage User Report Utility'
)
ap.add_argument(
    '-u',
    '--user-lists',
    default='./',
    dest='root',
    help=(
        'Path to the directory containing the user list files '
        '(default: current directory)'
    ),
    required=False,
    type=str
)
args = ap.parse_args()
cau = ColdfrontAdUtils()
users = list()
for service in ['Storage1', 'Storage2', 'Storage3']:
    path = f'{args.root}/{service}-UserList.csv'
    if os.path.isfile(path):
        with open(path) as sul:
            users.extend([x.rstrip() for x in sul.readlines()])
    else:
        print(f'Warning: no input found for {service}; skipping.')
if len(users):
    print('User Name,User ID,Department Name', flush=True)
    for user in set(users):
        if not user:
            continue
        try:
            ad_resp = cau.get_user_department(user)
        except ValueError:
            continue
        department_name = ad_resp.get('attributes', {}) \
                            .get('wustlEduHRPrimeDeptName', 'N/A')
        # print(f'DEBUG: {department_name}')
        if not re.match(r'^DOM - ', str(department_name)):
            continue
        display_name = ad_resp.get('attributes', {}) \
                        .get('wustlEduOLSDisplayName', 'N/A')
        print(f'{display_name},{user},{department_name}', flush=True)
else:
    print('No users to report')
    sys.exit(1)
sys.exit(0)
