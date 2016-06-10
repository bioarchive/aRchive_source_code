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

import json
import argparse
import os
import os.path
import subprocess
import shutil
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

    if os.path.isdir(os.path.join(path, ".svn")):
        subprocess.check_call(['svn', 'update'], cwd=path)
    else:
        subprocess.check_call(['svn', 'co', '--username', 'readonly',
                               '--password', 'readonly',
                               'https://hedgehog.fhcrc.org/bioconductor/trunk/madman/Rpacks/'],
                              cwd=path
                              )

    # Fetch repository information
    repo_info = {}
    tmp_info = subprocess.check_output(['svn', 'info', 'Rpacks'], cwd=path)
    for entry in tmp_info.split('\n'):
        if len(entry.strip()) > 0:
            key, value = entry.strip().split(': ')
            repo_info[key] = value

    return repo_info


def bad_yaml_parser(bioc_pack):
    """
    Get the fields of the BioConductor package by parsing the
    "DESCRIPTION" file

    Args:
      bioc_pack (str): Name of the BioConductor package
    """
    try:
        desc_file = os.path.join(bioc_pack, 'DESCRIPTION')
        data = {}
        with open(desc_file, 'r') as handle:
            current_key = None
            for line in handle:
                # If deps are starting
                if not line.startswith(' '):
                    current_key = line.split(':')[0].strip()
                    if current_key not in data:
                        data[current_key] = ''
                    data[current_key] += line.replace(current_key + ':', '').strip() + ' '
                else:
                    # If deps runs over multiple lines
                    if current_key is not None:
                        # If it starts with a space, then we're on a continuation
                        # of the dependencies
                        if line.startswith(' '):
                            data[current_key] += line.strip() + ' '
                        else:
                            # If it starts with anything other than a space, then
                            # we're no longer in the dependencies.
                            current_key = None
        for key in data:
            data[key] = data[key].strip()
        return data
    except Exception, e:
        log.warn("Could not parse %s: %s" % (bioc_pack, e))
        return {}


def get_package_dependencies(bioc_pack):
    """
    Get the dependencies of the BioConductor package by parsing the
    "DESCRIPTION" file

    Args:
      bioc_pack (str): Name of the BioConductor package
    """
    data = bad_yaml_parser(bioc_pack)
    deps = []
    for key in ('Depends', 'Imports'):
        if 'Depends' in data:
            deps += [x.strip() for x in data['Depends'].split(',') if x.strip() not in deps]
    return deps


def get_package_version(bioc_pack):
    """
    Get the version of the BioConductor package by parsing the "DESCRIPTION"

    Args:
      bioc_pack (str): Name of the BioConductor package
    """
    data = bad_yaml_parser(bioc_pack)
    if 'Version' in data:
        return data['Version']
    else:
        log.warn("Could not obtain a version number for %s" % (bioc_pack))
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
            subprocess.check_call(["svn", "update", "-r", revision], cwd=cwd)
        except Exception, e:
            log.warning("Exception checking output of svn checkout version: %s" % e)
    else:
        log.debug("Updating to latest rev")
        subprocess.check_call(["svn", "update"], cwd=cwd)


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


def archive_package_versions(bioc_pack, archive_dir, latest_rev=1000):
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
    latest_info = bad_yaml_parser(bioc_pack)
    log.info("Latest Version: %s" % latest_version)

    bioc_pack_name = os.path.split(bioc_pack)[-1]
    # Dependency info
    dependency_data = []
    # Store a list of all versions for the "API"
    stored_version = [latest_version]
    # Loop through the revert IDs to find new versions
    for rev_id in revert_ids:
        log.debug("\n\nProcessing version ID: %s" % rev_id)
        # Update repository to previous revert ID
        checkout(bioc_pack, revision=rev_id)
        # Grab current version (or None if folder doesn't exist,
        # in which case we'll finish the loop)
        curr_version = get_package_version(bioc_pack)
        if curr_version is not None:
            log.debug("Bioc_pack %s version of %s" % (curr_version, bioc_pack))
            # Create new directory with version number as "-version" extension
            out_tarfile = "%s_%s.tar.gz" % (bioc_pack_name, curr_version)
            dest_tar_file = os.path.join(archive_dir, out_tarfile)

            log.info("\n output_directory: %s \n out_tarfile: %s \n dest_tar_file: %s" % (
                archive_dir, out_tarfile, dest_tar_file))

            if curr_version not in stored_version:
                stored_version.append(curr_version)

            if curr_version not in dependency_data:
                deps = get_package_dependencies(bioc_pack)
                dependency_data.append((
                    int(rev_id[1:]),
                    curr_version,
                    deps
                ))

            if not os.path.exists(dest_tar_file):
                # SAVE THE CURRENT VERSION HERE
                # Tar the directory
                log.info('adding contents of bioc_pack %s to tarfile %s' % (bioc_pack, out_tarfile))
                make_tarfile(out_tarfile, bioc_pack)
                dest = os.path.join(archive_dir, out_tarfile)
                log.info('Moving %s to %s' % (out_tarfile, dest))
                shutil.move(out_tarfile, dest)
                # Print contents and test
            else:
                log.warn(
                    "Destination tar file %s already exists; not recreating it" % dest_tar_file)
        else:
            log.warn("No current version. Skipped everything! There is an error you are not catching")
            break
    # Dump version info
    try:
        os.makedirs(os.path.join(archive_dir, 'api'))
    except Exception:
        pass
    with open(os.path.join(archive_dir, 'api', bioc_pack_name + '.json'), 'w') as handle:
        api_data = {
            'versions': stored_version,
            'info': latest_info,
        }
        json.dump(api_data, handle)

    dependency_data = dependency_data[::-1]
    version_list_path = os.path.join(archive_dir, bioc_pack_name + '_versions_full.txt')
    with open(version_list_path, 'w') as handle:
        for version_idx in range(len(dependency_data)):
            from_version = dependency_data[version_idx]

            if version_idx < len(dependency_data) - 1:
                to_version = dependency_data[version_idx + 1]
            else:
                to_version = (latest_rev, None, None)

            # (46412, '1.17.0', ['Biobase', 'graphics', 'grDevices', 'methods', 'multtest', 'stats', 'tcltk', 'utils'])
            for specific_idx in range(from_version[0], to_version[0]):
                handle.write('%s\t%s\t%s\n' % (specific_idx, from_version[1],
                                               ','.join(from_version[2])))

    # Return to most recent update
    checkout(bioc_pack)


def archive_local_repository(bioc_dir, archive_dir, repo_info):
    """
    Archive ALL packages in BioConductor.

    Args:
      bioc_dir (str): Path to directory which holds all the BioConductor
        repositories.
      archive_dir (str): Path to the archive directory
    """
    # Get all bioconductor packages
    rpacks = [directory for directory in os.listdir(bioc_dir) if not directory.startswith('.')]

    #rpacks = rpacks[1:3] + ['Biobase']
    latest_rev = int(repo_info['Revision'])
    for index, package_name in enumerate(rpacks):
        # Make Versions for EACH R package
        try:
            log.info("Archiving %s" % package_name)
            archive_package_versions(os.path.join(bioc_dir, package_name), archive_dir, latest_rev=latest_rev)
        except Exception, e:
            log.error(e)
        # Every 100 packages, run `svn cleanup`
        if index % 20 == 19:
            cleanup(bioc_dir)
            log.info("svn cleanup has been run.")
    log.info("aRchive has been created.")

    # Store a list of all packages to an "API"
    try:
        os.makedirs(os.path.join(archive_dir, 'api'))
    except Exception:
        pass
    with open(os.path.join(archive_dir, 'api', 'api.json'), 'w') as handle:
        json.dump(rpacks, handle)


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

    repo_info = checkout_main_biocondutor_repository(BIOCONDUCTOR_DIR)

    # Make the directory which user specifies to build the archive.
    if not os.path.exists(ARCHIVE_DIR):
        os.mkdir(ARCHIVE_DIR)
    archive_local_repository(os.path.join(BIOCONDUCTOR_DIR, 'Rpacks'), ARCHIVE_DIR, repo_info)


if __name__ == "__main__":
    main()
