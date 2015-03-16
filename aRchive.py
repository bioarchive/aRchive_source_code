#!/usr/bin/env python

import os,sys
import svn,svn.local,svn.remote
import pprint


# Download the Bioconductor Repo
def downloadMainBiocRepo(path):
    """
    Check out the main repository from Bioconductor giving 
    user-name: readonly; 
    password: readonly;
    """
    os.chdir(path)
    if os.path.isdir(".svn"):
        os.system("svn update")
        print "SVN repo updated"
    else:        
        mainRepo = svn.remote.RemoteClient("https://hedgehog.fhcrc.org/bioconductor/branches/RELEASE_3_0/madman/Rpacks/")
        pprint.pprint(mainRepo.info())
        mainRepo.checkout(path)
    return "Bioconductor Release version repository downloaded"


def makeVersion(folder):
    print "Package %s has been versioned" % folder
    
    return 


def archiveLocalRepo(path):
    # Check local repository for current revision number
    localRepo = svn.local.LocalClient(path)
    pprint.pprint(localRepo.info())
    # Print the version number
    print "Printing Repository revision number: ", localRepo.info()['commit#revision']
    rpacks = os.listdir(path)
    for folder in rpacks:
        if os.path.isdir(os.path.join(path,folder)):
            makeVersion(folder)
    return "aRchive has been created."

if __name__ == "__main__":
    # Run the install dependency function

    # import dependency_install
    # dependency_install.install_and_import('svn')
    # downloadMainBiocRepo('/Users/nturaga/Documents/Bioconductor-Rpacks/Rpacks')
    
    archiveLocalRepo('/Users/nturaga/Documents/Bioconductor-Rpacks/Rpacks')
    
