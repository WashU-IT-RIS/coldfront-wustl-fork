#!/usr/bin/env python3

import ldap3
import os
import smtplib
import subprocess
import sys

from argparse import ArgumentParser
from email.message import EmailMessage
from utils.coldfront_ad_utils import ColdfrontAdUtils

no_email = set()
cau = ColdfrontAdUtils()
print("E-mail Addresses")
for line in sorted(set(sys.stdin.readlines())):
    for uid in line.split(':')[-1].split(','):
        uid_resp = cau.get_user(uid)
        e_mail_address = uid_resp.get('attributes', {}).get('mail', 'N/A')
        if len(e_mail_address) == 0:
            no_email.add(uid)
            continue
        print(e_mail_address)
print("################################")
print("UserIDs Without E-mail Addresses")
for uid in sorted(no_email):
    print(uid)
exit(0)
