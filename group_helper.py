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

from groups import group
from groups.group import Group

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
		


