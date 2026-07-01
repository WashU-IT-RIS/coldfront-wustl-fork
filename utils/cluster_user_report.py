#!/usr/bin/env python3

import ldap3
import subprocess
import sys

from utils.coldfront_ad_utils import ColdfrontAdUtils

service_group_map = {
    'Compute1': 'compute',
    'Compute2': 'compute2',
    'Storage': 'storage',
    'Storage1': 'storage1',
    'Storage2': 'storage2',
    'Storage3': 'storage3',
}
group_members = subprocess.check_output([
    'getent',
    'group',
    'storage',
])
sys.exit(0)
