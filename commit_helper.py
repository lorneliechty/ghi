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

from subprocess_helper import getCmd, runCmd
import config
import inspect

def _getCallerModuleName():
	''''Get the name of the calling subcommand
	For more info on the basic idea see: http://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
	
	From the above, we're additionally grabbing the lowest level
	module name in the event that the command module was imported
	as part of a package (which is the case with our subcmds)'''
	
	# Note, we use a [2] to get the caller's caller here because
	# we assume that _getCallerModuleName is being called only
	# from a method within this module
	return inspect.getmodule((inspect.stack()[2])[0]
					).__name__.split('.')[-1]

def _stashWc():
	# Adding an issue includes adding a new commit to the repository.
	# To make sure that our commit doesn't include anything other
	# than this issue, clean the working copy using git-stash
	getCmd("git stash --all")

def _restoreWc():
	# Now restore the working copy
	getCmd("git stash pop")
	
def prepForCommit():
	_stashWc()
	
def commit(msg = None):
	if msg:
		getCmd('git commit -m "' + msg + '"')
	else:
		runCmd('git commit')
	
def addToIndex(path):
	getCmd("git add " + path)

def remove(path, force=False):
	if force:
		getCmd("git rm -f " + path)
	else:
		getCmd("git rm " + path)

def cleanWcAndCommitGhiDir(msg):
	'''Cleans the git working copy and creates a git commit for the
	whole .ghi directory'''
	
	_stashWc()
	
	getCmd("git add " + config.GHI_DIR)
	
	cmdName = _getCallerModuleName()
	print getCmd('git commit -m "ghi-' + cmdName + ' ' + msg + '"')
	
	_restoreWc()
