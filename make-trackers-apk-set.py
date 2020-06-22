#!/usr/bin/env python3

import glob
import json
import os
import sys
from fdroidserver import common, index

config = dict()
config['jarsigner'] = 'jarsigner'
common.config = config
index.config = config

local_apk_dir = '/data/malware-apks/known-good/f-droid.org'
set_dir = os.path.join(os.getcwd(), 'trackers')

for f in glob.glob(os.path.join(set_dir, '*/*/*.apk')):
    os.unlink(f)
for d in glob.glob(os.path.join(set_dir, '*/[0-9]*')):
    os.rmdir(d)

for section in ['repo', 'archive']:
    packageNames_with_trackers = set()
    url = 'https://ftp.fau.de/fdroid/' + section
    indexdata = None
    if os.path.exists('index-v1.json'):
        with open('index-v1.json') as fp:
            indexdata = json.load(fp)
    else:
        indexdata, etag = index.download_repo_index(url, verify_fingerprint=False)
    for app in indexdata['apps']:
        for antiFeature in app.get('antiFeatures', []):
            if antiFeature == 'Tracking':
                packageNames_with_trackers.add(app['packageName'])
    for appid, packages in indexdata['packages'].items():
        for package in packages:
            if package['packageName'] not in packageNames_with_trackers:
                continue
            apk_path = os.path.join(local_apk_dir, section, package['apkName'])
            symlink_path = os.path.join(set_dir,
                                        package['packageName'], str(package['versionCode']),
                                        package['hash'] + '.apk')
            os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
            print(apk_path, '\n\t', symlink_path)
            os.symlink(apk_path, symlink_path)

# TODO get clean set from Exodus
# TODO make androzoo index output