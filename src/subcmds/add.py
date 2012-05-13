#! /usr/bin/env python

import issue

NAME="add"
HELP="Add a new issue"

class Args:
    """Wrapper class that defines the command line args"""
    TITLE="title"
    TITLE_HELP="One line issue title"
    
    OPT_DESCRIPTION="--description"
    OPT_DESCRIPTION_SHORT="-d"
    OPT_DESCRIPTION_HELP="Description"

def execute(args):
    
    # First validate arguments
    
    # Create new issue
    newIssue = issue.Issue();
    
    # Set title
#    if (args.)