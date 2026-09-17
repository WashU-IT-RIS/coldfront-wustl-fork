#!/usr/bin/env python3

import os
import sys
import time

from argparse import ArgumentParser

class Oldest:
    path = None
    modified = time.time() + 86400

    def update(self, path, stat):
        min_stat = min([stat.st_atime, stat.st_mtime, stat.st_ctime])
        if min_stat >= self.modified:
            return
        self.path = path
        self.modified = min_stat

    def dump(self):
        def time_conv():
            return time.strftime(
                '%m/%d/%Y - %H:%M:%S GMT',
                time.gmtime(self.modified)
            )
        print(f'{self.path}, {time_conv()}')

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
oldest = Oldest()
for item in os.walk(args.path):
    oldest.update(item[0], os.stat(item[0]))
    for dir_file in item[2]:
        file_path = os.path.join(item[0], dir_file)
        if os.path.islink(file_path):
            continue
        oldest.update(file_path, os.stat(file_path))
oldest.dump()
sys.exit(0)
