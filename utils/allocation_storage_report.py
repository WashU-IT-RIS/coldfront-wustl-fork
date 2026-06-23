#!/usr/bin/env python3

import re
import sys

from argparse import ArgumentParser
from coldfront_ad_utils import ColdfrontAdUtils

ap = ArgumentParser(
    description='RIS Allocation PI Report Utility'
)
ap.add_argument(
    '-a',
    '--allocation-lists',
    default='./',
    dest='root',
    help=(
        'Path to the directory containing the allocation list files '
        '(default: current directory)'
    ),
    required=False,
    type=str
)
args = ap.parse_args()
cau = ColdfrontAdUtils()
allocations = list()
for user_file in ['Storage1', 'Storage2', 'Storage3']:
    path = f'./{user_file}-AllocationPIs.csv'
    if os.path.isfile(path):
        with open(path) as sul:
            allocations.extend([x.rstrip() for x in sul.readlines()])
    else:
        print(f'Warning: no input found for {service}; skipping.')
if len(allocations):
    print('Allocation Name,PI Name,PI User ID,Department Name', flush=True)
    for allocation in allocations:
        if not allocation:
            continue
        allocation_name, userid = allocation.split(',')
        try:
            ad_resp = cau.get_user_department(userid)
        except ValueError:
            continue
        department_name = ad_resp.get('attributes', {}) \
                            .get('wustlEduHRPrimeDeptName', 'N/A')
        if not re.match(r'^DOM - ', str(department_name)):
            continue
        display_name = ad_resp.get('attributes', {}) \
                        .get('wustlEduOLSDisplayName', 'N/A')
        print(f'{allocation_name},{display_name},{userid},{department_name}', flush=True)
else:
    print('No allocations to report')
    sys.exit(1)
sys.exit(0)
