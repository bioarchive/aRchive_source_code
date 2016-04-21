#!/usr/bin/env python

import sys
import requests
from string import Template
import urllib2

try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr
    from rpy2.robjects.vectors import StrVector
    import rpy2.robjects.packages as rpackages

except ImportError:
    raise ImportError(
        "RPy2 must be installed to use this script.")

ARCHIVE_URL_TEMPLATE = 'https://bioarchive.galaxyproject.org'
R_VERSION = '3.2'
R_PACKAGE_NAME = 'package_r_%s' % (R_VERSION.replace('.', '_'))
PACKAGE_NAME = 'monocle'
PACKAGE_VERSION = ''
README = '%s in version %s' % (PACKAGE_NAME, PACKAGE_VERSION)

PACKAGE_XML_TEMPLATE = "<package>%s</package>"

def package_exists(path):
    res = requests.head(path)
    return res.status_code == requests.codes.found

def install_dependencies():
    base = importr('base')
    base.source("http://www.bioconductor.org/biocLite.R")
    biocinstaller = importr("BiocInstaller")
    biocinstaller.biocLite("pkgDepTools")


def download_archive(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename


def test_links(urllist):
    failed_urls = []
    for i in urllist:
        try:
            urllib2.urlopen(i)
        except urllib2.HTTPError, e:
            print(e.code)
            failed_urls.appent(i)
        except urllib2.URLError, e:
            print(e.args)
    return list(set(urllist)-set(failed_urls))


def get_dependencies_url( package_name ):

    robjects.r("""
        cat("pass1")
        library("pkgDepTools")
        library("BiocInstaller")
        cat("pass2")
        getPackageDependencies <- function( package )
        {
            dependencies <- makeDepGraph(biocinstallRepos(), type="source", keep.builtin=TRUE, dosize=FALSE)
            packages <- getInstallOrder( package, dependencies, needed.only=FALSE )$packages

            contrib_url <- contrib.url(biocinstallRepos(), type = "source")
            available_packages <- available.packages( contrib_url )
            package_names <- as.vector( available_packages[,"Package"] )
            package_versions <- as.vector( available_packages[,"Version"] )
            package_urls <- as.vector(available_packages[,"Repository"])
            intersect <- match(packages, available_packages )
            intersect <- intersect[ !is.na(intersect) ]

            paste( package_urls[intersect], paste(paste( package_names[intersect], package_versions[intersect], sep="_"), "tar.gz", sep="."), sep="/" )
        }
    """
    )

    r_get_package_deps = robjects.r['getPackageDependencies']
    url_list = [url for url in r_get_package_deps( package_name ) if not url.startswith('NA')]
    tested_urls = test_links(url_list)
    return tested_urls


if __name__ == '__main__':

    urls = get_dependencies_url( PACKAGE_NAME )
    packages = []

    for url in urls:
        if url.find('bioconductor') != -1:
            aRchive_url = "%s/%s" % (ARCHIVE_URL_TEMPLATE, url.split('/')[-1])
            packages.append( PACKAGE_XML_TEMPLATE % aRchive_url )
        else:
            packages.append( PACKAGE_XML_TEMPLATE % url )
            download_archive(url)

    substitutes = {
        'R_VERSION': R_VERSION,
        'R_PACKAGE_NAME': R_PACKAGE_NAME,
        'README': README,
        'PACKAGE_NAME': PACKAGE_NAME,
        'PACKAGE_VERSION': PACKAGE_VERSION
    }

    substitutes['DEPENDENCIES'] = '\n                    '.join( packages )
    with open( 'tool_dependencies.xml' ) as handle:
        r_package_template = Template( handle.read() )
        sys.stdout.write( r_package_template.safe_substitute( substitutes ) )
