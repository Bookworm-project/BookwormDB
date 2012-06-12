#!/usr/bin/python
import subprocess
import sys
import time
from subprocess import Popen,list2cmdline,PIPE

#This file downloads a list of ocaids, in parallel.

filelist = open("../../Downloads/Catinfo/cleaned/catalog.txt")

def exec_commands(cmds):
    ''' Exec commands in parallel in multiple process                                   
    (as much as we have CPU) (This is code from stack overflow that Ryan Lee cleaned up for us) 
    '''
    if not cmds: return # empty list                                
    def done(p):
        return p.poll() is not None
    def success(p):
        return p.returncode == 0
    def fail():
        print "ERROR OF SOME SORT!!!"
    max_task = 20
    processes = []
    while True:
        while cmds and len(processes) < max_task:
            task = cmds.pop()
            #print list2cmdline(task)
            processes.append(Popen(task, stdout=PIPE))
        for p in processes:
            if done(p):
                if success(p):
                    processes.remove(p)
                else:
                    processes.remove(p)
                    fail()
        if not processes and not cmds:
            break
        else:
            time.sleep(0.05)

max_task = 12
cmds = []

for line in filelist:
    ocaid = line.split("\t")[1]
    print ocaid
    #if the file exists, we don't need to download it.
    try:
        open("../../raw/" + ocaid + ".txt")
    except:
        cmds.append(['curl','-L', '-o', "../../raw/" + ocaid + ".txt", "http://archive.org/download/" + ocaid + "/" + ocaid + "_djvu.txt"])
    if len(cmds) >= 10000:
        #This is slightly inefficient, but not so bad--the 10,000 commands are processed, 12 at a time, until they're all done:
        #Then it clears the list, and moves on again to building it up.
        exec_commands(cmds)
        cmds=[]

#And once at the end, since less than a thousand will be there...
exec_commands(cmds)



