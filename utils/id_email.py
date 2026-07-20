#!/usr/bin/env python3

import ldap3
import os
import smtplib
import subprocess
import sys

from argparse import ArgumentParser
from email.message import EmailMessage
from utils.coldfront_ad_utils import ColdfrontAdUtils

cau = ColdfrontAdUtils()
for line in sorted(set(sys.stdin.readlines())):
    for uid in line.split(':')[-1].split(','):
        uid_resp = cau.get_user(uid)
        print(uid_resp.get('attributes', {}).get('mail', 'N/A'))
exit(0)
