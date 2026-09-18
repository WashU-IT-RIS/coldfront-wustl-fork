#!/usr/bin/env python3

import os
import sys
import time

from argparse import ArgumentParser

class Latest:
    path = None
    modified = 0.0

    def __init__(self, path):
        self.path = path

    def update(self, path, stat):
        max_stat = max([stat.st_atime, stat.st_mtime, stat.st_ctime])
        if max_stat <= self.modified:
            return
        self.modified = max_stat

    def dump(self):
        def time_conv():
            return time.strftime(
                '%m/%d/%Y - %H:%M:%S GMT',
                time.gmtime(self.modified)
            )
        print(f'{self.path},{time_conv()}')

ap = ArgumentParser(
    description='Allocation "last used" tool'
)
ap.add_argument(
    '-p',
    '--path',
    dest='path',
    help='The path to inspect',
    required=True
)
args = ap.parse_args()
latest = Latest()
for item in os.walk(args.path):
    latest.update(item[0], os.stat(item[0]))
    for dir_file in item[2]:
        file_path = os.path.join(item[0], dir_file)
        if os.path.islink(file_path):
            continue
        latest.update(file_path, os.stat(file_path))
latest.dump()
sys.exit(0)
