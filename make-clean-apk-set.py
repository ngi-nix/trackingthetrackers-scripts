#!/usr/bin/env python3

import glob
import json
import os
import trackingthetrackers
from fdroidserver import common, index

config = dict()
config['jarsigner'] = 'jarsigner'
common.config = config
index.config = config

code_signatures_regex, network_signatures_regex = trackingthetrackers.get_exodus_signatures()

fdroid_apk_dir = '/data/malware-apks/known-good/f-droid.org'
set_dir = os.path.join(os.getcwd(), 'clean')

for f in glob.glob(os.path.join(set_dir, '*/*/*.apk')):
    os.unlink(f)
for d in glob.glob(os.path.join(set_dir, '*/[0-9]*')):
    os.rmdir(d)

apk_list = set()
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
            if package['packageName'] in packageNames_with_trackers:
                continue
            apk_path = os.path.join(fdroid_apk_dir, section, package['apkName'])
            symlink_path = os.path.join(set_dir,
                                        package['packageName'], str(package['versionCode']),
                                        package['hash'] + '.apk')
            os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
            print(apk_path, '\n\t', symlink_path)
            os.symlink(apk_path, symlink_path)

            apk_list.add((
                package['hash'],  # sha256
                None,  # sha1
                None,  # md5
                None,  # dex_date
                os.path.getsize(apk_path),
                package['packageName'],
                package['versionCode'],
                None,  # VirusTotal detection
                None,  # VirusTotal scan date
                None,  # dex size
                'f-droid.org',
            ))
            trackingthetrackers.write_feature_vector_json(symlink_path,
                                                          package['packageName'],
                                                          package['hash'])

trackingthetrackers.write_apk_list(apk_list, 'clean/apk_list.csv.gz')
# TODO get clean set from Exodus
