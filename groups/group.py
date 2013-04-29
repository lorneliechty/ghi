#! /usr/bin/env python
#
# Copyright (C) 2012 Lorne Liechty
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

from subprocess_helper import getCmd
import config
import os.path

def getListOfAllGroups():
    ret = []
    for paths, dirs, files in os.walk(config.GROUPS_DIR):
        for f in files:
            if not f == '.gitignore':
                ret.extend(
                   [os.path.join(paths,f).partition(config.GROUPS_DIR + os.sep)[2]]
                   )
    return ret

def getIssueIdsInGroups():
    ret = {};
    for group in getListOfAllGroups():
        filepath = config.GROUPS_DIR + os.sep + group
        with open(filepath, 'rb') as f:
            lines = f.readlines()
            ret[group] = [line.rstrip() for line in lines]
    
    return ret

def getGroupsForIssueId(issueID):
    groupPaths = getCmd("git grep --name-only " 
                + issueID + " -- " + config.GROUPS_DIR)

    groups = []
    pathPrefix = config.GROUPS_DIR[len(config.GIT_ROOT) + 1:] # +1 to remove '/'
    if groupPaths != None:
        for path in groupPaths.splitlines():
            groupname = path[len(pathPrefix) + 1:] # +1 to remove '/'
            groups.extend([groupname]) 
    
    return groups

def exists(group):
    if group is None:
        return False
    
    try:
        # Assume the input is a Group
        path = group.getPath()
        
    except:
        # Assume that the input is a string
        path = Group(group).getPath()
        
    return os.path.exists(path)
    
class Group:
    _path = None
    _name = None
    
    def __init__(self, name = None):
        if name:
            self._name = name
    
    def getPath(self):
        if self._path is None and self.getName():
            self._path = config.GROUPS_DIR + os.sep + self.getName()
            
        return self._path

    def getName(self):
        return self._name
    
    def getIssueIds(self):
        with open(self.getPath(), 'rb') as f:
            lines = f.readlines()
            ret = [line.rstrip() for line in lines]
        return ret
    
    def addIssue(self, issueID):
        if self.hasIssue(issueID):
            # Keep group issue lists unique
            return None

        # Issue not already in group, so add it
        # First see if this is a subgroup and contains some directory structure
        if self.getPath().find(os.sep) > -1:
            parentGroup = self.getPath().rpartition(os.sep)[0]
            if not os.path.exists(parentGroup):
                os.mkdir(parentGroup)

        # Now actually add the issue to the group (creating if necessary)
        try:
            with open(self.getPath(), "ab") as f:
                f.write(issueID + "\n")
                
        except IOError:
            if os.path.exists(self.getPath()):
                # Kind of a hack... shouldn't be printing from here :(
                print 'Cannot add issue to subgroup parent!'
    
    def hasIssue(self, issueID):
        try:
            with open(self.getPath(), 'rb') as f:
                lines = f.read()
                if lines.count(issueID):
                    # Issue already in group
                    return True
                
        except IOError:
            # Group doesn't exist yet...
            pass

        return False
    
    def rmIssue(self, issueID, force = False):
        if not self._canRmIssueFromGroup(issueID, force):
            return False
        
        groupIDs = self.getIssueIds()
        
        # If we're removing the last issue in a file, then rm the file
        if len(groupIDs) == 1 and groupIDs[0] == issueID:
            # HACK HACK HACK
            # Should not be executing a git command here
            if force:
                getCmd('git rm -f "' + self.getPath() + '"')
            else:
                getCmd('git rm "' + self.getPath() + '"')
        else:
            with open(self.getPath(), "wb") as f:
                for identifier in groupIDs:
                    if not identifier == issueID:
                        f.write(identifier + "\n")
    
            # HACK HACK HACK
            # Should not be executing a git command here
            getCmd('git add "' + self.getPath() + '"')
    
    def _canRmIssueFromGroup(self, issueID, force = False):
        if force:
            return True
        
        groupIDs = self.getIssueIds()
        
        if groupIDs.count(issueID) == 0 or len(groupIDs) == 0:
            return False
        
        # If there is more than one issue in the group we can always
        # successfully remove (assuming the issue is in this group)
        if len(groupIDs) > 1:
            return True
        
        # If this group only has one issue and we're trying to remove
        # it then we have to remove the group file as well. If this is
        # the case and the group is already modified in the git
        # index then we need a force to make this happen
        else: # len(groupIDs) == 1
            groupGitStatus = getCmd('git status --porcelain -- "' + self.getPath() + '"') 
            if groupGitStatus and groupGitStatus[0] != " ":
                return False
        
        return True
