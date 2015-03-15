#!/usr/bin/env python

import os,sys,svn
import svn.local,svn.remote
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
    return "Bioconductor Release version repository completely downloaded"


def archiveLocalRepo(path):
    # Check local repository for current revision number
    localRepo = svn.local.LocalClient('/Users/nturaga/Documents/Bioconductor-Rpacks/Rpacks')
    pprint.pprint(localRepo.info())

    # Print the version number
    print localRepo.info()['commit#revision']


if __name__ == "__main__":
    downloadMainBiocRepo('/Users/nturaga/Documents/Bioconductor-Rpacks/Rpacks')
    archiveLocalRepo('/Users/nturaga/Documents/Bioconductor-Rpacks/Rpacks')
    
