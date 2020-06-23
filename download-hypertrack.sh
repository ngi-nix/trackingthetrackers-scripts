#!/bin/sh
#
# https://jcenter.bintray.com/io/hypertrack/smart-scheduler/0.0.9/smart-scheduler-0.0.9.pom
# https://jcenter.bintray.com/io/hypertrack/smart-scheduler/0.0.9/smart-scheduler-0.0.9.aar
# http://hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com/com/hypertrack/android/0.4.5/android-0.4.5.pom
# http://hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com/com/hypertrack/android/0.4.5/android-0.4.5-release.aar
# http://hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com/io/hypertrack/paho/1.1.2/paho-1.1.2-release.aar
# http://hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com/io/hypertrack/mqttv3/1.1.2/mqttv3-1.1.2-release.jar

set -e
set -x

BASEDIR=/export/share/code/eighthave/track-the-trackers/hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com
BASEURL=http://hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com
for i in 0 1 2 3 4 5 6 7 8 9; do
    for j in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18; do
        for k in 0 1 2 3 4 5 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40; do
            dir=$BASEDIR/com/hypertrack/android/${i}.${j}.${k}
            test -d $dir || mkdir $dir
            cd $dir
            (wget --continue ${BASEURL}/com/hypertrack/android/${i}.${j}.${k}/android-${i}.${j}.${k}.pom || true) &
            (wget --continue ${BASEURL}/com/hypertrack/android/${i}.${j}.${k}/android-${i}.${j}.${k}-release.aar || true) &
            (wget --continue ${BASEURL}/com/hypertrack/android/${i}.${j}.${k}/android-${i}.${j}.${k}.aar || true) &

            dir=$BASEDIR/com/hypertrack/hyperlog/${i}.${j}.${k}
            test -d $dir || mkdir $dir
            cd $dir
            (wget --continue ${BASEURL}/com/hypertrack/hyperlog/${i}.${j}.${k}/hyperlog-${i}.${j}.${k}.pom || true) &
            (wget --continue ${BASEURL}/com/hypertrack/hyperlog/${i}.${j}.${k}/hyperlog-${i}.${j}.${k}-release.jar || true) &
            (wget --continue ${BASEURL}/com/hypertrack/hyperlog/${i}.${j}.${k}/hyperlog-${i}.${j}.${k}.jar || true) &
            (wget --continue ${BASEURL}/com/hypertrack/hyperlog/${i}.${j}.${k}/hyperlog-${i}.${j}.${k}-release.aar || true) &
            (wget --continue ${BASEURL}/com/hypertrack/hyperlog/${i}.${j}.${k}/hyperlog-${i}.${j}.${k}.aar || true) &

            dir=$BASEDIR/io/hypertrack/mqttv3/${i}.${j}.${k}
            test -d $dir || mkdir $dir
            cd $dir
            (wget --continue ${BASEURL}/io/hypertrack/mqttv3/${i}.${j}.${k}/mqttv3-${i}.${j}.${k}.pom || true) &
            (wget --continue ${BASEURL}/io/hypertrack/mqttv3/${i}.${j}.${k}/mqttv3-${i}.${j}.${k}-release.jar || true) &
            (wget --continue ${BASEURL}/io/hypertrack/mqttv3/${i}.${j}.${k}/mqttv3-${i}.${j}.${k}.jar || true) &
            (wget --continue ${BASEURL}/io/hypertrack/mqttv3/${i}.${j}.${k}/mqttv3-${i}.${j}.${k}-release.aar || true) &
            (wget --continue ${BASEURL}/io/hypertrack/mqttv3/${i}.${j}.${k}/mqttv3-${i}.${j}.${k}.aar || true) &

            dir=$BASEDIR/io/hypertrack/paho/${i}.${j}.${k}
            test -d $dir || mkdir $dir
            cd $dir
            (wget --continue ${BASEURL}/io/hypertrack/paho/${i}.${j}.${k}/paho-${i}.${j}.${k}-release.aar || true) &
            wget --continue ${BASEURL}/io/hypertrack/paho/${i}.${j}.${k}/paho-${i}.${j}.${k}.aar || true

        done
    done 
done



