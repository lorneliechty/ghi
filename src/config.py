#! /usr/bin/env python

class _Module:
	'''This class provides a series of lazy-loaded properties that
	represent the general ghi config.'''
	@property
	def STATUS_OPTS(self):
		'''List of legal issue status values'''
		import config_file
		if not hasattr(self, '_STATUS_OPTS'):
			config = config_file.ConfigFile.read(self.GHI_DIR + '/config')
			self._STATUS_OPTS = config.statusOpts
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
	def GIT_EDITOR(self):
		'''Get the root directory for all ghi files'''
		from subprocess_helper import getCmd
		if not hasattr(self, '_GIT_EDITOR'):
			self._GIT_EDITOR = getCmd('git config core.editor')
		return self._GIT_EDITOR

# The same properties from above are listed here simply so that
# tab completions and auto-discovery features of Eclipse don't
# break due to the fact that we're swapping the module reference
# in the namespace at the bottom of this file
GIT_ROOT = _Module.GIT_ROOT
GHI_DIR = _Module.GHI_DIR
ISSUES_DIR = _Module.ISSUES_DIR

GIT_EDITOR = _Module.GIT_EDITOR

STATUS_OPTS = _Module.STATUS_OPTS

if not __name__ == "__main__":
	# This craziness makes all of our PROPERTIES in the _Module class
	# immediately usable for anyone that imports the config module.
	import sys
	sys.modules[__name__] = _Module()
