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

import uuid
import config
import dircache

def genNewIssueID():
	return uuid.uuid4()

def getFullIssueIdFromLeadingSubstr(substr):
	'''Returns the full ID string for a given leading substring.
	Returns None if the substring is not found in any known Issue
	ID.'''
	if (substr == None):
		return None
	
	#Get the list of all IDs
	for issueID in dircache.listdir(config.ISSUES_DIR):
		if (issueID.find(substr,0,len(substr)) == 0):
			return issueID
	
	return None

def getPathFromId(identifier):
	# For now assume that this is an issue
	return config.ISSUES_DIR + "/" + identifier