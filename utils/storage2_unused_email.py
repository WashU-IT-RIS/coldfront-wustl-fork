#!/usr/bin/env python3

import subprocess
import sys

from coldfront_ad_utils import ColdfrontAdUtils

# Example:
#            0,              1, 2,              3,                4,             5
# Storage Name,Filesystem Path,PI,Billing Contact,Technical Contact,Storage Groups
# abrummett,/storage2/fs1/abrummett,abrummett,abrummett,abrummett,storage-abrummett-rw|storage-abrummett-ro
# alexxai,/storage2/fs1/alexxai,alexxai,alexxai,alexxai,storage2-alexxai-rw|storage2-alexxai-ro

cau = ColdfrontAdUtils()
def email_from_contact_handler(key, email_set, synthetic_set):
    global cau
    user_email = cau.get_user_email(key)
    if type(user_email) == type(list()):
        synthetic_set.add(f'{key}@wustl.edu')
    else:
        email_set.add(user_email)

print(f'Storage Name,Filesystem Path,E-mail Addresses,WUSTL Key E-mail Addresses')
for line in sys.stdin.readlines()[1:]:
    email_addresses = set()
    synth_addresses = set()
    columns = line.split(',')
    for contact in columns[2:5]:
        if len(contact) == 0:
            print(f'SKIPPING contact user {contact} from {columns[2:5]}')
            continue
        email_from_contact_handler(contact, email_addresses, synth_addresses)
    for group in columns[5].split('|'):
        # Example getent output
        #                       0,1,      2,                3
        # storage2-azheleznyak-rw:*:7146387:user1,user2,user3
        getent_result = subprocess.run(
            ['/usr/bin/getent', 'group', group],
            capture_output=True,
            encoding='utf-8'
        )
        try:
            group_users = getent_result.stdout.rstrip().split(':')[3].split(',')
        except Exception as e:
            # print(
            #    f'got exception {e} on {getent_result.stdout}; '
            #    f'group was {group}'
            # )
            continue
        if len(group_users) == 0:
            continue
        for user in group_users:
            if len(user) == 0:
                print(f'SKIPPING group user {user} from {getent_result.stdout}')
                continue
            email_from_contact_handler(user, email_addresses, synth_addresses)
    print(
        (
            ','.join(columns[:2]) + ',' + '|'.join(email_addresses) + ',' +
            '|'.join(synth_addresses)
        )
    )
sys.exit(0)
