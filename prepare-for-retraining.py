#!/usr/bin/env python3
#
# prepare string bitmask lists (CSVs) for each feature vector data point

import binascii
import datetime
import glob
import json
import os
import sys
import trackingthetrackers
from colorama import Fore, Style

files = sorted(glob.glob('*/*/*/*.json'))
if not files:
    print(Fore.RED + 'ERROR: no feature vector JSON files found! ' + Style.RESET_ALL)
    print('Usage: this expects files in <label>/<applicationId>/<versionCode>/<SHA256>.json')
    sys.exit(1)

features = dict()
for f in files:
    with open(f) as fp:
        data = json.load(fp)
    if sorted(data.keys()) != ['apks', 'meta']:
        print(Fore.RED + 'ERROR:' + f + Style.RESET_ALL)
        continue
    for apk in data['apks']:
        for k, v in apk.items():
            if k not in features:
                features[k] = set()
            if isinstance(v, str):
                features[k].add(v)
            else:
                for item in v:
                    features[k].add(item)

output = trackingthetrackers.init_search_space()
for k, v in features.items():
    output['apks'][0][k] = sorted(v)
with open('search_space.json', 'w') as fp:
    json.dump(output, fp, indent=2, sort_keys=True)
