#! /usr/bin/env python
from color import Color
from subprocess_helper import getCmd
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
	def __init__(self, identifier):
		self._id = identifier
		
	def getId(self):
		return self._id
	
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
		tmp = IssueFile.readIssueFromDisk(
			config.ISSUES_DIR + '/' + self._id)
		self.setTitle(tmp.getTitle())
		self.setStatus(tmp.getStatus())
		self.setDescription(tmp.getDescription())
		
	def _loadDates(self):
			cmd = ('git log'
				+ ' --topo-order'
				+ ' --reverse'
				+ ' --pretty=format:"%H %at %an %ae"'
				+ ' HEAD'
				+ ' -- ' + config.ISSUES_DIR + "/" + self.getId())
			commits = getCmd(cmd).split('\n')
			if commits:
				self._createdDate = 		commits[0].split()[1]
				self._createdAuthorName = 	commits[0].split()[2]
				self._createdAuthorEmail = 	commits[0].split()[3]

				self._modifiedDate = 		commits[-1].split()[1]
				self._modifiedAuthorName = 	commits[-1].split()[2]
				self._modifiedAuthorEmail = commits[-1].split()[3]


class IssueDisplayBuilder:
	def __init__(self, identifier):
		self._issue = Issue(identifier)
	
	def getFullIssueDisplay(self):
		lines = []
		lines.extend([str(Color('yellow')) + 
					"Issue ID: " + self.getIdStr() + '\n'])
		
		lines.extend([str(Color('none')) +
					"Created: " + self.getCreatedDateStr() + '\t' +
					"Author: " + self.getCreatedAuthorStr() + '\n'])
				
		lines.extend([str(Color('none')) +
					"Modified: " + self.getModifiedDateStr() + '\t' +
					"Author: " + self.getModifiedAuthorStr() + '\n'])
				
		lines.extend([str(Color('none')) +
					"Status: " + self.getStatusStr() + '\n'])
		
		lines.extend(['\n'])
		lines.extend([str(Color('none')) + 
					"Title: " + self.getTitle() + '\n'])
		lines.extend(['-' * 80])
		
		lines.extend(['\n'])
		lines.extend(str(Color('none')) +
					self.getDescription())
		
		line = ""
		for l in lines: 
			line += l
		
		return line
	
	def getOneLineStr(self):
		clr_y = str(Color('yellow'))
		clr_n = str(Color('none'))
		
		line = clr_y + self.getShortIdStr()
		
		stat = self.getStatusStr()
		line += clr_n + '\t' + ((stat[:5] + '..') if len(stat) > 7 else stat)
		line += clr_n + '\t' + self.getTitle()
		
		return line
	
	def getIdStr(self):
		return self._issue.getId()
	
	def getShortIdStr(self):
		return self._issue.getId()[:7]
	
	def getTitle(self):
		return self._issue.getTitle(False)
	
	def getStatusStr(self):
		if not hasattr(self,'_issue'):
			self._loadFullIssue()
		return config.STATUS_OPTS[int(self._issue.getStatus())]

	def getDescription(self):
		return self._issue.getDescription()
				
	def getCreatedDateStr(self):
		return self._formatDateFromTimestamp(self._issue.getCreatedDate())
	
	def getModifiedDateStr(self):
		return self._formatDateFromTimestamp(self._issue.getModifiedDate())
	
	def getCreatedAuthorStr(self):
		return (self._issue.getCreatedAuthorName()
			+ "<" + self._issue.getCreatedAuthorEmail() + ">")
	
	def getModifiedAuthorStr(self):
		return (self._issue.getModifiedAuthorName()
			+ "<" + self._issue.getModifiedAuthorEmail() + ">")
	
	def _formatDateFromTimestamp(self, timestamp):
		import time
		localtime = time.localtime(int(timestamp))
		dateStr = str(localtime.tm_year)
		dateStr += "-" + str(localtime.tm_mon)
		dateStr += "-" + str(localtime.tm_mday)
		dateStr += " " + str(localtime.tm_hour)
		dateStr += ":" + str(localtime.tm_min)
		dateStr += ":" + str(localtime.tm_sec)
		return dateStr

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
