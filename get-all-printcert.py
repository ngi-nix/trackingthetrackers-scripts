#!/usr/bin/env python3

import glob
import json
import logging
import os
import re
import subprocess
import zipfile
from androguard.core.bytecodes.apk import get_apkid
from fdroidserver import common


logging.getLogger("androguard.axml").setLevel(logging.ERROR)
logging.getLogger("androguard.session").setLevel(logging.ERROR)

sha256_pat = re.compile(r'^([0-9A-F]{64})\.apk$', re.IGNORECASE)

all_certs = dict()
certs_per_appid = dict()
certs_per_apk = dict()
for f in glob.glob('*/*/*.apk'):
    try:
        appid, versionCode, versionName = get_apkid(f)
        with zipfile.ZipFile(f, 'r') as apk:
            cert_files = [n[9:] for n in apk.namelist() if common.SIGNATURE_BLOCK_FILE_REGEX.match(n)]
    except Exception as e:
        print(f, e)
        continue

    filename = os.path.basename(f)

    sha256 = None
    m = sha256_pat.match(filename)
    if m:
        sha256 = m.group(1).upper()

    fingerprint = common.apk_signer_fingerprint(f)

    cmd = ['keytool', '-printcert', '-jarfile', f]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    printcert = p.stdout.decode()
    if fingerprint not in all_certs:
        all_certs[fingerprint] = []
    all_certs[fingerprint].append({
        'file': filename,
        'sha256': sha256,
        'printcert': printcert,
        'applicationId': appid,
        'versionCode': versionCode,
        'versionName': versionName,
    })

    certs_per_apk[filename] = {
        'versionCode': versionCode,
        'versionName': versionName,
        'printcert': printcert,
        'cert_files': cert_files,
    }
    if fingerprint:
        certs_per_apk[filename]['fingerprint'] = fingerprint.upper()
    if sha256:
        certs_per_apk[filename]['sha256'] = sha256

    if appid not in certs_per_appid:
        certs_per_appid[appid] = []
    certs_per_appid[appid].append(certs_per_apk[filename])
    print('.', end='', flush=True)

with open('all_certs.json', 'w') as fp:
    json.dump(all_certs, fp)

with open('certs_per_apk.json', 'w') as fp:
    json.dump(certs_per_apk, fp)

with open('certs_per_appid.json', 'w') as fp:
    json.dump(certs_per_appid, fp)
