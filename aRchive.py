#!/usr/bin/env python

"""
Author: Nitesh Turaga
Email: nturaga1 at jhu dot edu

Please contact me for any questions regarding this abstract and code.

This script works entirely in the user specified folder:
1. Clones the BIOCONDUCTOR REPOSITORY in the folder
2. Creates an archive in the same specified folder.
3. If there already exists a folder with packages, it updates the aRchive
    with new versions.

Usage: python aRchive.py -dir <Rpacks folder>

NOTE: If you do not run the dependency installation for SVN, then the following program will throw an 
    error.
"""

import os
import os.path
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


def makeVersion(bioc_pack,archive_dir):
    # Change into current bioconductor package
    os.chdir(bioc_pack)
    # Get history of the SVN repo and get all revert IDs
    history = subprocess.check_output(['svn','log'])
    revert_ids = [line[0:line.find(" |")] for line in history.splitlines() if re.match("^r[0-9]",line)]
    print revert_ids
    # Get the version number of the Bioconductor package from DESCRIPTION file in SVN repo
    with open(os.path.join(bioc_pack,"DESCRIPTION")) as fp:
        latest_version = str([line[8:].strip() for i,line in enumerate(fp) if re.match("^Version: [0-9]",line)][0])
    print "Latest Version", latest_version
    # Loop through the revert IDs to find new versions
    for id in revert_ids:
        # Update repository to previous revert ID
        cmd = subprocess.Popen(["svn","update","-r", id],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = cmd.communicate()
        localRepo = svn.local.LocalClient('.')
        with open(os.path.join(bioc_pack,"DESCRIPTION")) as fp2:
            curr_version = str([line[8:].strip() for i,line in enumerate(fp2) if re.match("^Version: [0-9]",line)][0])
        print "\n\n\n Current revision is %s at %s version \n\n"% (str(localRepo.info()['commit#revision']),curr_version)

        if curr_version!=latest_version:
            print bioc_pack 
            # Create new directory with version number as "-version" extention
            bioc_pack = os.path.split(bioc_pack)[-1] + str(curr_version)
            if not os.path.exists(os.path.join(archive_dir,bioc_pack)):
                # TODO: LOGIC ERROR
                os.mkdir(os.path.join(archive_dir,bioc_pack))
                print "HERE"
                # SAVE THE CURRENT VERSION HERE
                
        else:
            print "Save to another bioc_pack"
            # os.system("tar -zxvf .")
        if id=="r101096":break
    # Return to most recent update
    update_cmd = subprocess.Popen(["svn","update"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    update_out,update_err=update_cmd.communicate()
    return 


def archiveLocalRepo(bioc_dir,archive_dir):
    # Check local repository for current revision number
    # localRepo = svn.local.LocalClient(bioc_path)
    # pprint.pprint(localRepo.info())
    # Print the version number
    # print "Printing Repository revision number: ", localRepo.info()['commit#revision']
    print bioc_dir
    print archive_dir
    # Make the directory which user specifies to build the archive. 
    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir)
        print "Made %s" % archive_dir
    # Get all bioconductor packages
    rpacks = os.listdir(bioc_dir)
    # TEST only DESeq2 , Remove this to run on all packages
    testPack = rpacks[rpacks.index('DESeq2')]
    #CALL make version
    makeVersion((os.path.join(bioc_dir,testPack)),archive_dir)
    for bioc_pack in rpacks:
        if os.path.isdir(os.path.join(path,bioc_pack)) and not bioc_pack.startswith("."):
            # Make Versions for EACH R package
            makeVersion(os.path.join(path,bioc_pack))
    return "aRchive has been created."



if __name__ == "__main__":
    # Run the install dependency function

    import argparse
    parser = argparse.ArgumentParser(add_help=True, description="Create Bioconductor archive for all packages, \
        and version them based on commit history. If the command is rerun, it should automatically add to an \
        existing archive.")
    parser.add_argument("-bioconductor_dir",dest="bioconductor_dir",help="Name of directory where aRchive.py should work i.e the Bioconductor clone repository",type=str)
    parser.add_argument("-archive_dir",dest="archive_dir",help="Directory name to host all versions of all bioconductor packages. This is where the archive lives",type=str)
    if len(sys.argv) <= 2:
        parser.print_usage()
        sys.exit(1)
    else:
        args = parser.parse_args()


    BIOCONDUCTOR_DIR = os.path.abspath(args.bioconductor_dir)
    ARCHIVE_DIR = os.path.abspath(args.archive_dir)
    print "aRchive is being run in %s " % BIOCONDUCTOR_DIR
    print "aRchive is being stored in %s" % ARCHIVE_DIR
    # downloadMainBiocRepo(BIOCONDUCTOR_DIR)
    archiveLocalRepo(BIOCONDUCTOR_DIR,ARCHIVE_DIR)
    
