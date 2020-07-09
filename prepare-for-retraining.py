#!/usr/bin/env python3
#
# prepare string bitmask lists (CSVs) for each feature vector data point

import binascii
import datetime
import git
import glob
import json
import os
import sys
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

output = {
    'features': features,
    'meta': {
        'ver': '0.2.0',
        'generated': datetime.datetime.now().isoformat(),
        'generatedBy': __file__,
    },
}
if os.path.isdir('.git'):
    repo = git.repo.Repo('.')
    output['meta']['sourceDataCommitId'] = binascii.hexlify(bytearray(repo.head.commit.binsha)).decode()

script_git_path = os.path.dirname(__file__)
if os.path.isdir(os.path.join(script_git_path, '.git')):
    repo = git.repo.Repo(script_git_path)
    output['meta']['generatedByCommitId'] = binascii.hexlify(bytearray(repo.head.commit.binsha)).decode()

for k, v in features.items():
    output['features'][k] = sorted(v)
with open('feature_vectors.json', 'w') as fp:
    json.dump(output, fp, indent=2, sort_keys=True)
