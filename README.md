*What is bioaRchive?*
======================

The Bioconductor suite provides bioinformatics tools in the form of R packages, which have frequent version upgrades. However, once a Bioconductor package is upgraded, it is difficult to retrieve previous versions and that causes interoperability challenges between Galaxy and Bioconductor. The Galaxy Tool Shed enables Galaxy administrators to easily install desired versions of tools, including Bioconductor packages. However, not all Bioconductor package versions are available. To address this, we have implemented this “bioaRchive” - a repository of all versions of all Bioconductor packages and can be easily retrieved.

## Accessing the [bioaRchive](https://bioarchive.galaxyproject.org/)

Packages stored in the bioaRchive are available in an S3 bucket in a folder-like structure *https://bioarchive.galaxyproject.org/*



*bioaRchive* source code
======================

Here lives the source code for *bioaRchive*.

###Description

*bioaRchive* stores versions of BioConductor packages to promote interoperability between Galaxy and Bioconductor. The main idea is to allow users access to all the versions of current BioConductor packages.


### Main goals:

1. Promote interoperability between Galaxy and BioConductor users.
2. Archive versions of Bioconductor packages and host in a public repository.
3. Promote reproducibility within Galaxy instances using Bioconductor packages.



### Script dependencies:

Please install [Subversion](https://subversion.apache.org/)

aRchive.py should work directly when it is run. But if it doesn't and raises a dependency error, please install svn.

1. SVN

    This package can be installed using

    `sudo pip install svn`

     or

    `sudo easy_install svn`

     or

     `sudo apt-get install Subversion`
