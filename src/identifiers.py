#! /usr/bin/env python

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