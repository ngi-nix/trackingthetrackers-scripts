
import binascii
import csv
import datetime
import functools
import glob
import gzip
import hashlib
import io
import json
import os
import re
import requests
import sys
import time
import zipfile
from xml.etree import ElementTree
from androguard.core.bytecodes.apk import get_apkid

APK_ROOT = '/data/malware-apks'

APKANALYZER_ROOT = '/data/ttt-apks/extracted-features/apkanalyzer-dex-packages'
AXML_ROOT = '/data/ttt-apks/extracted-features/apkparser-axml2xml'
FAUP_ROOT = '/data/ttt-apks/extracted-features/faup-hosts'
IPGREP_ROOT = '/data/ttt-apks/extracted-features/unzip-ipgrep'
RIPGREP_FAUP_ROOT = '/data/ttt-apks/extracted-features/ripgrep-faup'

code_signatures_regex = None
network_signatures_regex = None

errors = []


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(obj)
        return super().default(obj)


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


def append_error(packageName, packageHash, apk_path, symlink_path, e):
    errors.append([packageName, packageHash, apk_path, symlink_path, str(e)])


def write_errors(set_dir):
    output = init_feature_vector_instance()
    output['errors'] = errors
    with open(os.path.join(set_dir, 'errors.json'), 'w') as fp:
        json.dump(output, fp, indent=2, sort_keys=True, cls=Encoder)


def init_feature_vector_instance():
    """https://gitlab.com/trackingthetrackers/wiki/-/wikis/JSON-format-definition-for-feature-vectors"""
    output = {
        "apks": [{
            "metaDataNames": [],
            "broadcastReceiverIntentFilterActionNames": [],
            "dependencies": [],
            "domainNames": [],
            "domainNamesFilteredByExodus":[],
            "usesPermissions": [],
        }],
        "meta": {
            "ver": "0.3.0",
            "generated": datetime.datetime.now().isoformat(),
            "generatedBy": sys.argv,
        }
    }
    try:
        import git
    except ImportError:
        return output
    if os.path.isdir('.git'):
        repo = git.repo.Repo('.')
        output['meta']['sourceDataCommitId'] = binascii.hexlify(bytearray(repo.head.commit.binsha)).decode()

    script_git_path = os.path.dirname(sys.argv[0])
    if os.path.isdir(os.path.join(script_git_path, '.git')):
        repo = git.repo.Repo(script_git_path)
        output['meta']['generatedByCommitId'] = binascii.hexlify(bytearray(repo.head.commit.binsha)).decode()
    return output


def init_search_space():
    """search_space uses sets during operation, then is output as lists"""
    d = init_feature_vector_instance()
    for k in d['apks'][0].keys():
        d['apks'][0][k] = set()
    return d


def add_to_search_space(search_space, apk_vector):
    for k in search_space['apks'][0].keys():
        search_space['apks'][0][k].update(apk_vector.get(k, []))


def write_search_space(output, set_dir):
    output['apks'][0]['label'] = os.path.basename(set_dir)
    with open(os.path.join(set_dir, 'search_space.json'), 'w') as fp:
        json.dump(output, fp, indent=2, sort_keys=True, cls=Encoder)


def write_feature_vector_json(search_space, apk_symlink_path, applicationId, sha256):
    global code_signatures_regex, network_signatures_regex
    if not code_signatures_regex or not network_signatures_regex:
        code_signatures_regex, network_signatures_regex = get_exodus_signatures()

    starttime = time.time()

    apk_path = os.readlink(apk_symlink_path)[len(APK_ROOT) + 1:]
    apk_vector = {
        'applicationId': applicationId,
        'sha256': sha256,
    }
    feature_vector_json = apk_symlink_path[:-4] + '.json'

    dex_path = os.path.join(APKANALYZER_ROOT, apk_path + '.dex-dump.gz')
    if not os.path.exists(dex_path):
        print('NO DEX_DUMP')
        return
    dependencies = set()
    if False:  # enable as needed, this is slow
        try:
            with gzip.open(dex_path, 'rt', errors='replace') as gz:
                for m in code_signatures_regex.findall(gz.read()):
                    dependencies.add(m)
        except EOFError as e:
            print(dex_path, e)
            os.remove(dex_path)
    if dependencies:
        apk_vector['dependencies'] = sorted(dependencies)
    elif os.path.exists(feature_vector_json):
        with open(feature_vector_json) as fp:
            data = json.load(fp)
            if 'dependencies' in data.get('apks', [{}, ])[0]:
                apk_vector['dependencies'] = data['apks'][0]['dependencies']
            else:
                print('NO CACHED DEX DUMP')
                return
    else:
        print('NO CACHED DEX DUMP OR FEATURE VECTOR JSON')
        return
    dexdumptime = time.time()

    axml_path = os.path.join(AXML_ROOT, apk_path + '.AndroidManifest.xml')
    if not os.path.exists(axml_path):
        print('NO AXML')
        return
    try:
        tree = ElementTree.parse(axml_path)
        permissions = tree.findall('uses-permission')  # type: List[ElementTree.Element]
        # loop over xml tree and gather permissions in a list
        permissions_requested = []
        for perm in permissions:  # type: ElementTree.Element
            for p in perm.items():  # type: Tuple[str, str]
                permissions_requested.append(p[1])  # actual permission
        apk_vector['usesPermissions'] = sorted(permissions_requested)

        action_names = set()
        application = tree.find('application')
        meta_data_parents = [tree, application]
        if application and len(application) > 0:
            receivers = application.findall('receiver')
            meta_data_parents += (
                receivers
                + application.findall('activity')
                + application.findall('activity-alias')
                + application.findall('provider')
                + application.findall('service')
            )
            for receiver in receivers:
                for intent_filter in receiver.findall('intent-filter'):
                    for action in intent_filter.findall('action'):
                        action_name = action.attrib['{http://schemas.android.com/apk/res/android}name']
                        action_names.add(action_name)
        apk_vector['broadcastReceiverIntentFilterActionNames'] = sorted(action_names)

        meta_data_names = set()
        for item in meta_data_parents:
            if item is None:
                continue
            for meta_data in item.findall('meta-data'):
                meta_data_names.add(meta_data.attrib['{http://schemas.android.com/apk/res/android}name'])
        apk_vector['metaDataNames'] = sorted(meta_data_names)
    except ElementTree.ParseError as e:
        print(axml_path, e)
        os.remove(axml_path)
    axmltime = time.time()

    domain_names = set()
    csv.register_dialect('skiperrors', strict=False, quoting=csv.QUOTE_NONE)

    ripgrep_faup_path = os.path.join(RIPGREP_FAUP_ROOT, apk_path + '.ripgrep-faup.csv.gz')
    if os.path.exists(ripgrep_faup_path):
        try:
            # ripgrep sometimes outputs NULL bytes and other things that shouldn't be there
            with gzip.open(ripgrep_faup_path, 'rt', errors='replace') as gz:
                csvfile = csv.reader([line[:8192].replace('\0', '') for line in gz.readlines()],
                                     dialect='skiperrors')
                # faup sometimes outputs corrupt rows so just include all columns in the set
                for row in csvfile:
                    domain_names.update([x.strip() for x in row])
        except (EOFError, OSError) as e:
            print('rm', ripgrep_faup_path, e)
            os.remove(ripgrep_faup_path)
        except csv.Error as e:
            print(ripgrep_faup_path, row, e)
    ripgreptime = time.time()

    ipgrep_path = os.path.join(IPGREP_ROOT, apk_path + '.unzip-ipgrep')
    if os.path.exists(ipgrep_path):
        with open(ipgrep_path, errors='replace') as fp:
            hosts = csv.reader(fp, dialect='excel-tab')
            for row in hosts:
                if len(row) != 3:
                    print('CORRUPT ROW:', ipgrep_path, row)
                    continue
                domainname = row[1]
                if domainname and domainname != '-':
                    domain_names.add(domainname)
    ipgreptime = time.time()

    faup_path = os.path.join(FAUP_ROOT, apk_path + '.unzip-faup.csv')
    if os.path.exists(faup_path):
        try:
            with open(faup_path, errors='replace') as fp:
                csvfile = csv.reader(fp, dialect='skiperrors')
                for row in csvfile:
                    # faup sometimes outputs corrupt rows so just include all columns in the set
                    domain_names.update([x.strip() for x in row])
        except csv.Error as e:
            print(faup_path, row, e)

    if not os.path.exists(ipgrep_path) and not os.path.exists(faup_path) and not os.path.exists(ripgrep_faup_path):
        print('NO IPGREP or FAUP domainNames')
        return
    if '' in domain_names:
        domain_names.remove('')
    fauptime = time.time()

    tracker_domain_names = set()
    for name in domain_names:
        for match in network_signatures_regex.findall(name):
            tracker_domain_names.add(match)
    if '' in tracker_domain_names:
        tracker_domain_names.remove('')
    apk_vector['domainNamesFilteredByExodus'] = sorted(tracker_domain_names)

    add_to_search_space(search_space, apk_vector)
    output = init_feature_vector_instance()
    output['apks'] = [apk_vector]
    print('WRITE FEATURE VECTOR:', feature_vector_json)
    with open(feature_vector_json, 'w') as fp:
        json.dump(output, fp, indent=2, sort_keys=True)
    endtime = time.time()
    print('\tdexdump: %02.4f' % (dexdumptime - starttime),
          'axml: %02.4f' % (axmltime - dexdumptime),
          'ripgrep: %02.4f' % (ripgreptime - axmltime),
          'ipgrep: %02.4f' % (ipgreptime - ripgreptime),
          'faup: %02.4f' % (fauptime - ipgreptime),
          'write: %02.4f' % (endtime - fauptime),
          'TOTAL: %02.4f\n' % (endtime - starttime),
          sep='\t')
