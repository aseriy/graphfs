#!/usr/bin/bash

# This script needs to be run from the top Apache directory project within the archive,
# e.g. 'accumulo' or 'airflow'


# The archives we're looking for are *.tar.gz and *.zip files

PROJ=$(basename $(pwd))

RELS_TAR_GZ=$(find . -type f -name "*.tar.gz" | xargs dirname | sort -u)

RELS_ZIP=$(find . -type f -name "*-*.zip" | xargs dirname | sort -u)

RELS=$(echo $RELS_TAR_GZ $RELS_ZIP | tr " " "\n" | sort -u)
echo $RELS
