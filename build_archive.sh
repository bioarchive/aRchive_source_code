#!/bin/bash
rm -rf ~/aRchive_source_code-master
wget https://github.com/bioarchive/aRchive_source_code/archive/master.tar.gz -O archive_source_code.tar.gz
tar xvfz archive_source_code.tar.gz
rm -f ~/archive_source_code.tar.gz

# Build archive
python aRchive_source_code-master/aRchive.py ~/Rpacks /srv/nginx/bioarchive.galaxyproject.org/root/
# Copy js updates in
cp -Rv aRchive_source_code\-master/app/ /srv/nginx/bioarchive.galaxyproject.org/root/
