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

from utils.color import Color
from utils.console_display_utils import truncateOrPadStrToWidth
from groups import group
from groups.group import Group
from issues import identifiers, display
from issues.display import IssueDisplayBuilder
from issues.identifiers import getFullIssueIdFromLeadingSubstr
from issues.issue import Issue
from utils.pager import PageOutputBeyondThisPoint
from subprocess_helper import getCmd
import config
import dircache
import sys

NAME = "ls"
HELP = "List issues"

class Args:
    """Wrapper class that defines the command line args"""
    ID="id"
    ID_HELP="Issue ID"
    ID_NARGS="?"
    
    OPT_GROUPED="--group"
    OPT_GROUPED_HELP="List issues by group"
    OPT_GROUPED_ACTION="store_true"
    
    OPT_SORT="--sort"
    OPT_SORT_HELP="Sort issues"
    
    @staticmethod
    def addCmdToParser(parser):
        cmd_ls = parser.add_parser(NAME, help=HELP)
        
        cmd_ls.add_argument(Args.ID,
                            help=Args.ID_HELP,
                            nargs=Args.ID_NARGS)
        
        cmd_ls.add_argument(Args.OPT_GROUPED,
                            action=Args.OPT_GROUPED_ACTION,
                            help=Args.OPT_GROUPED_HELP)
        
        cmd_ls.add_argument(Args.OPT_SORT,
                            help=Args.OPT_SORT)
        
        cmd_ls.set_defaults(func=execute)

def execute(args):
    issueIDs = _getFilteredListofIssueIDs(args)
    if issueIDs == None:
        print "Could not find issue: " + args.id
        return
    
    elif len(issueIDs) == 1:
        print IssueDisplayBuilder(issueIDs[0]).getFullIssueDisplay()
            
    else:
        columns = [display.COLUMNS['id'],
                   display.COLUMNS['status'],
                   display.COLUMNS['groups'],
                   display.COLUMNS['title'],
                   display.COLUMNS['mdate']]
        
        # We may have a lot of issues in the list that would make the output
        # run pretty long, therefore page it.
        PageOutputBeyondThisPoint()
        
        header = '  '.join([truncateOrPadStrToWidth(col.name, col.length) for col in columns])
        print header
        print '-' * len(header)        

        # Any sorting required?
        if args.sort != None:
            issueIDs = _sortIssues(issueIDs, args.sort)
            
        # Check to see if a default issue sort has been configured for this repository
        else:
            sort = getCmd('git config issue.ls.sort')
            if sort != None:
                issueIDs = _sortIssues(issueIDs, sort)

        # Group arg can be passed as parameter or via configured default
        if args.group or getCmd('git config issue.ls.group') == 'true':
            _displayGrouped(issueIDs, columns)        
        else:
            _displayUnGrouped(issueIDs, columns)

def _getFilteredListofIssueIDs(args):
    if args.id:
        issueId = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
        if issueId == None:
            # See if this is a group ID
            if group.exists(args.id):
                return Group(args.id).getIssueIds()
            else:
                return None
            
        return [issueId]
    
    else:
        return _getAllIssueIDs()

def _getAllIssueIDs():
    issueIDs = dircache.listdir(config.ISSUES_DIR)
    try:
        issueIDs.remove('.gitignore')
    except:    pass
    return issueIDs
            
def _sortIssues(issueIDs, sortBy):
    if sortBy == None:
        return None
    
    if sortBy == 'id':
        # We don't need to do anything here. Since the issues are stored with the id as the
        # filename, then they will be automatically sorted.
        return issueIDs
    
    issuesPathPrefix = config.ISSUES_DIR[len(config.GIT_ROOT) + 1:] # +1 to remove '/'
    issueSortTuple =[]
    
    if sortBy == 'title':
        for issueID in issueIDs:
            issueSortTuple.extend([[Issue(issueID).getTitle(), getFullIssueIdFromLeadingSubstr(issueID)]])
    
    elif sortBy == 'status':
        # Organize the issues into status groups
        for sk in config.STATUS_OPTS:
            issues = getCmd('git grep -n ^' + str(sk) + '$ -- ' + config.ISSUES_DIR)
            if issues != None:
                for i in issues.splitlines():
                    issueSortTuple.extend([[sk, i.split(':')[0][len(issuesPathPrefix) + 1:]]]) # +1 to remove '/'
    
    elif sortBy == 'date' or sortBy == 'cdate':
        for issueID in issueIDs:
            issueSortTuple.extend([[Issue(issueID).getCreatedDate(), getFullIssueIdFromLeadingSubstr(issueID)]])
            
    elif sortBy == 'mdate':
        for issueID in issueIDs:
            issueSortTuple.extend([[Issue(issueID).getModifiedDate(), getFullIssueIdFromLeadingSubstr(issueID)]])
            
    # Sort by Date
    issueSortTuple.sort(key=lambda issue: issue[0])
    
    if len(issueSortTuple) > 0:
        return map (lambda issueID: issueID[1], issueSortTuple)
    
    return None
        
def _displayUnGrouped(issueIDs, columns):
    for issueID in issueIDs:    
        print IssueDisplayBuilder(issueID).getOneLineStr(columns)

def _displayGrouped(issueIDs, columns):
    groups = group.getIssueIdsInGroups()

    grouped = {}
    ungrouped = []
    for issueID in issueIDs:
        isUngrouped = True
        for g in groups:
            if groups[g].count(issueID):
                isUngrouped = False
                if not grouped.has_key(g):
                    grouped[g] = []
                grouped[g].extend([issueID])
        if isUngrouped:
            ungrouped.extend([issueID])

    first = True
    for g in grouped:
        if first:    first = False
        else:        print ""

        print g
        for issueID in grouped[g]:
            sys.stdout.write(IssueDisplayBuilder(issueID).getOneLineStr(columns) + '\n')
    
    if len(ungrouped) > 0:
        if len(grouped) > 0: print ""
        print "ungrouped"
        for issueID in ungrouped: 
            print IssueDisplayBuilder(issueID).getOneLineStr(columns)

if (__name__ == "__main__"):
    execute()
