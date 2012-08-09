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
	return os.path.exists(getPathForGroup(groupname))

def getPathForGroup(groupname):
	groupPath = config.GROUPS_DIR + "/" + groupname
	return groupPath

def getIssueIdsInGroups():
	ret = {};
	for group in dircache.listdir(config.GROUPS_DIR):
		if not group == ".gitignore":
			filepath = config.GROUPS_DIR + "/" + group
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

def rmIssueInGroup(issueID, groupname):
	with open(getPathForGroup(groupname), "rb") as f:
		lines = f.readlines()
		groupIDs = [line.rstrip() for line in lines]
	
	# If we're removing the last issue in a file, then rm the file
	if len(groupIDs) == 1 and groupIDs[0] == issueID:
		# HACK HACK HACK
		# Should not be executing a git command here
		#
		# Another Hackish note...
		# It's possible for the user, when they run multiple 
		# ghi-rm commands in a row without committing, to here
		# try to remove the group file when changes to it are
		# already staged in the index. Really we should try to
		# get confirmation from the user in this scenario (maybe?)
		# ... but for now we're just going to force the remove
		# with '-f'
		getCmd('git rm -f "' + getPathForGroup(groupname) + '"')
	else:
		with open(getPathForGroup(groupname), "wb") as f:
			for identifier in groupIDs:
				if not identifier == issueID:
					f.write(identifier + "\n")

		# HACK HACK HACK
		# Should not be executing a git command here
		getCmd('git add "' + getPathForGroup(groupname) + '"')