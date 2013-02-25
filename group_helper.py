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

from groups.group import Group
from subprocess_helper import getCmd
import config
import dircache

def groupExists(groupname):
	return Group.Exists(groupname)

def getPathForGroup(groupname):
	group = Group(groupname)
	if group:
		return group.getPath()
	return None

def getIssueIdsInGroups():
	ret = {};
	for group in dircache.listdir(config.GROUPS_DIR):
		if not group == ".gitignore":
			filepath = config.GROUPS_DIR + "/" + group
			with open(filepath, 'rb') as f:
				lines = f.readlines()
				ret[group] = [line.rstrip() for line in lines]
	
	return ret

def getIssueIdsInGroup(groupname):
	group = Group(groupname)
	if group:
		return group.getIssueIds()
	return None

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

def addIssueToGroup(issueID, groupname):
	group = Group(groupname)
	if group:
		return group.addIssue(issueID)
	return None
		
def canRmIssueFromGroup(issueID, groupname, force=False):
	group = Group(groupname)
	if group:
		return group._canRmIssueFromGroup(issueID, force)
	return None

def rmIssueInGroup(issueID, groupname, force=False):
	group = Group(groupname)
	if group:
		group.rmIssue(issueID, force)
	return None
		
def rmIssueFromGroups(issueID, force=False):
	groups = getGroupsForIssueId(issueID)




