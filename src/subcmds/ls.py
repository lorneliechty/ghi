#! /usr/bin/env python

import dircache
import config

NAME = "ls"
HELP = "List issues"

class Args:
    """Wrapper class that defines the command line args"""
    ID="id"
    ID_HELP="Issue ID"
    ID_NARGS="?"
    ID_DEFAULT="*"

def execute(args):
    for issue in dircache.listdir(config.ISSUES_DIR): 
        print issue

if (__name__ == "__main__"):
    execute()