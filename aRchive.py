#!/usr/bin/env python

"""
Author: Nitesh Turaga
Email: nturaga1 at jhu dot edu

Please contact me for any questions regarding this abstract and code.

This script works entirely in the user specified folder:
1. Clones the BIOCONDUCTOR REPOSITORY in the folder
2. Creates an archive in the same specified folder.
3. If there already exists a folder with packages, it updates the aRchive
    with new versions.

Usage: python aRchive.py -bioconductor_dir ../Rpacks/ -archive_dir ../archive

NOTE: If you do not run the dependency installation for SVN, then the following program will throw an
    error.
"""

import argparse
import os
import os.path
import sys
import subprocess
import re
import svn
import svn.local
import svn.remote
import shutil
import linecache
import yaml


# Download the Bioconductor Repo
def downloadMainBiocRepo(path):
    """
    Check out the main repository from Bioconductor giving
    user-name: readonly;
    password: readonly;
    """
    os.chdir(path)
    if os.path.isdir(".svn"):
        os.system("svn update")
        print "SVN repo updated"
    else:
        subprocess.check_call(['svn', 'co', '--username', 'readonly',
                               '--password', 'readonly',
                               'https://hedgehog.fhcrc.org/bioconductor/branches/RELEASE_3_0/madman/Rpacks/'])
    return "Bioconductor Release version repository downloaded"


# HELPER FUNCTION
def copyDirectory(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


def get_package_version(bioc_pack):
    with open(os.path.join(bioc_pack, 'DESCRIPTION'), 'r') as handle:
        info = yaml.load(handle)
        return info['Version']


def checkout(bioc_pack, revision=None):
    if revision is not None:
        return subprocess.check_call(["svn", "update", "-r", revision])
    else:
        return subprocess.check_call(["svn", "update"])


def makeVersion(bioc_pack, archive_dir):
    # Change into current bioconductor package
    os.chdir(bioc_pack)
    # Get history of the SVN repo and get all revert IDs
    history = subprocess.check_output(['svn', 'log', '-q'])
    revert_ids = [line.split()[0] for line in history.splitlines() if line.startswith('r')]

    # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
    latest_version = get_package_version(bioc_pack)
    print "Latest Version", latest_version

    # Loop through the revert IDs to find new versions
    for id in revert_ids:
        # Update repository to previous revert ID
        checkout(bioc_pack, revision=id)
        # Needed?
        # localRepo = svn.local.LocalClient('.')
        # print "\n\n\n Current revision is %s at %s version \n\n" % (str(localRepo.info()['commit#revision']), curr_version)

        if not os.path.exists(os.path.join(bioc_pack, "DESCRIPTION")):
            continue

        curr_version = get_package_version(bioc_pack)

        if curr_version != latest_version:
            print "Bioc_pack version", bioc_pack
            # Create new directory with version number as "-version" extention
            bioc_pack_name = os.path.split(bioc_pack)[-1]
            output_directory = os.path.join(archive_dir, bioc_pack_name, curr_version)
            if not os.path.exists(output_directory):
                print "Made new versioned directory", output_directory
                # SAVE THE CURRENT VERSION HERE
                copyDirectory(bioc_pack, output_directory)
        else:
            pass
    # Return to most recent update
    checkout(bioc_pack)


def archiveLocalRepo(bioc_dir, archive_dir):
    print bioc_dir
    print archive_dir
    # Make the directory which user specifies to build the archive.
    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir)
        print "Made %s" % archive_dir
    # Get all bioconductor packages
    rpacks = [directory for directory in os.listdir(bioc_dir) if not directory.startswith('.')]
    # TODO :  Run "svn cleanup" after every 200 package revisions
    print rpacks

    for bioc_pack in rpacks:
        # Make Versions for EACH R package
        try:
            makeVersion((os.path.join(bioc_dir, bioc_pack)), archive_dir)
        except:
            e = sys.exc_info()[0]
            print "Error in - %s - Bioconductor package: \n %s" % (bioc_pack, e)
            PrintException()
    return "aRchive has been created."


if __name__ == "__main__":
    # Run the install dependency function
    parser = argparse.ArgumentParser(add_help=True, description="Create Bioconductor archive for all packages, \
        and version them based on commit history. If the command is rerun, it should automatically add to an \
        existing archive.")
    parser.add_argument("-bioconductor_dir",dest="bioconductor_dir",help="Name of directory where aRchive.py should work i.e the Bioconductor clone repository",type=str)
    parser.add_argument("-archive_dir",dest="archive_dir",help="Directory name to host all versions of all bioconductor packages. This is where the archive lives",type=str)
    if len(sys.argv) <= 2:
        parser.print_usage()
        sys.exit(1)
    else:
        args = parser.parse_args()

    BIOCONDUCTOR_DIR = os.path.abspath(args.bioconductor_dir)
    ARCHIVE_DIR = os.path.abspath(args.archive_dir)
    print "aRchive is being run in %s " % BIOCONDUCTOR_DIR
    print "aRchive is being stored in %s" % ARCHIVE_DIR
    downloadMainBiocRepo(BIOCONDUCTOR_DIR)
    archiveLocalRepo(BIOCONDUCTOR_DIR, ARCHIVE_DIR)
