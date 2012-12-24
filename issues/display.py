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
from color import Color
from issues.issue import Issue
import config

class Column:
    name = None
    color = None
    length = None
    
    def __init__(self, name, color=Color('none'), length=None):
        self.name = name
        self.color = color
        self.length = (length if length != None else 100)

COLUMNS = {'id'     : Column('id', Color('yellow'), length=7),
           'status' : Column('status', length=7),
           'title'  : Column('title'),
           'cdate'  : Column('cdate', Color('green'), length=20),
           'mdate'  : Column('mdate', Color('green'), length=20),
           'groups' : Column('groups', Color('blue'), length=20)}

class IssueDisplayBuilder:
    def __init__(self, issue):
        if issue and type(issue) is str:
            self._issue = Issue(issue)
        else:
            self._issue = issue
    
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
    
    def getOneLineStr(self, columns):
        line = ""
        for column in columns:
            color = str(column.color)
            field = "" 
            if column.name == 'id':
                field = self.getShortIdStr()
            elif column.name == 'status':
                field = self.getStatusStr()
            elif column.name == 'title':
                field = self.getTitle()
            elif column.name == 'cdate':
                field = self.getCreatedDateStr()
            elif column.name == 'mdate':
                field = self.getModifiedDateStr()
            elif column.name == 'groups':
                import group_helper
                field = ', '.join(group_helper.getGroupsForIssueId(self.getIdStr()))
            
            fullField = color + ((field[:column.length-2] + '..') if len(field) > column.length else field)
            line += fullField + (' ' * (column.length - len(fullField)) if len(fullField) < column.length else '') + '\t'
                
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
        if self._issue.getCreatedDate() == 0:
            return "Not yet committed"
        return self._formatDateFromTimestamp(self._issue.getCreatedDate())
    
    def getModifiedDateStr(self):
        if self._issue.getModifiedDate() == 0:
            return "Not yet committed"
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