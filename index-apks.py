#!/usr/bin/env python3
#
# generate an index of an APK collection following the pattern in
# https://androzoo.uni.lu/lists
#
# run in the background at low priority with:
#   nice -n 19 ionice -c3 ~/code/trackingthetrackers/scripts/index-apks.py


import base64
import binascii
import csv
import functools
import glob
import gzip
import hashlib
import io
import logging
import os
import re
import zipfile
from androguard.core.bytecodes.apk import get_apkid
from datetime import datetime

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


logging.getLogger("androguard.axml").setLevel(logging.ERROR)
logging.getLogger("androguard.session").setLevel(logging.ERROR)

apk_list = set()
apk_list_file = 'apk_list.csv.gz'
if os.path.exists(apk_list_file):
    with gzip.open(apk_list_file, 'rt') as fp:
        reader = csv.reader(fp)
        for row in reader:
            apk_list.add(tuple(row))

for f in sorted(glob.glob('/data/*/*/*/*/*/*.apk')
                + glob.glob('/data/ttt-apks/random-google-play/*.apk')
                + glob.glob('/data/malware-apks/ikarus/*/*_[0-9]*')
                + glob.glob('/data/malware-apks/github.com/*/*/*/*/*/*.apk')):
    basename = os.path.basename(f)
    if os.path.isdir(f):
        continue
    row = gen_row(f)
    if row:
        print('.', end='', flush=True)
        apk_list.add(row)

print('writing', apk_list_file)
with gzip.GzipFile(apk_list_file, 'w') as gz:
    buff = io.StringIO()
    writer = csv.writer(buff)
    writer.writerows(apk_list)
    gz.write(buff.getvalue().encode())
