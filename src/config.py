#! /usr/bin/env python

class Config:
    statusOpts = {  0: 'New', 
                    1: 'In Progress', 
                    2: 'Fixed' }

def writeConfigToFile(filepath, config):
    with open(filepath, 'wb') as f:
        
        f.write('[status]\n');
        for k, v in config.statusOpts.iteritems():
            f.write('\t{} = {}\n'.format(k,v))

    f.closed
    return

def readConfigFromFile(filepath):
    config = Config()

    with open(filepath, 'rb') as f:
        lines = f.readlines()

        marks = {};
        for i, line in enumerate(lines):
            if line.rstrip() == '[status]':
                marks['status'] = i
        
        for line in lines[marks['status']+1:]:
            key, val = line.strip().split('=')
            config.statusOpts[int(key.strip())] = val.strip()

    f.closed

    return config

if __name__ == "__main__":
    import sys
    startConfig = Config()
    print startConfig.statusOpts
    writeConfigToFile("/Users/lorne/dev/personal/ghi/src/test",startConfig)
    endConfig = readConfigFromFile("/Users/lorne/dev/personal/ghi/src/test")
    print endConfig.statusOpts
