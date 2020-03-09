#!/usr/bin/env python3


import glob
import logging
import os
import sys
from androguard.core.bytecodes.apk import get_apkid
from fdroidserver import common


if len(sys.argv) != 2:
    print('Usage:', sys.argv[0], '[destdir]')
    sys.exit(1)

basedir=sys.argv[1]

if not os.path.isdir(sys.argv[1]) or len(os.listdir(basedir)) > 0:
    print('ERROR:', sys.argv[1], 'must exist and be empty!')
    sys.exit(1)

logging.getLogger("androguard.axml").setLevel(logging.ERROR)
logging.getLogger("androguard.session").setLevel(logging.ERROR)

for f in sorted(glob.glob('*.apk')):
    apk_dir = None
    try:
        appid, versionCode, versionName = get_apkid(f)
        apk_dir = os.path.join(basedir, appid, str(versionCode))
    except (KeyError, Exception) as e:
        aapt_line = "aapt dump badging %s | head -1" % f
        m = common.APK_ID_TRIPLET_REGEX.match(os.popen(aapt_line).read())
        if m:
            apk_dir = os.path.join(basedir, m.group(1), m.group(2))
            print(m.group(1), m.group(2), m.group(3))
        else:
            errors_dir = os.path.join(basedir, 'ERRORS')
            os.makedirs(errors_dir, exist_ok=True)
            with open(os.path.join(errors_dir, os.path.basename(f) + '.error'), 'w') as fp:
                fp.write(os.path.join(os.getcwd(), f))
                fp.write(',')
                fp.write(e.__class__.__name__)
                fp.write(',')
                fp.write(str(e))
                fp.write('\n')

    if apk_dir:
        print(f, '-->', os.path.join(apk_dir, os.path.basename(f)))
        os.makedirs(apk_dir, exist_ok=True)
        os.symlink(f, os.path.join(apk_dir, os.path.basename(f)))
