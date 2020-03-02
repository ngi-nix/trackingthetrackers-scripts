#!/bin/sh -e

set -x
test -e latest.csv
test -e parse-appids-from-libraries-details.csv
test -n "$ANDROZOO_KEY"
set +x

if [ ! -e tracker-package-names.matches ]; then
    grep -F `cat parse-appids-from-libraries-details.csv | xargs printf ' -e %s '` latest.csv \
	 > tracker-package-names.matches
fi

unset `set | grep -i '^[A-Za-z].*proxy' | cut -d = -f 1`
unset SOCKS_SERVER

for SHA256 in `cut -d , -f 1 ../tracker-package-names.matches`; do
    test -e ${SHA256}.apk && continue
    curl -O --remote-header-name -G -d apikey=${ANDROZOO_KEY} -d sha256=${SHA256} \
	 https://androzoo.uni.lu/api/download
done
