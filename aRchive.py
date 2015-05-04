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

"""

import argparse
import os
import os.path
import subprocess
import shutil
import re
import logging
logging.basicConfig(level=logging.DEBUG, name="aRchive")
log = logging.getLogger()


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


def get_package_version(bioc_pack):
    """
    Get the version of the BioConductor package by parsing the "DESCRIPTION"

    Args:
      bioc_pack (str): Name of the BioConductor package
    """
    try:
        with open(os.path.join(bioc_pack, 'DESCRIPTION'), 'r') as handle:
            # Hack to prevent DESCRIPTION files from failing to load,
            # because of yaml parsing.
            info = str(
                [line[8:].strip() for i, line in enumerate(handle) if re.match("^Version: [0-9]", line)][0])
            return info
    except Exception, e:
        log.warn("Could not obtain a version number for %s" % bioc_pack)
        log.warn(e)
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
        log.debug("Updating to rev %s" % revision)
        try:
            subprocess.check_output(["svn", "update", "-r", revision], cwd=cwd)
        except Exception, e:
            log.warning(e)
    else:
        log.debug("Updating to latest rev")
        subprocess.check_output(["svn", "update"], cwd=cwd)


def cleanup(path):
    """
    Run SVN cleanup on BioConductor repository

    Args:
      path (str): Local copy of BioConductor repository
    """
    try:
        subprocess.check_call(['svn', 'cleanup', path])
        log.debug("Ran SVN cleanup on local copy of BioConductor repository")
    except Exception:
        pass


def archive_package_versions(bioc_pack, archive_dir):
    """
    Archive ONE package in BioConductor.

    Args:
      bioc_pack (str): Path of the BioConductor package
      archive_dir (str): Path to the archive directory of that package
    """
    # Get history of the SVN repo and get all revert IDs
    try:
        history = subprocess.check_output(['svn', 'log', '-q'], cwd=bioc_pack)
    except subprocess.CalledProcessError:
        log.error("SVN log unable to be accessed in this %s package" % bioc_pack)
        return None
    except Exception, e:
        log.error(e)
        return None

    revert_ids = [line.split()[0] for line in history.splitlines() if line.startswith('r')]
    log.debug("IDs that touched %s: %s" % (bioc_pack, ','.join(revert_ids)))

    # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
    latest_version = get_package_version(bioc_pack)
    log.info("Latest Version: %s" % latest_version)

    # Loop through the revert IDs to find new versions
    for id in revert_ids:
        # Update repository to previous revert ID
        checkout(bioc_pack, revision=id)
        # Grab current version (or None if folder doesn't exist,
        # in which case we'll finish the loop)
        curr_version = get_package_version(bioc_pack)
        if curr_version is not None:
            log.debug("Bioc_pack version %s %s" % (bioc_pack, curr_version))
            # Create new directory with version number as "-version" extension
            bioc_pack_name = os.path.split(bioc_pack)[-1]
            output_directory = os.path.join(archive_dir,
                                            bioc_pack_name, curr_version)
            if not os.path.exists(output_directory):
                log.info("Made new version directory: %s" % output_directory)
                # SAVE THE CURRENT VERSION HERE
                shutil.copytree(bioc_pack, output_directory)
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
    """
    # Get all bioconductor packages
    rpacks = [directory for directory in os.listdir(bioc_dir) if not directory.startswith('.')]
    log.debug(' '.join(rpacks))

    # TODO : rpacks[392:398] yaml tab problem test
    rpacks = rpacks[392:398]
    for index, package_name in enumerate(rpacks):
        # Make Versions for EACH R package
        try:
            log.info("Archiving %s" % package_name)
            archive_package_versions(os.path.join(bioc_dir, package_name), archive_dir)

        except Exception, e:
            log.error(e)
        # Every 100 packages, run `svn cleanup`
        if index % 100 == 99:
            cleanup(bioc_dir)
    log.info("aRchive has been created.")


if __name__ == "__main__":
    # Run the install dependency function
    parser = argparse.ArgumentParser(add_help=True, description="Create Bioconductor archive for\
        all packages, and version them based on commit history. If the command is rerun,\
        it should automatically add to an existing archive.")
    parser.add_argument("bioconductor_dir", help="New (or existing) path for clone of\
     Bioconductor repository")
    parser.add_argument("archive_dir", help="Output directory for created BioConductor aRchives")
    args = parser.parse_args()

    BIOCONDUCTOR_DIR = os.path.abspath(args.bioconductor_dir)
    ARCHIVE_DIR = os.path.abspath(args.archive_dir)
    log.info("aRchive is being run in %s " % BIOCONDUCTOR_DIR)
    log.info("aRchive is being stored in %s" % ARCHIVE_DIR)
    checkout_main_biocondutor_repository(BIOCONDUCTOR_DIR)

    # Make the directory which user specifies to build the archive.
    if not os.path.exists(ARCHIVE_DIR):
        os.mkdir(ARCHIVE_DIR)
    archive_local_repository(os.path.join(BIOCONDUCTOR_DIR, 'Rpacks'), ARCHIVE_DIR)
