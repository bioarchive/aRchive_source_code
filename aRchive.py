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
        subprocess.check_call(['svn', 'update'])
    else:
        subprocess.check_call(['svn', 'co', '--username', 'readonly',
                               '--password', 'readonly',
                               'https://hedgehog.fhcrc.org/bioconductor/branches/RELEASE_3_0/madman/Rpacks/'])
    return "Bioconductor Release version repository updated"


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
    #print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


def get_package_version(bioc_pack):
    try:
        with open(os.path.join(bioc_pack, 'DESCRIPTION'), 'r') as handle:
            info = yaml.load(handle)
            return info['Version']
    except Exception, e:
        return None


def checkout(cwd, revision=None):
    if revision is not None:
        print "Updating to rev %s" % revision
        try:
            subprocess.check_output(["svn", "update", "-r", revision], cwd=cwd)
        except Exception:
            pass
    else:
        subprocess.check_output(["svn", "update"], cwd=cwd)


def archive_package_versions(bioc_pack, archive_dir):
    # Get history of the SVN repo and get all revert IDs
    history = subprocess.check_output(['svn', 'log', '-q'], cwd=bioc_pack)
    revert_ids = [line.split()[0] for line in history.splitlines() if line.startswith('r')]

    # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
    latest_version = get_package_version(bioc_pack)
    print "Latest Version", latest_version

    # Loop through the revert IDs to find new versions
    for id in revert_ids:
        # Update repository to previous revert ID
        checkout(bioc_pack, revision=id)
        # Grab current version (or None if folder doesn't exist, in which case we'l finish the loop)
        curr_version = get_package_version(bioc_pack)
        if curr_version is not None and curr_version != latest_version:
            print "Bioc_pack version", bioc_pack, curr_version
            # Create new directory with version number as "-version" extention
            bioc_pack_name = os.path.split(bioc_pack)[-1]
            output_directory = os.path.join(archive_dir, bioc_pack_name, curr_version)
            if not os.path.exists(output_directory):
                print "Made new versioned directory", output_directory
                # SAVE THE CURRENT VERSION HERE
                copyDirectory(bioc_pack, output_directory)
        else:
            continue
    # Return to most recent update
    checkout(bioc_pack)


def archiveLocalRepo(bioc_dir, archive_dir):
    # Make the directory which user specifies to build the archive.
    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir)
    # Get all bioconductor packages
    rpack_dir = os.path.join(bioc_dir, 'Rpacks')
    rpacks = [directory for directory in os.listdir(rpack_dir) if not directory.startswith('.')]
    # TODO :  Run "svn cleanup" after every 200 package revisions
    print rpacks

    os.chdir(rpack_dir)
    for bioc_pack in ('groHMM', ): #rpacks[0:1]:
        # Make Versions for EACH R package
        try:
            pack_path = os.path.join(bioc_dir, 'Rpacks', bioc_pack)
            archive_package_versions(pack_path, archive_dir)
        except Exception:
            pass
            #print e
            #e = sys.exc_info()[0]
            #print "Error in - %s - Bioconductor package: \n %s" % (bioc_pack, e)
            #PrintException()
    return "aRchive has been created."


if __name__ == "__main__":
    # Run the install dependency function
    parser = argparse.ArgumentParser(add_help=True, description="Create Bioconductor archive for all packages, \
        and version them based on commit history. If the command is rerun, it should automatically add to an \
        existing archive.")
    parser.add_argument("bioconductor_dir", help="New (or existing) path for clone of Bioconductor repository")
    parser.add_argument("archive_dir", help="Output directory for created BioConductor aRchives")
    args = parser.parse_args()

    BIOCONDUCTOR_DIR = os.path.abspath(args.bioconductor_dir)
    ARCHIVE_DIR = os.path.abspath(args.archive_dir)
    print "aRchive is being run in %s " % BIOCONDUCTOR_DIR
    print "aRchive is being stored in %s" % ARCHIVE_DIR
    downloadMainBiocRepo(BIOCONDUCTOR_DIR)
    archiveLocalRepo(BIOCONDUCTOR_DIR, ARCHIVE_DIR)
