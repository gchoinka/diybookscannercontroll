import subprocess
from subprocess import PIPE
import re
import json
import threading
from collections import deque
import sys
from time import sleep
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor


def enqueue_output(file, queue):
    for line in iter(file.readline, ''):
        queue.put(line)
    file.close()

class ThreadPipeReader(threading.Thread):
    def __init__(self, pipe, proc):
        super().__init__()
        self.queue:Queue[str] = Queue()
        self.pipe = pipe
        self.proc = proc
        self.retv = None

    def run(self):
        line = ""
        while ch := self.pipe.read(1):
            line += ch
            if re.match(r"con\s?\d*>", line):
                self.queue.put(str(line))
                line = ""
            if ch == "\n":
                self.queue.put(str(line))
                line = ""
            if retv := self.proc.poll() is not None:
                self.retv = retv
                break
        self.pipe.close()

        
class Cam:
    def __init__(self, busId, devId, serialId, dataDir, chdkptpBin):
        self.metainfo_dic = {}
        self.busId = busId
        self.devId = devId
        self.serialId = serialId
        self.chdkptpBin = chdkptpBin
        self.name = ""
        self.q_stdout = None
        self.q_stderr = None
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
        self.subp = subprocess.Popen(args, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True, bufsize=1)
        self.q_stdout = ThreadPipeReader(self.subp.stdout, self.subp)
        self.q_stderr = ThreadPipeReader(self.subp.stderr, self.subp)
        self.q_stdout.start()
        self.q_stderr.start()
        self.call(f"connect -b={str(self.busId)} -d={str(self.devId)}", wait=False)



    def getName(self):
        if "name" in self.metaInfo:
            return self.metaInfo["name"]
        else:
            return "unknown"
        
    def call(self, cmd:str, wait:bool=True):
        while True:
            try:
                out_line = self.q_stdout.queue.get_nowait()
                # print("flushing line " + out_line.strip())
            except Empty:
                break

        self.subp.stdin.write(cmd+"\n")
        self.subp.stdin.flush()
        while True and wait:
            try:
                line = self.q_stdout.queue.get_nowait()
                # print("got new line " + line.strip())
                if re.match(r"con\s?\d*>.*",  line):
                    break
            except Empty:
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
        
def getCams(dataDir, chdkptpBin):
    chdkptpOutput = subprocess.check_output([chdkptpBin, "-elist"])
    camList=[]
    for line in chdkptpOutput.split(b'\n'):
        devmatch = re.match(rb'^([-+]?\d+):(?P<name>.*) b=(?P<busId>\S*) d=(?P<devId>\S*) v=0x4a9 p=0x31ef s=(?P<serialId>\S*)', line)
        if devmatch is not None:
            g = devmatch.groupdict()
            camList.append(Cam(g["busId"].decode(), g["devId"].decode(), g["serialId"].decode(), dataDir, chdkptpBin))
    return camList
