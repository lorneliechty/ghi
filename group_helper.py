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
import dircache
import os

def groupExists(groupname):
	if groupname:
		return os.path.exists(getPathForGroup(groupname))
	return None

def getPathForGroup(groupname):
	if groupname:
		return config.GROUPS_DIR + "/" + groupname
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
	with open(getPathForGroup(groupname), 'rb') as f:
		lines = f.readlines()
		ret = [line.rstrip() for line in lines]
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

def addIssueToGroup(issueID, groupname):
	path = getPathForGroup(groupname)
	try:
		with open(path, "rb") as f:
			lines = f.read()
			if lines.count(issueID):
				# Issue already in group
				return None
	except IOError:
		# Group doesn't exist yet... carry on.
		pass
	
	# Issue not already in group, so add it
	with open(path, "ab") as f:
		f.write(issueID + "\n")
		
def canRmIssueFromGroup(issueID, groupname, force=False):
	if force:
		return True
	
	groupIDs = getIssueIdsInGroup(groupname)
	
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
		groupGitStatus = getCmd('git status --porcelain -- "' + getPathForGroup(groupname) + '"') 
		if groupGitStatus and groupGitStatus[0] != " ":
			return False
	
	return True

def rmIssueInGroup(issueID, groupname, force=False):
	groupIDs = getIssueIdsInGroup(groupname)
	
	# If we're removing the last issue in a file, then rm the file
	if len(groupIDs) == 1 and groupIDs[0] == issueID:
		# HACK HACK HACK
		# Should not be executing a git command here
		if force:
			getCmd('git rm -f "' + getPathForGroup(groupname) + '"')
		else:
			getCmd('git rm "' + getPathForGroup(groupname) + '"')
	else:
		with open(getPathForGroup(groupname), "wb") as f:
			for identifier in groupIDs:
				if not identifier == issueID:
					f.write(identifier + "\n")

		# HACK HACK HACK
		# Should not be executing a git command here
		getCmd('git add "' + getPathForGroup(groupname) + '"')
		
def rmIssueFromGroups(issueID, force=False):
	groups = getGroupsForIssueId(issueID)
	
	pass




