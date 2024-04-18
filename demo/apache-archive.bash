#!/usr/bin/bash

# This script needs to be run from the top Apache directory project within the archive,
# e.g. 'accumulo' or 'airflow'


# The archives we're looking for are *.tar.gz and *.zip files

PROJ=$(basename $(pwd))

RELS_TAR_GZ=$(find . -type f -name "*.tar.gz")
RELS_ZIP=$(find . -type f -name "*.zip")

if [[ ! -z $RELS_TAR_GZ ]]; then
  RELS_TAR_GZ=$(echo $RELS_TAR_GZ | xargs dirname | tr " " "\n" | sort -u)
fi

for rel in $RELS_TAR_GZ; do
  (cd $rel && \
  for f in *.gz; do (mkdir tmp && cd tmp && tar xvfz ../$f && cd .. && rm $f && mv tmp $f); done \
  )
done


if [[ ! -z $RELS_ZIP ]]; then
  RELS_ZIP=$(echo $RELS_ZIP | xargs dirname | tr " " "\n" | sort -u)
fi

for rel in $RELS_ZIP; do
  (cd $rel && \
  for f in *.zip; do (mkdir tmp && cd tmp && unzip ../$f && cd .. && rm $f && mv tmp $f); done \
  )
done
