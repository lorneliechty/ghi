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
import config

class IssueProto:
	"""Class that represents an Issue"""
	
	def getTitle(self):
		if not hasattr(self,'_title'):
			return r""
		return self._title
	
	def setTitle(self, title):
		self._title = title
	
	def getDescription(self):
		if not hasattr(self, '_description'):
			return r""
		return self._description
	
	def setDescription(self, description):
		self._description = description
	
	def getStatus(self):
		if not hasattr(self, '_status'):
			return 0
		return self._status
	
	def setStatus(self, status):
		self._status = status
	
class Issue(IssueProto):
	def __init__(self, identifier, ref=None):
		self._id = identifier
		self._ref = ref

	def getId(self):
		return self._id
	
	def getRef(self):
		return self._ref
	
	def getTitle(self, peak=True):
		if not hasattr(self, '_title'):
			if peak:
				self._title = IssueFile.peakTitle(
					config.ISSUES_DIR + '/' + self.getId())
			else:
				self._loadIssueFile()
		return IssueProto.getTitle(self)
	
	def getDescription(self):
		if not hasattr(self, '_description'):
			self._loadIssueFile()
		return IssueProto.getDescription(self)
	
	def getStatus(self):
		if not hasattr(self, '_status'):
			self._loadIssueFile()
		return IssueProto.getStatus(self)
	
	# Lazy load scm-based issue metadata so that we don't take
	# the performance hit of querying this data if we don't
	# have to.
	def getCreatedDate(self):
		'''Date on which the issue was first committed into the repository'''
		if not hasattr(self, '_createdDate'):
			self._loadDates()
		return self._createdDate
	
	def getCreatedAuthorName(self):
		if not hasattr(self, '_createdAuthorName'):
			self._loadDates()
		return self._createdAuthorName
	
	def getCreatedAuthorEmail(self):
		if not hasattr(self, '_createdAuthorEmail'):
			self._loadDates()
		return self._createdAuthorEmail
	
	def getModifiedDate(self):
		'''Date on which the issue was last modified in the repository'''
		if not hasattr(self, '_modifiedDate'):
			self._loadDates()
		return self._modifiedDate
	
	def getModifiedAuthorName(self):
		if not hasattr(self, '_modifiedAuthorName'):
			self._loadDates()
		return self._modifiedAuthorName
	
	def getModifiedAuthorEmail(self):
		if not hasattr(self, '_modifiedAuthorEmail'):
			self._loadDates()
		return self._modifiedAuthorEmail
	
	def _loadIssueFile(self):
		if self._ref == None:
			tmp = IssueFile.readIssueFromDisk(
				config.ISSUES_DIR + '/' + self._id)
		else:
			getCmd('git show ' + self.getRef() + ':' + config.mkPathRel(config.ISSUES_DIR) + '/' + self._id 
					+ ' > ' + config.mkPathRel(config.GHI_DIR) + '/tmpfile')
			tmp = IssueFile.readIssueFromDisk(config.GHI_DIR + '/tmpfile')
			getCmd('rm ' + config.GHI_DIR + '/tmpfile')
		
		self.setTitle(tmp.getTitle())
		self.setStatus(tmp.getStatus())
		self.setDescription(tmp.getDescription())
		
	def _loadDates(self):
		revision = 'HEAD' if self.getRef() == None else self.getRef()
		cmd = ('git log'
			+ ' --topo-order'
			+ ' --reverse'
			+ ' --pretty=format:"%H %at %an %ae"'
			+ ' ' + revision
			+ ' -- ' + config.ISSUES_DIR + "/" + self.getId())
		commits = getCmd(cmd)
		if commits:
			commits = commits.split('\n')
			self._createdDate = 		commits[0].split()[1]
			self._createdAuthorName = 	commits[0].split()[2]
			self._createdAuthorEmail = 	commits[0].split()[3]

			self._modifiedDate = 		commits[-1].split()[1]
			self._modifiedAuthorName = 	commits[-1].split()[2]
			self._modifiedAuthorEmail = commits[-1].split()[3]
		else:
			self._createdDate = 		0
			self._createdAuthorName = 	getCmd("git config user.name")
			self._createdAuthorEmail = 	getCmd("git config user.email")

			self._modifiedDate = 		0
			self._modifiedAuthorName = 	getCmd("git config user.name")
			self._modifiedAuthorEmail = getCmd("git config user.email")

class IssueFile:
	"""Wraps all file I/O for Issues"""
	FIELD_DELIM = '\n'
	FILE_TAG = "ISSUE-1"

	@staticmethod
	def writeIssueToDisk(filepath, issue):
		my = IssueFile
		with open(filepath, 'wb') as f:
			f.write(my.FILE_TAG + my.FIELD_DELIM)
			f.write(str(issue.getStatus()) + my.FIELD_DELIM)
			f.write(issue.getTitle() + my.FIELD_DELIM)
			f.write(issue.getDescription() + my.FIELD_DELIM)

	@staticmethod
	def readIssueFromDisk(filepath):
		my = IssueFile
		issue = IssueProto()
		with open(filepath, 'rb') as f:
			# Verify file type
			buf = f.readline().strip()
			if buf != my.FILE_TAG:
				print "FAIL!", buf
				return None
			
			# Status
			issue.setStatus(f.readline().strip())
			# Title
			issue.setTitle(f.readline().strip())
			
			# All remaining lines in the file are the issue description
			description = ""
			lines = f.readlines()
			for l in lines:
				description += l
			# Remove any trailing new line
			issue.setDescription(description.rstrip())

		return issue
	
	@staticmethod
	def writeEditableIssueToDisk(filepath, issue):
		with open(filepath, 'wb') as f:
			# Title with helper comment
			f.write('# TITLE: One line immediately below this comment' + '\n')
			f.write(issue.getTitle() + '\n')
			
			# Status with helper comment
			f.write("\n")
			f.write('# STATUS: One line immediately below this comment' + '\n')
			f.write('# Legal values are:' + '\n')
			statusOpts = config.STATUS_OPTS
			for val,status in statusOpts.iteritems():
				f.write('#\t' + str(val) + ': ' + status + '\n')
			f.write(str(issue.getStatus()) + '\n')
			
			# Description with helper comment
			f.write("\n")
			f.write('# DESCRIPTION: All lines below this comment' + '\n')
			f.write(issue.getDescription() + '\n')

	@staticmethod
	def readEditableIssueFromDisk(filepath):
		issue = IssueProto()
		with open(filepath, 'rb') as f:
			lines = f.readlines()
			n = 0
			description = ""
			for l in lines:
				if (l.find('#',0,1) == -1 
					and (n > 2 or not len(l.rstrip()) == 0)):
					
					if (n==0):
						issue.setTitle(l.rstrip())
					elif (n==1):
						issue.setStatus(l.rstrip())
					else:
						description += l			
					n += 1
																
			# Remove any trailing new line
			issue.setDescription(description.rstrip())

		return issue
	
	@staticmethod
	def peakTitle(filepath):
		my = IssueFile
		with open(filepath, 'rb') as f:
			# Verify file type
			buf = f.readline().strip()
			if buf != my.FILE_TAG:
				print "FAIL!", buf
				return None
			
			# Status
			f.readline().strip()
			
			# Title
			return f.readline().strip()
