#!/usr/bin/env python
"""
Author: Nitesh Turaga
Email: nturaga1 at jhu dot edu

Please contact me for any questions regarding this abstract and code.

This script works entirely in the user specified folder:
1. Clones the BIOCONDUCTOR REPOSITORY in the folder
2. Creates an archive in the specified folder.
3. If there already exists a folder with packages, it updates the aRchive
    with new versions.

Example:
    The Usage of the program is described below

        $ python aRchive.py -bioconductor_dir ../Rpacks/ -archive_dir ../archive

NOTE: This package required SVN as a dependency, it will throw an error if SVN doesn't exist.
"""

import argparse
import os
import os.path
import subprocess
import shutil
import yaml


# Download the Bioconductor Repo
def checkout_main_biocondutor_repository(path):
    """
    SVN checkout the main repository from Bioconductor giving
    user-name: readonly;
    password: readonly;

    Args:
      path (str): The path of the main BioConductor repository to be 
        downloaded onto the machine. 
    """
    if not os.path.exists(path):
        os.mkdir(path)

    os.chdir(path)
    if os.path.isdir(".svn"):
        subprocess.check_call(['svn', 'update'])
    else:
        subprocess.check_call(['svn', 'co', '--username', 'readonly',
                               '--password', 'readonly',
                               'https://hedgehog.fhcrc.org/bioconductor/branches/RELEASE_3_0/madman/Rpacks/'])
    return "Bioconductor Release version repository updated"



def copy_directory(src, dest):
    """
    Copies entire directory recursively

    Args:
      param1 (str): Source of the directory to be copied
      param2 (str): Destination of the directory to be copied

    """
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def get_package_version(bioc_pack):
    """
    Get the version of the BioConductor package by parsing the "DESCRIPTION"

    Args:
      bioc_pack (str): Name of the BioConductor package

    Raises:
      IOError: File not found, because the "DESCRIPTION" file is missing
        in the package
    """
    try:
        with open(os.path.join(bioc_pack, 'DESCRIPTION'), 'r') as handle:
            info = yaml.load(handle)
            return info['Version']
    except Exception, e:
        print e
        return None


def checkout(cwd, revision=None):
    """
    SVN checkout a particular revision of a BioConductor package

    Args:
      cwd (str): Current working directory
      revision(str, optional): Revision number of the package
        for checkout.
    """
    if revision is not None:
        print "Updating to rev %s" % revision
        try:
            subprocess.check_output(["svn", "update", "-r", revision], cwd=cwd)
        except Exception:
            pass
    else:
        subprocess.check_output(["svn", "update"], cwd=cwd)


def cleanup(path):
    """
    Run SVN cleanup on BioConductor repository

    Args:
      path (str): Local copy of BioConductor repository
    """
    try:
        subprocess.check_call(['svn', 'cleanup', path])
    except Exception:
        pass
    return "Ran SVN cleanup on local copy of BioConductor repository"


def archive_package_versions(bioc_pack, archive_dir):
    """
    Archive ONE package in BioConductor.

    Args:
      bioc_pack (str): Path of the BioConductor package
      archive_dir (str): Path to the archive directory of that package
    """
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
        # Grab current version (or None if folder doesn't exist, in which case we'll finish the loop)
        curr_version = get_package_version(bioc_pack)
        if curr_version is not None:
            print "Bioc_pack version", bioc_pack, curr_version
            # Create new directory with version number as "-version" extension
            bioc_pack_name = os.path.split(bioc_pack)[-1]
            output_directory = os.path.join(archive_dir, bioc_pack_name, curr_version)
            if not os.path.exists(output_directory):
                print "Made new version directory", output_directory
                # SAVE THE CURRENT VERSION HERE
                copy_directory(bioc_pack, output_directory)
        else:
            continue
    # Return to most recent update
    checkout(bioc_pack)


def archive_local_repository(bioc_dir, archive_dir):
    """
    Archive ALL packages in BioConductor.

    Args:
      bioc_dir (str): Path to directory which holds all the BioConductor
        repositories.
      archive_dir (str): Path to the archive directory

    TODO: Add SVN cleanup to this function after every 200 packages
    """
    # Make the directory which user specifies to build the archive.
    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir)
    # Get all bioconductor packages
    rpack_dir = os.path.join(bioc_dir)
    rpacks = [directory for directory in os.listdir(rpack_dir) if not directory.startswith('.')]
    # TODO :  Run "svn cleanup" after every 200 package revisions
    print rpacks

    os.chdir(rpack_dir)
    for bioc_pack in (rpacks[292:293]):
        # Make Versions for EACH R package
        try:
            print "Archiving %s" % bioc_pack
            pack_path = os.path.join(bioc_dir, bioc_pack)
            archive_package_versions(pack_path, archive_dir)
        except Exception:
            pass
    print "aRchive has been created."


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
    checkout_main_biocondutor_repository(BIOCONDUCTOR_DIR)
    archive_local_repository(BIOCONDUCTOR_DIR, ARCHIVE_DIR)
