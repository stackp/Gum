#!/bin/sh

# This script builds scalpel tarballs

USAGE="usage: $0 version_number"

if [ "$1" = "" ]; then
    echo $USAGE
    exit 1
fi

set -u
VERSION="$1"
DIR="scalpel-$VERSION"
ARCHIVE="$DIR.tar.gz"
FILES="control.py event.py gtkui.py player.py scalpel.py edit.py \
graphmodel.py gtkwaveform.py pysndfile.py selection.py"

rm -f $ARCHIVE
mkdir $DIR
for file in $FILES; do
    cp $file $DIR
done
tar cvzf $ARCHIVE $DIR
rm -rf $DIR