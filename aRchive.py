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
import tarfile
import logging
logging.basicConfig(level=logging.DEBUG, name="aRchive", filename="archive.log")
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
        desc_file = os.path.join(bioc_pack, 'DESCRIPTION')
        with open(os.path.join(bioc_pack, 'DESCRIPTION'), 'r') as handle:
            # Hack to prevent DESCRIPTION files from failing to load,
            # because of yaml parsing.
            info = str([line[8:].strip() for i, line in enumerate(handle) if re.match("^Version: [0-9]", line)][0])
        return info
    except Exception, e:
        log.warn("Could not obtain a version number for %s: %s" % (bioc_pack, e))
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
            log.debug("[A] {0} exists? {1}".format(cwd, os.path.exists(cwd)))
            log.debug("cmd: {0}".format(["svn", "update", "-r", revision]))
            subprocess.check_call(["svn", "update", "-r", revision], cwd=cwd)
            log.debug("[B] {0} exists? {1}".format(cwd, os.path.exists(cwd)))
        except Exception, e:
            log.warning("Exception checking output of svn checkout version: %s" % e)
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
    except Exception, e:
        log.warn("Could not run svn cleanup %s" % path)
        log.warn(e)
        pass


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


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
        log.error("Unexpected error while getting history: ", e)
        return None

    revert_ids = [line.split()[0] for line in history.splitlines() if line.startswith('r')]
    log.debug("IDs that touched %s: %s" % (bioc_pack, ','.join(revert_ids)))

    # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
    latest_version = get_package_version(bioc_pack)
    log.info("Latest Version: %s" % latest_version)

    # Loop through the revert IDs to find new versions
    for rev_id in revert_ids:
        log.debug("\n\nProcessing version ID: %s" % rev_id)
        log.debug("[1] {0} exists? {1}".format(bioc_pack, os.path.exists(bioc_pack)))
        # Update repository to previous revert ID
        checkout(bioc_pack, revision=rev_id)
        log.debug("[2] {0} exists? {1}".format(bioc_pack, os.path.exists(bioc_pack)))
        # Grab current version (or None if folder doesn't exist,
        # in which case we'll finish the loop)
        curr_version = get_package_version(bioc_pack)
        log.debug("[3] {0} exists? {1}".format(bioc_pack, os.path.exists(bioc_pack)))
        if curr_version is not None:
            log.debug("Bioc_pack %s version of %s" % (curr_version, bioc_pack))
            # Create new directory with version number as "-version" extension
            bioc_pack_name = os.path.split(bioc_pack)[-1]
            output_directory = os.path.join(archive_dir)
            out_tarfile = "%s_%s.tar.gz" % (bioc_pack_name, curr_version)
            dest_tar_file = os.path.join(output_directory, out_tarfile)

            log.debug("[4] {0} exists? {1}".format(bioc_pack, os.path.exists(bioc_pack)))
            log.info("\n output_directory: %s \n out_tarfile: %s \n dest_tar_file: %s" % (
                output_directory, out_tarfile, dest_tar_file))

            if not os.path.exists(dest_tar_file):
                # SAVE THE CURRENT VERSION HERE
                # Tar the directory
                log.info('adding contents of bioc_pack %s to tarfile %s' % (bioc_pack, out_tarfile))
                make_tarfile(out_tarfile, bioc_pack)
                dest = os.path.join(output_directory, out_tarfile)
                log.info('Moving %s to %s' % (out_tarfile, dest))
                shutil.move(out_tarfile, dest)
                # Print contents and test
            else:
                log.warn(
                    "Destination tar file %s already exists; not recreating it" % dest_tar_file)
        else:
            log.warn("No current version. Skipped everything! There is an error you are not catching")
            break
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
    # log.debug(' '.join(rpacks))

    rpacks = rpacks[1:3]
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


def main():

    # Add command line parsing options
    parser = argparse.ArgumentParser(add_help=True, description="Create Bioconductor archive for\
        all packages, and version them based on commit history. If the command is rerun,\
        it should automatically add to an existing archive.")
    parser.add_argument("bioconductor_dir", help="New (or existing) path for clone of\
     Bioconductor repository")
    parser.add_argument("archive_dir", help="Output directory for created BioConductor aRchives")
    args = parser.parse_args()

    # Define directories
    BIOCONDUCTOR_DIR = os.path.abspath(args.bioconductor_dir)
    ARCHIVE_DIR = os.path.abspath(args.archive_dir)
    log.info("aRchive is being run in %s " % BIOCONDUCTOR_DIR)
    log.info("aRchive is being stored in %s" % ARCHIVE_DIR)

    checkout_main_biocondutor_repository(BIOCONDUCTOR_DIR)

    # Make the directory which user specifies to build the archive.
    if not os.path.exists(ARCHIVE_DIR):
        os.mkdir(ARCHIVE_DIR)
    archive_local_repository(os.path.join(BIOCONDUCTOR_DIR,'Rpacks'), ARCHIVE_DIR)


if __name__ == "__main__":
    main()
