#!/usr/bin/env python3

import ldap3
import os
import smtplib
import subprocess
import sys
import time

from argparse import ArgumentParser
from email.message import EmailMessage
from utils.coldfront_ad_utils import ColdfrontAdUtils

def generate_file_name(service):
    filename = None
    tm = time.localtime(time.time())
    filename_ts = (
        f'{tm.tm_year:04d}{tm.tm_mon:02d}{tm.tm_mday:02d}'
        f'{tm.tm_hour:02d}{tm.tm_min:02d}'
    )
    if service == 'all':
        filename = f'RIS-User-Report-{filename_ts}.csv'
    else:
        filename = f'RIS-{service}-User-Report-{filename_ts}.csv'
    return filename

def generate_message_content(service, filename, filter_string):
    def filter_sentence():
        if not filter_string:
            return ''
        return(
            '\nThe list was filtered to include users associated with '
            f'department(s) matching the following string: {filter_string}\n'
        )
        """
Hello-

You are receiving this message because you or someone on your behalf requested
a user report for {} provided by RIS.  Please see the attached file, {}, for the
requested report.
{}
Thank you,

RIS Application Engieering
        """.format(service, filename, filter_sentence())
    )

def generate_list(group_list, department, department_users, ad_object=None):
    output_list = ''
    for member in sorted(set(group_list)):
        dept_resp = department_name = None
        try:
            dept_resp = ad_object.get_user_department(member)
        except ValueError:
            pass
        if dept_resp:
            department_name = dept_resp \
                .get('attributes', {}) \
                .get('wustlEduHRPrimeDeptName', False)
        if department is False:
            output_list += f'{member}'
        elif member in department_users:
            output_list += f'{member}'
        else:
            continue
        if department_name:
            output_list += f',{department_name}'
        output_list += '\n'
    return bytes(output_list, encoding='utf-8')

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
    help=(
        'Filter results by department--'
        'can also be passed with REPORT_DEPARTMENT'
    ),
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
if args.department is False:
    args.department = os.environ.get('REPORT_DEPARTMENT', False)
# example "getent group storage" output:
# storage:*:7151593:bmulligan,gunnar,ris-svc-sys-tester...
if args.service == 'all':
    group_list = []
    for service_name, group_name in service_group_map.items():
        getent_cp = subprocess.run(
            [
                'getent',
                'group',
                group_name
            ],
            capture_output=True
        )
        group_list.extend(
            str(getent_cp.stdout).rstrip('\n').split(':')[3].split(',')
        )
else:
    getent_cp = subprocess.run(
        [
            'getent',
            'group',
            service_group_map.get(args.service)
        ],
        capture_output=True
    )
    group_list = list(
        str(getent_cp.stdout).rstrip('\n').split(':')[3].split(',')
    )
cau = ColdfrontAdUtils()
department_users = set()
if args.department is not False:
    department_users_resp = cau.get_department_users(args.department)
    for dept_user in department_users_resp:
        uid = dept_user.get('attributes', {}).get('sAMAccountName')
        dept = dept_user.get('attributes', {}).get('wustlEduHRPrimeDeptName')
        if uid:
            department_users.add(uid)
report_data = generate_list(group_list, args.department, department_users, cau)
if os.environ.get('JENKINS_HOME', False):
    if args.service.lower() == 'all':
        service_label = 'All Services'
    else:
        service_label = f'the {args.service} Service'
    attachment_filename = generate_file_name(args.service)
    msg = EmailMessage()
    msg['Subject'] = f'RIS User Report for {service_label}'
    msg['To'] = os.environ.get('REPORT_RECIPIENT', 'bmulligan@wustl.edu')
    msg['From'] = 'ris-svc-builder@wustl.edu'
    msg.set_content(
        generate_message_content(
            service_label,
            attachment_filename,
            args.department
        )
    )
    msg.add_attachment(
        report_data,
        maintype='text',
        subtype='plain',
        filename=attachment_filename
    )
    with smtplib.SMTP('smtp.ris.wustl.edu') as smtp:
        smtp.send_message(msg)
else:
    print(str(report_data, encoding='utf-8'), end='')
sys.exit(0)
