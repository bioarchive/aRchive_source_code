#!/usr/bin/env python
import os
import argparse
import json


def _important_revisions(dependency_file):
    old_version = None
    for line in dependency_file:
        # 18438	1.1.2	Biobase,multtest
	data = line.strip().split('\t')
        #(rev, version, deps) = line.strip().split('\t')
        if data[1] != old_version:
            old_version = data[1]
            if len(data) == 2:
                deps = []
            else:
                deps = data[2].split(',')
            yield (data[0], data[1], deps)


def get_version_at_rev(package, revision, archive_dir=None):
    try:
        with open(os.path.join(archive_dir, package + '_versions_full.txt'), 'r') as handle:
            for line in handle:
                if line.startswith(revision + '\t'):
                    return {'package': package, 'version': line.strip().split('\t')[1] }
    except Exception:
        return {'package': package}


def main(dependency_file):
    package_file = os.path.basename(dependency_file.name).replace('_versions_full.txt', '')
    package_dir = os.path.dirname(dependency_file.name)

    pkg_api_dir = os.path.join(package_dir, 'api', package_file)
    try:
        os.makedirs(pkg_api_dir)
    except Exception:
        pass

    for (rev, version, deps) in _important_revisions(dependency_file):
        version_deps_file = os.path.join(pkg_api_dir, '%s.json' % (version))
        versioned_deps = [get_version_at_rev(x, rev, archive_dir=package_dir)
                          for x in deps]
        with open(version_deps_file, 'w') as output:
            json.dump(versioned_deps, output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Generate easy to consume dependencies')
    parser.add_argument('dependency_file', type=file,
                        help='PACKAGE_versions_full.txt file')
    args = parser.parse_args()

    main(**vars(args))
