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

ikarus_adware_apk_dir = '/data/malware-apks/ikarus/adware'
fdroid_apk_dir = '/data/malware-apks/known-good/f-droid.org'
set_dir = os.path.join(os.getcwd(), 'trackers')

for f in glob.glob(os.path.join(set_dir, '*/*/*.apk')):
    os.unlink(f)

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
            if package['packageName'] not in packageNames_with_trackers:
                continue
            apk_path = os.path.join(fdroid_apk_dir, section, package['apkName'])
            symlink_path = os.path.join(set_dir,
                                        package['packageName'], str(package['versionCode']),
                                        package['hash'] + '.apk')
            if os.path.exists(symlink_path):
                print('SKIPPING DUPLICATE:', symlink_path)
                continue
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

for f in sorted(glob.glob(os.path.join(ikarus_adware_apk_dir, '*'))):
    if os.path.isdir(f):
        continue
    row = trackingthetrackers.gen_row(f)
    if row:
        apk_list.add(row)
        if row[5] and row[6]:
            symlink_path = os.path.join(set_dir, row[5], row[6], row[0] + '.apk')
            os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
            print(f, '\n\t', symlink_path)
            os.symlink(f, symlink_path)
            trackingthetrackers.write_feature_vector_json(symlink_path, row[5], row[0])

trackingthetrackers.write_apk_list(apk_list, 'trackers/apk_list.csv.gz')

# TODO get tracker set from Exodus
