#!/usr/bin/env python
import json
import argparse
import os
import os.path
import subprocess
import shutil
import tarfile
import sqlite3
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(name="archive")

__author__ = 'Nitesh Turaga'
__email__ = 'nturaga1 at jhu dot edu'

class SvnClient(object):

    def __init__(self, path):
        self.repo_url = 'https://hedgehog.fhcrc.org/bioconductor/trunk/madman/Rpacks/'
        self.username = 'readonly'
        self.password = 'readonly'
        self.path = path

    def cloneOrUpdate(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        if os.path.isdir(os.path.join(self.path, ".svn")):
            subprocess.check_call(['svn', 'update'], cwd=self.path)
        else:
            subprocess.check_call([
                'svn', 'co',
                '--username', self.username,
                '--password', self.password,
                self.repo_url
            ], cwd=self.path)

    def repo_info(self):
        repo_info = {}
        tmp_info = subprocess.check_output(['svn', 'info', 'Rpacks'], cwd=self.path)
        for entry in tmp_info.split('\n'):
            if len(entry.strip()) > 0:
                key, value = entry.strip().split(': ')
                repo_info[key] = value

        return repo_info

# Download the Bioconductor Repo

    def checkout(self, revision=None):
        """
        SVN checkout a particular revision of a BioConductor package

        :type revision: str or None
        :param revision: Revision number of the package for checkout

        :rtype: None
        """
        if revision is not None:
            log.debug("Updating to rev %s" % revision)
            try:
                subprocess.check_call([
                    "svn", "update", "-r", revision
                ], cwd=self.path)
            except Exception, e:
                log.warning("Exception checking output of svn checkout version: %s", e)
        else:
            log.debug("Updating to latest rev")
            subprocess.check_call(["svn", "update"], cwd=self.path)

    def cleanup(self):
        """Run SVN cleanup on BioConductor repository
        """
        try:
            subprocess.check_call(['svn', 'cleanup', self.path])
            log.debug("Ran SVN cleanup on local copy of BioConductor repository")
        except Exception, e:
            log.warn("Could not run svn cleanup %s", self.path)
            log.warn(e)

    def diff(self, start, end):
        return subprocess.check_output([
            'svn', 'diff',
            '-r', '%s:%s' % (start, end),
            '--summarize'
        ], cwd=self.path)


class BiocPackage(object):

    def __init__(self, pack_dir, archive_dir, svnClient):
        self.pack = pack_dir
        self.svn = svnClient
        self.bioc_pack_name = os.path.split(self.pack)[-1]
        self.archive_dir = archive_dir

    def bad_yaml_parser(self):
        try:
            desc_file = os.path.join(self.path, 'DESCRIPTION')
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
            log.warn("Could not parse %s: %s" % (self.path, e))
            return {}

    def get_package_dependencies(self):
        """
        Get the dependencies of the BioConductor package by parsing the
        "DESCRIPTION" file

        Args:
        bioc_pack (str): Name of the BioConductor package
        """
        data = self.bad_yaml_parser()
        deps = []
        for key in ('Depends', 'Imports'):
            if 'Depends' in data:
                deps += [x.strip() for x in data['Depends'].split(',') if x.strip() not in deps]
        return deps

    def get_package_version(self):
        """Get the version of the BioConductor package by parsing the
        "DESCRIPTION"
        """
        data = self.bad_yaml_parser()
        if 'Version' in data:
            return data['Version']
        else:
            log.warn("Could not obtain a version number for %s", self)
            return None

    def get_available_versions(self):
        """List svn revision IDs which touched this package
        """
        # Get history of the SVN repo and get all revert IDs
        try:
            history = subprocess.check_output(['svn', 'log', '-q'], cwd=self.pack)
        except subprocess.CalledProcessError:
            log.error("SVN log unable to be accessed in this %s package" % self.pack)
            return None
        except Exception, e:
            log.error("Unexpected error while getting history: ", e)
            return None

        return [line.split()[0] for line in history.splitlines() if
                line.startswith('r')]

    def make_tarfile(self, output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    def archive_package_versions(self, latest_rev=1000):

        """
        Archive ONE package in BioConductor.
        """
        revert_ids = self.get_available_versions()
        log.debug("IDs that touched %s: %s", self.pack,
                  ','.join(revert_ids))

        # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
        latest_version = self.get_package_version()
        latest_info = self.bad_yaml_parser()
        log.info("Latest Version: %s" % latest_version)

        # Dependency info
        dependency_data = []
        # Store a list of all versions for the "API"
        stored_version = [latest_version]
        # Loop through the revert IDs to find new versions
        for rev_id in revert_ids:
            log.debug("\n\nProcessing version ID: %s" % rev_id)
            # Update repository to previous revert ID
            self.svn.checkout(self.pack, revision=rev_id)
            # Grab current version (or None if folder doesn't exist,
            # in which case we'll finish the loop)
            curr_version = self.get_package_version()
            if curr_version is not None:
                log.debug("Bioc_pack %s version of %s",
                          curr_version, self.pack)
                # Create new directory with version number as "-version" extension
                out_tarfile = "%s_%s.tar.gz" % (self.bioc_pack_name, curr_version)
                dest_tar_file = os.path.join(self.archive_dir, out_tarfile)

                log.info("\n output_directory: %s \n out_tarfile: %s \n dest_tar_file: %s" % (
                    self.archive_dir, out_tarfile, dest_tar_file))

                if curr_version not in stored_version:
                    stored_version.append(curr_version)

                if curr_version not in dependency_data:
                    deps = self.get_package_dependencies()
                    dependency_data.append((
                        int(rev_id[1:]),
                        curr_version,
                        deps
                    ))

                if not os.path.exists(dest_tar_file):
                    # SAVE THE CURRENT VERSION HERE
                    # Tar the directory
                    log.info('adding contents of bioc_pack %s to tarfile %s' % (self.bioc_pack, out_tarfile))
                    self.make_tarfile(out_tarfile, self.pack)
                    dest = os.path.join(self.archive_dir, out_tarfile)
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
            os.makedirs(os.path.join(self.archive_dir, 'api'))
        except Exception:
            pass
        with open(os.path.join(self.archive_dir, 'api', self.bioc_pack_name + '.json'), 'w') as handle:
            api_data = {
                'versions': stored_version,
                'info': latest_info,
            }
            json.dump(api_data, handle)

        dependency_data = dependency_data[::-1]
        version_list_path = os.path.join(self.archive_dir, self.bioc_pack_name + '_versions_full.txt')
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
        self.svn.checkout(self.pack)


class BiocRepo(object):

    def __init__(self, bioc_dir, archive_dir, svn):
        self.bioc_dir = bioc_dir
        self.archive_dir = archive_dir
        self.svn = svn
        self.repo_info = svn.repo_info()
        self.db = os.path.join(self.archive_dir, 'bioarchive.sqlite3')
        self.create_db(self.db)

    def create_db(self, db_path):
        self.conn = sqlite3.connect(db_path)
        cursor = self.conn.cursor()
        statements = [
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT,
                value TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bioc_packs (
                id INTEGER PRIMARY KEY,
                pack TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bioc_versions (
                id INTEGER PRIMARY KEY,
                pack_id INTEGER,
                version TEXT,
                FOREIGN KEY(pack_id) REFERENCES bioc_packs(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bioc_deps (
                id INTEGER PRIMARY KEY,
                version_id INTEGER,
                dependency TEXT
            )
            """
        ]

        for stmt in statements:
            cursor.execute(stmt)
        self.conn.commit()

    def update_index(self):
        """Updates the database index, does not generate packages.

        With the new sqlite database being stored, we only need to
        calculate changes between the revisions we've seen, rather
        than completely from end to end.
        """
        previousRevision = self.meta_get_kv('svn_rev')
        currentRevision = self.repo_info['Revision']

        self.svn.update()
        rpacks = [directory for directory in os.listdir(self.bioc_dir) if not
                  directory.startswith('.')]

        for index, package_name in enumerate(rpacks):
            pack_dir = os.path.join(self.bioc_dir, package_name)
            pack = BiocPackage(pack_dir, self.archive, self.svn)
            try:
                log.info("Archiving %s" % package_name)
                pack.archive_package_versions(latest_rev=latest_rev)
            except Exception, e:
                log.error(e)
            # Every 100 packages, run `svn cleanup`
            if index % 100 == 99:
                self.svn.cleanup()
        log.info("aRchive has been created.")

        # Store a list of all packages to an "API"
        try:
            os.makedirs(os.path.join(self.archive_dir, 'api'))
        except Exception:
            pass
        with open(os.path.join(self.archive_dir, 'api', 'api.json'), 'w') as handle:
            json.dump(rpacks, handle)


        # self.meta_set_kv('svn_rev', int(self.repo_info['Revision']))

    def meta_get_kv(self, key):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT value FROM meta WHERE key == ?""",
            (key, )
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0]

    def meta_set_kv(self, key, value):
        val = self.meta_get_kv(key)
        cursor = self.conn.cursor()

        if val is not None:
            q = """UPDATE meta SET value = ? where key = ?"""
            d = (value, key)
        else:
            q = """INSERT INTO meta VALUES (?, ?)"""
            d = (key, value)

        cursor.execute(q, d)

        self.conn.commit()


def main():
    # Add command line parsing options
    parser = argparse.ArgumentParser(add_help=True, description=(
        "Create Bioconductor archive for "
        "all packages, and version them based on commit history. If the command is rerun,"
        "it should automatically add to an existing archive."
    ))
    parser.add_argument("bioc", help="Path to clone bioconductor directory")
    parser.add_argument("arch", help="Output directory for created BioConductor aRchives")
    args = parser.parse_args()

    # Define directories
    bioc_dir = os.path.abspath(args.bioc)
    archives = os.path.abspath(args.arch)
    log.info("aRchive is being run in %s " % bioc_dir)
    log.info("aRchive is being stored in %s" % archives)

    svn = SvnClient(bioc_dir)
    # svn.cloneOrUpdate()

    # Make the directory which user specifies to build the archive.
    if not os.path.exists(archives):
        os.mkdir(archives)

    bioc = BiocRepo(bioc_dir, archives, svn)
    bioc.update_index()
    # bioc.archive_local_repository()

if __name__ == "__main__":
    main()
