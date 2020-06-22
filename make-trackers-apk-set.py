#!/usr/bin/env python3

import binascii
import csv
import functools
import glob
import gzip
import hashlib
import io
import json
import os
import sys
import zipfile
from androguard.core.bytecodes.apk import get_apkid
from fdroidserver import common, index


def gen_row(f):
    sha256 = hashlib.sha256()
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    with open(f, 'rb') as fp:
        for chunk in iter(functools.partial(fp.read, 8192), b''):
            sha256.update(chunk)
            sha1.update(chunk)
            md5.update(chunk)
    try:
        with zipfile.ZipFile(f) as zf:
            classes_dex = zf.getinfo('classes.dex')
            dt = classes_dex.date_time
            dex_date = '%04d-%02d-%02d %02d:%02d:%02d' % dt
            appid, versionCode, versionName = get_apkid(f)
        return (
            binascii.hexlify(sha256.digest()).decode(),
            binascii.hexlify(sha1.digest()).decode(),
            binascii.hexlify(md5.digest()).decode(),
            str(dex_date),
            os.path.getsize(f),
            appid,
            versionCode
        )
    except (KeyError, Exception) as e:
        print('\n', f, e)
    return tuple()


config = dict()
config['jarsigner'] = 'jarsigner'
common.config = config
index.config = config

ikarus_adware_apk_dir = '/data/malware-apks/ikarus/adware'
fdroid_apk_dir = '/data/malware-apks/known-good/f-droid.org'
set_dir = os.path.join(os.getcwd(), 'trackers')

for f in glob.glob(os.path.join(set_dir, '*/*/*.apk')):
    os.unlink(f)
for d in glob.glob(os.path.join(set_dir, '*/[0-9]*')):
    os.rmdir(d)

apk_list = set()
apk_list_file = 'trackers/apk_list.csv.gz'
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

for f in glob.glob(os.path.join(ikarus_adware_apk_dir, '*')):
    if os.path.isdir(f):
        continue
    row = gen_row(f)
    if row:
        apk_list.add(row)
        if row[5] and row[6]:
            symlink_path = os.path.join(set_dir, row[5], row[6], row[0] + '.apk')
            os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
            print(f, '\n\t', symlink_path)
            os.symlink(f, symlink_path)

print('writing', apk_list_file)
with gzip.GzipFile(apk_list_file, 'w') as gz:
    buff = io.StringIO()
    writer = csv.writer(buff)
    writer.writerows(apk_list)
    gz.write(buff.getvalue().encode())

# TODO get tracker set from Exodus
