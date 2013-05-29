#! /usr/bin/env python
#
# Copyright (C) 2012-2013 Lorne Liechty
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from utils.subprocess_helper import getCmd
import commit_helper
import config
import os

NAME="init"
HELP="give git issues"

class Args:
    """Wrapper class that defines the command line args"""
    @staticmethod
    def addCmdToParser(parser):
        cmd_init = parser.add_parser(NAME, help=HELP)
        
        cmd_init.set_defaults(func=execute)

def execute(args):
    bFileAdd = False
        
    # Check to see if the .ghi directories have already been created
    # If it doesn't exist, create it.
    if os.path.isdir(config.GHI_DIR) == False:
        os.makedirs(config.GHI_DIR)
        _writeGhiDirGitIgnoreFile(config.GHI_DIR + "/.gitignore")
        bFileAdd = True

    if os.path.isdir(config.ISSUES_DIR) == False:
        os.makedirs(config.ISSUES_DIR)
        # Touch a .gitignore file in the ISSUES_DIR so that we can
        # track the directory in git before any issues get added
        getCmd("touch " + config.ISSUES_DIR + "/.gitignore")
        bFileAdd = True

    if os.path.isdir(config.GROUPS_DIR) == False:
        os.makedirs(config.GROUPS_DIR)
        # Touch a .gitignore file in the GROUPS_DIR so that we can
        # track the directory in git before any issues get added
        getCmd("touch " + config.GROUPS_DIR + "/.gitignore")
        bFileAdd = True

    for key, val in config.STATUS_OPTS.iteritems():
        getCmd('git config '
                + '-f ' + config.GHI_DIR + '/config '
                + 'status.s' + str(key) + ' "' + val + '"')

    if bFileAdd:
        commit_helper.cleanWcAndCommitGhiDir("Initializing ghi")

    # Alias "git issue" to ghi
    getCmd("git config alias.issue '!ghi'")
    ghicmdpath = "ghi"

    # Insert git hooks
    getCmd("cp " + ghicmdpath + "/hooks/prepare-commit-msg "
                + config.GIT_ROOT + "/.git/hooks/")

    # Clever successful response message... in the future it would
    # be nice if running 'ghi-init' on a git that already has issues
    # would give you a summary of stats on the current issues of that
    # git
    print "Initialized ghi, but this git currently has no issues"

def _writeGhiDirGitIgnoreFile(filepath):
    with open(filepath, 'wb') as f:
        f.write("ISSUE_EDIT\n")
    f.close()
