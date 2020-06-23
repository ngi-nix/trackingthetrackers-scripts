
import csv
import functools
import glob
import gzip
import hashlib
import io
import json
import os
import re
import requests
import zipfile
from xml.etree import ElementTree

APK_ROOT = '/data/malware-apks'

APKANALYZER_ROOT = '/data/ttt-apks/extracted-features/apkanalyzer-dex-packages'
AXML_ROOT = '/data/ttt-apks/extracted-features/apkparser-axml2xml'
FAUP_ROOT = '/data/ttt-apks/extracted-features/faup-hosts'
IPGREP_ROOT = '/data/ttt-apks/extracted-features/unzip-ipgrep'

code_signatures_regex = None
network_signatures_regex = None


def write_apk_list(apk_list, apk_list_file):
    print('writing', apk_list_file)
    with gzip.GzipFile(apk_list_file, 'w') as gz:
        buff = io.StringIO()
        writer = csv.writer(buff)
        writer.writerows(apk_list)
        gz.write(buff.getvalue().encode())


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


def get_exodus_signatures():
    r = requests.get('https://etip.exodus-privacy.eu.org/trackers/export')
    r.raise_for_status()
    exodus = r.json()
    code_signatures = []
    network_signatures = []
    print(exodus['trackers'][0])
    for tracker in exodus['trackers']:
        code_signature = tracker.get('code_signature')
        if code_signature and code_signature != 'NC':  # there are some errant 'NC' entries
            code_signatures.append(code_signature)
        network_signature = tracker.get('network_signature')
        if network_signature and network_signature != 'NC':  # there are some errant 'NC' entries
            network_signatures.append(network_signature)
    code_signatures_regex = re.compile('(%s)' % '|'.join(sorted(code_signatures)))
    network_signatures_regex = re.compile('(%s)' % '|'.join(sorted(network_signatures)))
    return (code_signatures_regex, network_signatures_regex)


def write_feature_vector_json(apk_symlink_path, applicationId, sha256):
    global code_signatures_regex, network_signatures_regex
    if not code_signatures_regex or not network_signatures_regex:
        code_signatures_regex, network_signatures_regex = get_exodus_signatures()

    apk_path = os.readlink(apk_symlink_path)[len(APK_ROOT) + 1:]
    dex_path = os.path.join(APKANALYZER_ROOT, apk_path + '.dex-dump.gz')
    apk_vector = {
        'applicationId': applicationId,
        'sha256': sha256,
    }

    dependencies = set()
    with gzip.open(dex_path, 'rt') as gz:
        for m in code_signatures_regex.findall(gz.read()):
            dependencies.add(m)
    apk_vector['dependencies'] = sorted(dependencies)

    axml_path = os.path.join(AXML_ROOT, apk_path + '.AndroidManifest.xml')
    tree = ElementTree.parse(axml_path)
    permissions = tree.findall('uses-permission')  # type: List[ElementTree.Element]
    # loop over xml tree and gather permissions in a list
    permissions_requested = []
    for perm in permissions:  # type: ElementTree.Element
        for p in perm.items():  # type: Tuple[str, str]
            permissions_requested.append(p[1])  # actual permission
    apk_vector['usesPermissions'] = sorted(permissions_requested)

    ipgrep_path = os.path.join(IPGREP_ROOT, apk_path + '.unzip-ipgrep')
    print(ipgrep_path)
    print(glob.glob(ipgrep_path))
    domain_names = set()
    with open(ipgrep_path) as fp:
        hosts = csv.reader(fp, dialect='excel-tab')
        for row in hosts:
            domainname = row[1]
            if domainname and domainname != '-':
                domain_names.add(domainname)

    faup_path = os.path.join(FAUP_ROOT, apk_path + '.unzip-faup.csv')
    with open(faup_path) as fp:
        domain_names.update([x.strip() for x in fp.readlines()])
    if '' in domain_names:
        domain_names.remove('')

    tracker_domain_names = set()
    for name in domain_names:
        for match in network_signatures_regex.findall(name):
            tracker_domain_names.add(match)
    if '' in tracker_domain_names:
        tracker_domain_names.remove('')
    apk_vector['domainNames'] = sorted(tracker_domain_names)

    print('WRITE FEATURE VECTOR:', apk_symlink_path.replace('.apk', '.json'))
    with open(apk_symlink_path.replace('.apk', '.json'), 'w') as fp:
        json.dump(apk_vector, fp, indent=2, sort_keys=True)
