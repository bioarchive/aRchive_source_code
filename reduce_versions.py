#!/usr/bin/env python
import os
import argparse


def _important_revisions(dependency_file):
    old_version = None
    for line in dependency_file:
        # 18438	1.1.2	Biobase,multtest
        (rev, version, deps) = line.strip().split('\t')
        if version != old_version:
            old_version = version
            yield (rev, version, deps.split(','))


def get_version_at_rev(package, revision, archive_dir=None):
    try:
        with open(os.path.join(archive_dir, package + '_versions_full.txt'), 'r') as handle:
            for line in handle:
                if line.startswith(revision + '\t'):
                    return '\t'.join((
                        package,
                        line.strip().split('\t')[1],
                        '%s_%s_dependencies.txt' % (package, line.strip().split('\t')[1]),
                        '%s_%s.tar.gz' % (package, line.strip().split('\t')[1])
                    ))
    except Exception:
        return "# Could not find %s at r%s" % (package, revision)


def main(dependency_file):
    package_file = os.path.basename(dependency_file.name).replace('_versions_full.txt', '')
    package_dir = os.path.dirname(dependency_file.name)
    for (rev, version, deps) in _important_revisions(dependency_file):
        version_deps_file = os.path.join(package_dir, '%s_%s_dependencies.txt' % (package_file, version))

        versioned_deps = [get_version_at_rev(x, rev, archive_dir=package_dir)
                          for x in deps]
        with open(version_deps_file, 'w') as output:
            output.write('\n'.join(versioned_deps))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Generate easy to consume dependencies')
    parser.add_argument('dependency_file', type=file,
                        help='PACKAGE_versions_full.txt file')
    args = parser.parse_args()

    main(**vars(args))
