#!/usr/bin/env python

"""
Author: Nitesh Turaga
Email: nturaga1 at jhu dot edu

This script works entirely in the user specified folder:
1. Clones the BIOCONDUCTOR REPOSITORY in the folder
2. Creates an archive in the same specified folder.
3. If there already exists a folder with packages, it updates the aRchive
    with new versions.

Usage: python aRchive.py -dir <Rpacks folder>

"""

import os
import sys
import subprocess
import re
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
        os.system("svn co --username readonly --password readonly https://hedgehog.fhcrc.org/bioconductor/branches/RELEASE_3_0/madman/Rpacks/")
    return "Bioconductor Release version repository downloaded"


def makeVersion(folder):
    # Change into current bioconductor package
    os.chdir(folder)
    # Get history of the SVN repo and get all revert IDs
    history = subprocess.check_output(['svn','log'])
    revert_ids = [line[0:line.find(" |")] for line in history.splitlines() if re.match("^r[0-9]",line)]
    # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
    with open(os.path.join(folder,"DESCRIPTION")) as fp:
        latest_version = str([line[8:].strip() for i,line in enumerate(fp) if re.match("^Version: [0-9]",line)][0])
    print "Latest Version", latest_version
    # Loop through the revert IDs to find new versions
    for id in revert_ids:
        # Update repository to previous revert ID
        cmd = subprocess.Popen(["svn","update","-r", id],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = cmd.communicate()
        localRepo = svn.local.LocalClient('.')
        with open(os.path.join(folder,"DESCRIPTION")) as fp2:
            curr_version = str([line[8:].strip() for i,line in enumerate(fp2) if re.match("^Version: [0-9]",line)][0])
        print "\n\n\n Current revision is %s at %s version \n\n"% (str(localRepo.info()['commit#revision']),curr_version)

        if curr_version==latest_version:
            print curr_version==latest_version
            latest_version = curr_version
            # TODO: LOGIC ERROR
        else:
            print "Save to another folder"
            # os.system("tar -zxvf .")
        if id=="r100643":break
    # Return to most recent update
    update_cmd = subprocess.Popen(["svn","update"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    update_out,update_err=update_cmd.communicate()
    return 


def archiveLocalRepo(path):
    # Check local repository for current revision number
    localRepo = svn.local.LocalClient(path)
    # pprint.pprint(localRepo.info())
    # Print the version number
    # print "Printing Repository revision number: ", localRepo.info()['commit#revision']
    rpacks = os.listdir(path)
    testPack = rpacks[rpacks.index('DESeq2')]
    makeVersion(os.path.join(path,testPack))
    # for folder in rpacks:
        # if os.path.isdir(os.path.join(path,folder)) and not folder.startswith("."):
            # makeVersion(os.path.join(path,folder))
    return "aRchive has been created."



if __name__ == "__main__":
    # Run the install dependency function

    import argparse
    parser = argparse.ArgumentParser(add_help=True, description="Create Bioconductor archive for all packages, \
        and version them based on commit history. If the command is rerun, it should automatically add to an \
        existing archive.")
    parser.add_argument("-dir",dest="archive_directory",help="Name of directory where aRchive.py should work",type=str)

    if len(sys.argv) <= 1:
        parser.print_usage()
        sys.exit(1)
    else:
        args = parser.parse_args()

    ARCHIVE_DIR = os.path.abspath(args.archive_directory)
    print "aRchive is being run in %s " % ARCHIVE_DIR
    downloadMainBiocRepo(ARCHIVE_DIR)
    # archiveLocalRepo(ARCHIVE_DIR)
    
