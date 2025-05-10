import subprocess
from subprocess import PIPE
import re
import json
import threading
from collections import deque
import sys
from time import sleep


class Cam:
    def __init__(self, busId, devId, serialId, dataDir, chdkptpBin):
        self.metainfo_dic = {}
        self.busId = busId
        self.devId = devId
        self.serialId = serialId
        self.chdkptpBin = chdkptpBin
        self.name = ""
        self.pipeReader = None
        self._connect()
        self.metaInfo = {}
        self.dataDir = dataDir

    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.subp.kill()
        self.subp.wait(2)

    def _connect(self):
        args = [self.chdkptpBin, "-i"]
        self.subp = subprocess.Popen(args, shell=False, stdin=PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=0)
        # self.pipeReader = PipeReadThread(self.subp, self.subp.stdout)
        # self.pipeReader.start()
        self.call(f"connect -s={self.serialId}")


    def getName(self):
        if "name" in self.metaInfo:
            return self.metaInfo["name"]
        else:
            return "unknown"
        
    def call(self, cmd):
        print(cmd)
        self.subp.stdin.write(bytes(cmd+"\r\n", 'ascii'))
        self.subp.stdin.flush()

   
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
    camList=[]
    for line in chdkptpOutput.split(b'\n'):
        devmatch = re.match(rb'^([-+]?\d+):(?P<name>.*) b=(?P<busId>\S*) d=(?P<devId>\S*) v=0x4a9 p=0x31ef s=(?P<serialId>\S*)', line)
        if devmatch is not None:
            g = devmatch.groupdict()
            camList.append(Cam(g["busId"].decode(), g["devId"].decode(), g["serialId"].decode(), dataDir, chdkptpBin))
    return camList