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

class _Module:
	'''This class provides a series of lazy-loaded properties that
	represent the general ghi config.'''
	@property
	def STATUS_OPTS(self):
		'''List of legal issue status values'''
		from subprocess_helper import getCmd
		if not hasattr(self, '_STATUS_OPTS'):
			# Set the default status options to be used in case no
			# config file is present (shouldn't happen, but whatevs)
			self._STATUS_OPTS = {0:'New',1:'In progress',2:'Fixed'}

			status_options = getCmd('git config '
									+ '-f ' + self.GHI_DIR + '/config '
									+ '--get-regexp status.s')

			if status_options != None:
				for status in status_options.split('\n'):
					key,sep,val = str(status).partition(' ')
					self._STATUS_OPTS[int(key.lstrip('status.s'))] = val
		
		return self._STATUS_OPTS
	
	@property
	def GIT_ROOT(self):
		'''Get the git top-level directory'''
		from subprocess_helper import getCmd
		if not hasattr(self, '_GIT_ROOT'):
			self._GIT_ROOT = getCmd('git rev-parse --show-toplevel')
		return self._GIT_ROOT
	
	@property
	def GHI_DIR(self):
		'''Get the root directory for all ghi files'''
		if not hasattr(self, '_GHI_ROOT'):
			self._GHI_ROOT = self.GIT_ROOT + '/.ghi' 
		return self._GHI_ROOT
	
	@property
	def ISSUES_DIR(self):
		'''Get the root directory for all ghi files'''
		if not hasattr(self, '_ISSUES_DIR'):
			self._ISSUES_DIR = self.GHI_DIR + '/issues' 
		return self._ISSUES_DIR
	
	@property
	def GROUPS_DIR(self):
		'''Get the root directory for all ghi issue groups'''
		if not hasattr(self, '_GROUPS_DIR'):
			self._GROUPS_DIR = self.GHI_DIR + '/groups' 
		return self._GROUPS_DIR
	
	@property
	def GIT_EDITOR(self):
		'''Get the root directory for all ghi files'''
		from subprocess_helper import getCmd
		if not hasattr(self, '_GIT_EDITOR'):
			self._GIT_EDITOR = getCmd('git config core.editor')
		return self._GIT_EDITOR

	def mkPathRel(self,path):
		return path.replace(self.GIT_ROOT + "/", "")
	

# The same properties from above are listed here simply so that
# tab completions and auto-discovery features of Eclipse don't
# break due to the fact that we're swapping the module reference
# in the namespace at the bottom of this file
GIT_ROOT = _Module.GIT_ROOT
GHI_DIR = _Module.GHI_DIR
ISSUES_DIR = _Module.ISSUES_DIR
GROUPS_DIR = _Module.GROUPS_DIR

GIT_EDITOR = _Module.GIT_EDITOR

STATUS_OPTS = _Module.STATUS_OPTS

mkPathRel = _Module.mkPathRel

if not __name__ == "__main__":
	# This craziness makes all of our PROPERTIES in the _Module class
	# immediately usable for anyone that imports the config module.
	import sys
	sys.modules[__name__] = _Module()
