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
for uid in sorted(set(sys.stdin.readlines())):
    print(cau.get_user(uid))
exit(0)
