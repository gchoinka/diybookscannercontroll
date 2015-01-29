#!/usr/bin/python3.3

import subprocess
from subprocess import PIPE
import re
import json
import threading
from collections import deque
import sys


class PipeReadThread(threading.Thread): 
    def __init__(self, pipe): 
        threading.Thread.__init__(self) 
        self.pipe = pipe
        self.lineNum = 0
        self.goOn = True
        
    def run(self): 
        while self.goOn:
            ch = self.pipe.read(1)
            if ch == b'>':
                self.lineNum = self.lineNum + 1
            if ch == b'':
                break
        self.lineNum = self.lineNum + 1


class Cam:
    def __init__(self, busId, devId, serialId, dataDir, chdkptpBin):
        self.metainfo_dic = {}
        self.busId = busId
        self.devId = devId
        self.serialId = serialId;
        self.chdkptpBin = chdkptpBin
        self.name = ""
        self.pipeReader = None
        self._connect()
        self.metaInfo = {}
        self.dataDir = dataDir;

    def _connect(self):
        args = [self.chdkptpBin,  "-i"]
        self.subp = subprocess.Popen(args, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=0)
        self.pipeReader = PipeReadThread(self.subp.stdout)
        self.pipeReader.start()
        self.call("connect -b="+str(self.busId)+" -d="+str(self.devId)+"")

    def getName(self):
        if "name" in self.metaInfo:
            return self.metaInfo["name"]
        else:
            return "unknown"
        
    def call(self, cmd):
        currentLine = self.pipeReader.lineNum;        
        self.subp.stdin.write(bytes(cmd+"\n", 'ascii'))
        self.subp.stdin.flush()
        while currentLine == self.pipeReader.lineNum:
            pass
   
    def loadMetaInfo(self):
        fromFile = self._loadMetaInfo(self.dataDir)
        for (key,value) in fromFile.items():
            self.metaInfo[key] = value
        self._storMetaInfo(self.dataDir, self.metaInfo)

    def storMetaInfo(self):
        fromFile = self._loadMetaInfo(self.dataDir)       
        for (key,value) in self.metaInfo.items():
            fromFile[key] = value             
        self._storMetaInfo(self.dataDir, fromFile)

    def _loadMetaInfo(self, dataDir):
        filename = self._genFilename( dataDir )
        try:
            return json.loads(open(filename).read())
        except IOError:
            return json.loads("{}")
        
    def _storMetaInfo(self, dataDir, metaInfoDict):
        filename = self._genFilename( dataDir )
        open(filename, "w").write(json.dumps(metaInfoDict, sort_keys=True, indent=4, separators=(',', ': ')))
        
    def _genFilename(self, dataDir):
        return dataDir + "/cam_"+self.serialId+".js";
    
    def setZoom(self, zoom):
        self.call("lua set_zoom( "+str(zoom)+" )\n")
        self.metaInfo["zoom"] = zoom
        self.storMetaInfo()
        

#-1:Canon PowerShot A495 b=001 d=031 v=0x4a9 p=0x31ef s=12385D16CC5C440E81B45F05F73B6D50
def getCams(dataDir, chdkptpBin):
    chdkptpOutput = subprocess.check_output([chdkptpBin, "-elist"])
    devmatch = re.findall(b'^(.*?):Canon PowerShot A49[05] b=([0-9]{3}) d=([0-9]{3}) v=([^ ]*) p=([^ ]*) s=(\S*)$', chdkptpOutput, re.MULTILINE)
    camList=[]
    for (num, busId,devId, vtmp, ptmp, serialId) in devmatch:
        camList.append(Cam(busId.decode(), devId.decode(), serialId.decode(), dataDir, chdkptpBin))
    return camList