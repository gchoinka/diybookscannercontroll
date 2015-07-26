#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import queue
import chdkptp
import pprint
import re
import threading 
import time
import sys
import tempfile 
import os
import errno
import code
import random
import time
import readline
from bottle import route, template
import bottle
from collections import deque

from datetime import date

keyQueue = queue.Queue()
outputQueue = queue.Queue()

def myPrint(message):
    sys.stdout.write(message)
    outputQueue.put(message)
    
chdkptpBin=os.path.expandvars("$HOME")+"/opt/chdkptp/chdkptp.sh"

diybookscanercontrol_dirs = {
        "scriptdir":os.path.dirname(os.path.abspath(__file__)), 
        "logdir":os.path.dirname(os.path.abspath(__file__))+"/log",
        "bookdir":os.path.expandvars("$HOME")+"/book/",
        "tmp_nospaces":"/tmp",
        "luadir":os.path.dirname(os.path.abspath(__file__))+"/lua",
        "datadir":os.path.dirname(os.path.abspath(__file__))+"/../datadir"
}

imagenumber = 0
bookname  = "noname"

@route('/press/<key>')
def press(key):
    global keyQueue
    global bookname
    global imagenumber
    keyQueue.put(key)
    return u"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<OK />"""

@route('/book/<name>')
def press(name):
    global keyQueue
    global bookname
    global imagenumber
    bookname = name
    keyQueue.put("1")
    keyQueue.put("8")
    return u"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<OK />"""

@route('/number/<num>')
def press(num):
    global keyQueue
    global bookname
    global imagenumber
    imagenumber = int(num)
    keyQueue.put("1")
    keyQueue.put("4")
    return u"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<OK />"""

@route('/')
def index():
    return \
u"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>RestTrigger DIYBOOKSCANER</title>
<script type="text/javascript">
function send (key) {
    xmlhttp=new XMLHttpRequest(); 
    xmlhttp.open("GET","press/"+key,true); 
    xmlhttp.send(); 
    return false;
}

function sendto (des, message) {
    xmlhttp=new XMLHttpRequest(); 
    xmlhttp.open("GET", des + "/" + message, true); 
    xmlhttp.send(); 
    return false;
}
</script>
<style type="text/css">
body, html { height: 100%; width: 100%; margin:0; padding: 0;}
input[type="button"] { height: 100%; width: 100%; margin:0; padding: 0; background-color:none; }
input[type="button"]:active { height: 100%; width: 100%; margin:0; padding: 0; background-color:#ff0000; }
table { height: 100%; width: 100%; margin:0; padding: 0; }
tr, td {  margin:0; padding: 0; /* width: 100%; height:50% */}
</style>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
</head>
<body>
<table id="table1">
<tr>
    <td>
        <table>
        <tr>
        <td>
        name:
        </td>
        <td>
        <input name="bookInput" type="text" maxlength="512" id="bookInput" />
        </td>
        <td>
        <input type="button" onclick="sendto('book', document.getElementById('bookInput').value)" value="send" />
        </td>
        </tr>
        <tr>
        <td>
        number:
        </td>
        <td>
        <input name="numberInput" type="text" maxlength="512" id="numberInput" />
        </td>
        <td>
        <input type="button" onclick="sendto('number', document.getElementById('numberInput').value)" value="send" />
        </td>
        </tr>
        </table>
    <td>
        <table>
        <tr>
            <td><input type="button" onclick="send('u')" value="L-Shoot" /></td><td><input type="button" onclick="send('m')" value="R-Shoot" /></td>
        </tr>
        <tr>
            <td><input type="button" onclick="send('j')" value="A4-Shoot" /></td><td><input type="button" onclick="send('y')" value="Undo" /></td>
        </tr>    
        </table>
    </td>
    <td><input type="button" onclick="send('k')" value="L-R-Shoot" /></td>
</tr>
<tr>
    <td colspan="3">        
        <table>
        <tr>
            <td><input type="button" onclick="send('0')" value="0" /></td>
            <td><input type="button" onclick="send('1')" value="1" /></td>
            <td><input type="button" onclick="send('2')" value="2" /></td>
            <td><input type="button" onclick="send('3')" value="3" /></td>
            <td><input type="button" onclick="send('4')" value="4" /></td>
            
        </tr>
        <tr>
            <td><input type="button" onclick="send('5')" value="5" /></td>
            <td><input type="button" onclick="send('6')" value="6" /></td>
            <td><input type="button" onclick="send('7')" value="7" /></td>
            <td><input type="button" onclick="send('8')" value="8" /></td>
            <td><input type="button" onclick="send('9')" value="9" /></td>
        </tr>    
        </table>
    </td>
</tr>
</table>
</body>
</html> 
"""

class WebThread(threading.Thread): 
    def run(self): 
        bottle.run(host='0.0.0.0', port=8080, quiet=True)
        

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

class Enumerate(object):
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            
class ShootThread(threading.Thread): 
    def __init__(self, cam, filename): 
        threading.Thread.__init__(self) 
        self.cam = cam
        self.filename = filename
        
    def run(self): 
        print(self.filename)
        self.cam.call("remoteshoot %s"%(self.filename))        

class WaitThread(threading.Thread): 
    def __init__(self, secs): 
        threading.Thread.__init__(self) 
        self.secs = secs
        
    def run(self): 
        time.sleep(self.secs)      



def pullKey():
    key = keyQueue.get() 
    print(key)
    outputQueue.put(key)
    keyQueue.task_done()
    return key


def wait_for_keypress(message=""):
    myPrint(message+"press any key\n")
    return pullKey()


cams = chdkptp.getCams(diybookscanercontrol_dirs["datadir"], chdkptpBin)

if len(cams) != 3:
    myPrint("need 3 cams! going to exit\n")
    #exit()
           


postfix="raw/image%%04d%%s"
easy_imagepattern = "%s/%%s/%s"%(diybookscanercontrol_dirs["bookdir"],postfix)
imagepattern = easy_imagepattern % "noname"



camsDict = {}
for i in range(0,len(cams)):
    c=cams[i]
    
    c.loadMetaInfo();
    c.call("rec")            
    c.call("lua exit_alt()\n")
    c.call("luar set_prop(143,2)\n") # flash off
    c.call("luar set_prop(5,0)\n") # af light off
    
    zoom_val = 0;
    if "zoom" in c.metaInfo:
        zoom_val =  c.metaInfo["zoom"]
       
    c.setZoom(zoom_val)
    
    camsDict[c.getName()] = c
    


wt = WebThread()
wt.daemon = True
wt.start()
wait_for_keypress("AFL ")    
keyQueue.put("1")
keyQueue.put("3")
keyQueue.put("k")

keyQueue.put("1")
keyQueue.put("8")

lastnumber=0



doQuit=False
while not doQuit:    
    myPrint("\n 1:setup 0:quit %04d (%s)>>" % (imagenumber, bookname))
    key = pullKey()
    
    workcams = []

    if key == 'y':
        imagenumber = lastnumber
        continue
             
    if key == 'k':
        workcams.append(camsDict["rig"])
        workcams.append(camsDict["lef"])
        #pygame.mixer.music.play()
               
    if key == 'u':
        wait_for_keypress()
        workcams.append(camsDict["lef"])
        
    if key == 'm':
        wait_for_keypress()
        workcams.append(camsDict["rig"])

    if key == 'j':
        wait_for_keypress()
        workcams.append(camsDict["a4h"])
                    
    
    if key == '1':
        myPrint("\n")        
        myPrint("3: AFL\n")
        myPrint("5: zoom\n")
        myPrint("6: shutdown cams\n")
        myPrint("8: new book\n")
        myPrint("0: exit\n")
        choosed = pullKey()
        
        if choosed == '8' :
            imagepattern = easy_imagepattern % bookname
            mkdir_p(os.path.dirname(imagepattern))
        elif choosed == '4':
            pass
            #imagenumber = int(rlinput("number >>\n", "0"))
        elif choosed == '3':
            wait_for_keypress()
            for c in cams:
                c.call("""lua click("shoot_half")""")
            time.sleep(2)
            for c in cams:
                c.call("lua set_aflock(1)")
        elif choosed == '5':
            myPrint("1 zoom in | 3 zoom out | 0 exit \n")
            for c in cams:
                myPrint("cam %s\n" % c.getName())
                while True:
                    key = pullKey()
                    if key == '0':
                        break
                    
                    zoom_val =  c.metaInfo["zoom"]
                    if key == "3":
                        zoom_val = zoom_val - 1;
                    if key == "1":
                        zoom_val = zoom_val + 1;
                    c.setZoom(zoom_val)
                    myPrint(zoom_val)
                   
        elif choosed == '6':
            for c in cams:
                c.call("shutdown")

    if len(workcams) > 0:
        lastnumber = imagenumber 
        st = []
        for c in workcams:
            st.append(ShootThread(c,  imagepattern%(imagenumber, c.getName())))
            imagenumber+=1
        for t in st: t.start()
        for t in st: t.join()

    if key == '0':
        myPrint("Do you realy wont to Quit?(1/0)\n")
        if pullKey() == "1":
            doQuit = True
            for c in cams:
                c.call("quit")



    
    

    
#TODO:
#   weißabgleich und iso einstellen
#   AFL speichern
#   cam crash detect
#   aufwachen vor den zoom
#   logging
#   image vieer
#   sec einstellbar
#   call wait


# bsw_run
# left und right bilder am anfang und am ende / bilderdurchgehen
# logging (dauer, status)
# zoom
# copy to hdd / backup
