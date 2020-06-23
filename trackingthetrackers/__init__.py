
import csv
import functools
import gzip
import hashlib
import io
import zipfile

APK_ROOT = '/data/malware-apks'
AXML_ROOT = '/data/ttt-apks/extracted-features/apkparser-axml2xml'
FAUP_ROOT = '/data/ttt-apks/extracted-features/faup-hosts'


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
