#! /usr/bin/env python

import subprocess

# Get the git top-level directory
GIT_ROOT = subprocess.Popen(
    'git rev-parse --show-toplevel',
    shell=True,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    close_fds=True).stdout.read().strip()

GHI_DIR = GIT_ROOT + '/.ghi'
ISSUES_DIR = GHI_DIR + '/issues'


class Config:
    statusOpts = { }

class ConfigFile:
	STATUS = "status"
	BLOCK_STATUS = "[" + STATUS  + "]"

	@staticmethod
	def write(filepath, config):
		my = ConfigFile
		with open(filepath, 'wb') as f:
			
			f.write(my.BLOCK_STATUS + '\n');
			for k, v in config.statusOpts.iteritems():
				f.write('\t{} = {}\n'.format(k,v))

		f.closed
		return

	@staticmethod
	def read(filepath):
		my = ConfigFile
		config = Config()
		with open(filepath, 'rb') as f:
			lines = f.readlines()

			marks = {};
			for i, line in enumerate(lines):
				if line.rstrip() == my.BLOCK_STATUS:
					marks[my.STATUS] = i
			
			for line in lines[marks[my.STATUS] + 1:]:
				key, val = line.strip().split('=')
				config.statusOpts[int(key.strip())] = val.strip()

		f.closed
		return config

def test():
	startConfig = Config()
	startConfig.statusOpts = {0: 'New', 1: 'In Progress', 2: 'Fixed'}
	print startConfig.statusOpts
	ConfigFile.write("/Users/lorne/dev/personal/ghi/src/test",startConfig)
	endConfig = ConfigFile.read("/Users/lorne/dev/personal/ghi/src/test")
	print endConfig.statusOpts

if __name__ == "__main__":
	import sys
	test()
