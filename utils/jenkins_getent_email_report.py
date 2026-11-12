#!/usr/bin/env python3

import ldap3
import os
import smtplib
import subprocess
import sys

from argparse import ArgumentParser
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from utils.coldfront_ad_utils import ColdfrontAdUtils

# Generate a list of e-mail addresses by reading  output from the
# "getent group <group name>" command from standard input.  Example "getent"
# output is shown here for the "compute-ris" group (getent group compute-ris):
#
# compute-ris:*:1208827:cspohl,mweil,sleong,a.santiago,tz-kai.lin...

def all_services_arg(arg):
    return arg in [None, 'all', 'All']

def generate_message_content(service: str, filenames: list):
    return(
        """
Hello-

You are receiving this message because you or someone on your behalf requested
an e-mail address report for users of {} provided by RIS.
Please see the attached {} for the requested {}:

\t{}

Please note that not all user IDs configured to use the service may be
associated with valid e-mail addresses.  The user IDs without e-mail addresses
have been appended to the end of the report.

Thank you,

RIS Application Engieering
        """.format(
            service,
            'files' if len(filenames) > 1 else 'file',
            'reports' if len(filenames) > 1 else 'report',
            '\n\t'.join(filenames)
        )
    )


def generate_file_name(service):
    today = date.today()
    return (
        f'{service}-UserList-'
        f'{today.year:04d}{today.month:02d}{today.day:02d}.csv'
    )

def generate_report(group, debug=False):
    report = ''
    no_email = set()
    cau = ColdfrontAdUtils()
    report += "E-mail Addresses\n"
    completed_proc = subprocess.run(
        ['/usr/bin/getent', 'group', group],
        capture_output=True
    )
    for line in completed_proc.stdout.decode('utf-8').split('\n'):
        for uid in list(sorted(set(line.split(':')[-1].split(',')))):
            if not uid:
                if debug:
                    print(f'DEBUG Skipping bad uid: {uid}.')
                continue
            uid_resp = cau.get_user(uid)
            e_mail_address = uid_resp.get('attributes', {}).get('mail', 'N/A')
            if len(e_mail_address) == 0:
                no_email.add(uid)
                continue
            report += f'{e_mail_address}\n'
    report += (
        "####################################\n"
        "# UserIDs Without E-mail Addresses #\n"
        "####################################\n"
    )
    for uid in sorted(no_email):
        report += f'{uid}\n'
    return bytes(report, encoding='utf-8')

service_group_map = {
    'All': None,
    'Compute1': 'compute',
    'Compute2': 'compute2',
    'Storage': 'storage',
    'Storage1': 'storage1',
    'Storage2': 'storage2',
    'Storage3': 'storage3',
}
ap = ArgumentParser()
ap.add_argument(
    '-d',
    '--debug',
    action='store_true',
    default=False,
    required=False
)
ap.add_argument(
    '-s',
    '--service',
    choices=list(service_group_map.keys()).append(None),
    dest='service',
    required=False,
    type=str,
)
args = ap.parse_args()
msg = EmailMessage()
msg['To'] = os.environ.get('REPORT_RECIPIENT', 'bmulligan@wustl.edu')
msg['From'] = 'ris-svc-builder@wustl.edu'
if not all_services_arg(args.service):
    msg['Subject'] = f'RIS User E-Mail Address Report for {args.service}'
    report_filename = generate_file_name(args.service)
    report_data = generate_report(service_group_map[args.service], args.debug)
    msg.set_content(
        generate_message_content(
            f'the {args.service} service',
            [report_filename]
        )
    )
    msg.add_attachment(
        report_data,
        maintype='text',
        subtype='plain',
        filename=report_filename
    )
else:
    msg['Subject'] = f'RIS User E-Mail Address Report for All Services'
    reports_dict = {}
    for service_name, group_name in service_group_map.items():
        if service_name == 'All':
            continue
        report_filename = generate_file_name(service_name)
        reports_dict[report_filename] = generate_report(group_name, args.debug)
    msg.set_content(
        generate_message_content(
            'all Compute and Active Storage services',
            list(reports_dict.keys())
        )
    )
    for filename, report_data in reports_dict.items():
        msg.add_attachment(
            report_data,
            maintype='text',
            subtype='plain',
            filename=filename
        )

with smtplib.SMTP('smtp.ris.wustl.edu') as smtp:
    smtp.send_message(msg)
sys.exit(0)
