#!/usr/bin/python3
################################################################################
#  PatchRegression
#  By Tommy Castilleja
#
#
#  This script is to automatically perform Patch regressions
#   1. Remove old patches stitched in BIOS and stitches new patch
#   2. Copies ucode and stitched bios to share drive called out in ini file
#   3. Stitches knobs of each software config and moves to correct share drive 
#   4. Flash BIOS per software config specified or from swconfig in env var
#   5. Unlocks station after it has reached F5 or F6   
#
################################################################################

from __future__ import print_function
from __future__ import absolute_import
import argparse
import os, sys, re
os.system("")
from os import path
import time
from datetime import datetime, timedelta
import subprocess
time.sleep(.5)
import glob
import logging
import progressbar
import socket
import pdb


import configparser
config = configparser.ConfigParser()
print(os.path.realpath(sys.argv[0]))
script_path = os.path.realpath(sys.argv[0])
ini_path = '%s\\patch_regression.ini' % '\\'.join(script_path.split('\\')[0:-1])
config.read(ini_path)

if r'C:\SVSHARE\User_Apps\TTK2' not in sys.path: sys.path.append(r"C:\SVSHARE\User_Apps\TTK2")
if r'C:\SVSHARE\User_Apps\TTK2\API\Python\Examples' not in sys.path: sys.path.append(r"C:\SVSHARE\User_Apps\TTK2\API\Python\Examples")
if r'C:\SVSHARE\User_Apps\TTK2\API\Python' not in sys.path: sys.path.append(r"C:\SVSHARE\User_Apps\TTK2\API\Python")

from TTK2_ConfigManager import *
from TTK2_Port_80 import *

import shutil
from pathlib import Path as p

try:
    import pysvtools.xmlcli.XmlCli as cli
except:
    plog('error','Could not import XmlCli')

#List of local variables to be used throughout script
class Variables:
    cpuid = ''
    project = ''
    patch = ''
    step = ''
    mode = ''
    cli_bios_path = ''
    cpustep = ''
    fullpatchname = ''
    ver = ''
    ulockCheck = ''
    pMsg = True
    products = ['CLX','SKX']
    pathToSaveLog = ''
    log_file = ''
    finalBios = ''
    updatedBIOS = ''
    destBiospath = ''
    allTags = []
    changemade = False
    error = False

    
vars = Variables()


def listBins():
    # this will list all binaries in a directory
   
    fullPth = None
    fle = os.listdir(vars.cli_bios_path)
    for x in fle:
        if x.endswith('.bin'):
            fullPth = (vars.cli_bios_path +'\\'+ x)
    if fullPth == None:
        return(args.bios)
    else:
        return(fullPth)


def swconfigToBiosCheck():
    swconfigMatch = False

    swconfigs = args.swconfigs.replace('/','\\')
    if '.ini' in os.path.split(swconfigs)[1]:
        iniFile = open(swconfigs, 'r')
    else:
        iniFilename = os.listdir(args.swconfigs)[1]
        f = '%s\\%s' % (swconfigs, iniFilename)
        iniFile = open(f, 'r')
        
    plog('info','Check if swconfig used is correct for BIOS')
    lines = iniFile.readlines()
    
    for line in lines:
        if vars.project in line:
            swconfigMatch = True
            break
    
    return(swconfigMatch)


def buildDestPath():
    an_knobstitch_path = config['AN_KNOBSTITCH_PATH']
    biosOutdir = an_knobstitch_path['biosOutdir']
    biosOutdir = biosOutdir.replace('/','\\')
    
    if args.ucode == None:
        fileToUse = args.bios
    else:
        fileToUse = args.ucode

    
    patchname = ''
    patchnamex = ''

    fullFileName = os.path.split(fileToUse)[1]
    
    try:
        patchname = re.search("([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", fullFileName).group()
    except:
        pass
    try:
        patchnamex = re.search("([a-zA-Z]{1})_([0-9]{2})_([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", fullFileName).group()
    except:
        pass
    try:
        vars.cpuid = re.search("([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", fullFileName).group().split('_')[0]
    except:
        plog('warn','No CPUID detected')
    try:
        vars.patch = re.search("([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", fullFileName).group().split('_')[1]
    except:
        plog('warn','No Patch detected')
    
    
    allprojects = config['PROJECTS']
    
    if vars.patch == '' or vars.cpuid == '':
        #BIOS does not have cpuid, patch, or swconfigs in bios name. Using the raw bios path as destination path
        plog('warn','BIOS did not have search parameters in name\nDestination path will be same as BIOS source path')
        vars.destBiospath = os.path.split(args.bios)[0]
        
    else: 
        #BIOS has cpuid and patch in name. Continue to build destination path
        vars.project, vars.step = allprojects[vars.cpuid].split('_')[0], allprojects[vars.cpuid].split('_')[1]
        vars.cpustep = '%s_%s' % (vars.cpuid, vars.step)
        
        if int(vars.patch,16) & int('0x80000000',16) != 0:
            vars.mode = 'Debug'
        else:
            vars.mode = 'Baseline'
       
        if patchnamex == '':
            fullpatchname = patchname
        else:
            fullpatchname = patchnamex
            
        vars.destBiospath = '%s\%s\%s\%s\%s' % (biosOutdir, vars.project, vars.cpustep, vars.mode, fullpatchname)
        
        if os.path.isdir(vars.destBiospath) == False:
            os.makedirs(vars.destBiospath)
                  
    
def checkBinExist():
    
    taglist = config['TAGLIST']
    tags = taglist['tags']
    tags = tags.split(',')
    BiosMatchesTags = None
    
    buildDestPath()

    baseName = ''
    list_of_files = glob.glob('%s\\*' % vars.destBiospath)

    if args.swconfigs == None:
        fullpatchname = os.path.split(args.ucode)[1]
        for file in list_of_files:
            if fullpatchname in file:
                try:
                    baseName = re.search("([A-Za-z]{4})([0-9]{1})", CopiedOrgBios).group()
                except:
                    BiosMatchesTags = file
            
    else:
        listOftagsInSwConfig = []
        for t in tags:
            if t in os.path.split(args.swconfigs)[1]:
                listOftagsInSwConfig.append(t)

        task = listOftagsInSwConfig

        for file in list_of_files:
            listOftagsInBios = []
            for t in tags:
                if t in os.path.split(file)[1]:
                    listOftagsInBios.append(t)
                    
            if len(listOftagsInSwConfig) == len(listOftagsInBios):
                # if len(task) >= 1:
                x = 0
                for t in task:
                    if t in file:
                        x += 1
                        if x == len(task):
                            BiosMatchesTags = file
                        
    return(BiosMatchesTags)
    
    
def call_flasher(bios):

    an_paths = config['AN_PATHS']
    flasher = '%s\\BiosPackage.py' % an_paths['BiosPackage_Path']
    flasher = flasher.replace('/','\\')

    try:
        secHeader('BIOS Flash')
        plog('info','flash command: ' + flasher + ' -b ' + bios)
        vars.finalBios = bios
        vars.changemade = True

        os.system(flasher + ' -b ' + bios)
        secFooter('BIOS Flash')
        vars.finalBios = bios
        
        
        process = subprocess.Popen(flasher + ' -b ' + bios, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = process.communicate()[0]
        exitCode = process.returncode
        modoutput = str(output).split('\\r\\n')
        for idx in modoutput:
            logger.info(idx)
            if idx == 'Finished Successfully':
                secFooter('Stitching')
                
                
    except:
        plog('error', 'Error with flashing BIOS')
        vars.ulockCheck = False


def knobandstitch(): 
    
    #Check if Binary exists per software config
    BiosMatchesTags = checkBinExist()
    #if using Raw BIOS to stitch then SwConfig Check will be skipped
    if vars.destBiospath == os.path.split(args.bios)[0]:
        plog('warn','Raw BIOS will be stitched')
        match = True
        
    else:
        
        if args.swconfigs != None:
            #Check if swconfig is correct for BIOS
            secHeader('Checking SwConfig for BIOS')
            match = swconfigToBiosCheck()       
            secFooter('SwConfig Check')
        else:
            match = True
        
       
    if match == True:
        
        if BiosMatchesTags == None:
            if args.ucode == None:
                patch = ''
            else:
                patch = args.ucode
            if args.swconfigs == None:
                swconfigs = ''
            else:
                swconfigs = args.swconfigs
            
            call_ifwistitcher(bios = args.bios, patch = patch, swconfigs = swconfigs, destPath = vars.destBiospath)
                  
        else:
            plog('warn','Binaries already exists: %s\nIfwistitcher will be skipped' % BiosMatchesTags)
    else:
        plog('warn','SwConfig does not match BIOS')
                 
               
def call_ifwistitcher( bios = '', patch = '', swconfigs = '', destPath = '' ):

    an_knobstitch_path = config['AN_KNOBSTITCH_PATH']
    # stitcher_path = an_knobstitch_path['stitcher_path']
    stitcher_path = os.getcwd()
    # stitcher = '%s\\ifwistitcher.py' % stitcher_path.replace('/','\\')
    stitcher = '%s\script\ifwistitcher.py' % stitcher_path
    import subprocess
   
    command1 = [stitcher, bios, patch, swconfigs, destPath]
    
    try:
        strippedCommand1 = [x for x in command1 if x != '']
    except:
        strippedCommand1 = command1
    

    stitcher_mode = ''
    if patch != '' and swconfigs != '':
        stitcher_mode = '-op KnobandPatchChange'
    elif patch != '' and swconfigs == '':
        stitcher_mode = '-op PatchChange'
    else:
        stitcher_mode = '-op KnobChange'
    
    cmd =  ['python', stitcher, stitcher_mode, '-m Offline' , '-b %s' % bios]
    
    if patch != '':
        patch = '-p ' + patch
        cmd.append(patch)
    if swconfigs != '':
        cmd.append('-ki ' + swconfigs)
    
    destPath = destPath.replace('/','\\')
    cmd.append('-o ' + destPath)
    cmd = ' '.join(cmd)
    
    try:
                              
        secHeader('IfwiStitcher')
        plog('info','%s\n' % cmd)
        
        process = subprocess.Popen('%s\n' % cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = process.communicate()[0]
        exitCode = process.returncode
        modoutput = str(output).split('\\r\\n')
        for idx in modoutput:
            logger.info(idx)
            if idx == 'Finished Successfully':
                secFooter('Stitching')

        newlist_of_files = glob.glob('%s\\*' % destPath)
        latest_file = max(newlist_of_files, key=os.path.getctime)
        vars.finalBios = latest_file
        vars.changemade = True
    except:
        plog('error','Failed ifwistitcher')


def checkTask():

    conf = ''
    tasks = config['TASKLIST']
    tasklist = tasks['tasks']
    tags = config['TAGLIST']
    tlist = tags['tags']
    taglist = tlist.split(',')
    

    if args.task == None:
        #Using Base and tags from Zordon
        plog('notify','No SwConfig (task) specified\nUsing tags from Zordon')
        task = []
        swc = os.environ['SWConfig']
        task.append(swc.upper())
        tagL = os.environ['Tags']
        tgs = tagL.split(';')

        for tg in tgs:
            if tg in taglist:
                task.append(tg.upper())
        vars.allTags = task
        tsk = task.copy()

        for t in tsk:
            if t in tasklist:
                plog('notify','Zordon SwConfig: %s' % t)
                # vars.allTags.append(t)
                # conf = t
                tsk.remove(t)
        if tsk != '':
            plog('notify','Zordon Tags are: %s' % tsk)
            # vars.allTags.append(tsk)
            
    elif args.task == '': 
        #Using Base and tags from SwConfig ini file provided. This option muse be an ini file
        plog('notify','No SwConfig (task) specified\nUsing tags from SwConfig file provided')
        
        task = []

        if args.swconfigs != None and args.swconfigs != '':
            if '.ini' in args.swconfigs:
        
                for tg in taglist:
                    if tg in args.swconfigs:
                        task.append(tg.upper())
                vars.allTags = task
                tsk = task.copy()

                for t in tsk:
                    if t in tasklist:
                        plog('notify','SwConfig File has SwConfig : %s' % t)
                        # allTags.append(t)
                        # conf = t
                        tsk.remove(t)
                if tsk != '':
                    plog('notify','SwConfig File Tags are: %s' % tsk)
                    # vars.allTags.append(tsk)
            else:
                plog('warn','SwConfig must be an ini file to use this option')
            
        else:
            plog('warn','SwConfig file needed for this option')
            
        
    else:
        #Using Base and tags provided by user in GUI
        plog('notify','SwConfig (task) specified\nUsing tags specified by user')
        task = args.task.upper().strip()
        if ' ' in task:
            task = task.replace(' ','')
        # tasklist = dict(config.items('TASKLIST')).keys()
        if ',' in task:
            vars.allTags = task.split(',')
            tsk = task.split(',')
            for t in tsk:
                if t in tasklist:
                    plog('notify','User is requesting SwConfig: %s' % t)
                    # vars.allTags.append(t)
                    conf = t
                    tsk.remove(conf)
            if tsk != '':
                plog('notify','Tags are: %s' % tsk)
                # vars.allTags.append(tsk)
        elif task in tasklist:
            for t in tasklist:
                if t == task:
                    plog('notify','User is requesting SwConfig: %s' % t)
                    # vars.allTags.append(t)
        else:
            plog('error','User requested SwConfig is not in tasklist section of patch_regression.ini')


def setupSnapshot():
    import socket
    logger.info('####################################')
    logger.info('##### Patch Regression Snapshot #####')
    logger.info('####################################')
    plog('notify', 'Hostname: %s' % socket.gethostname())
    plog('notify', 'Full Bios Path: %s' % args.bios)
    plog('notify', 'Full Ucode Path: %s' % args.ucode)
    
    if args.swconfigs != None:
        plog('notify','SwConfig Path: %s' % args.swconfigs)
    
    if args.log == None:
        an_paths = config['AN_PATHS']
        list_of_files = glob.glob('%s/*' % os.path.split(an_paths['log_file'])[0])
        vars.log_file = max(list_of_files, key=os.path.getctime)
    else:
        if '"' in args.log:
            args.log = args.log.replace('"','')
        vars.log_file = args.log
    plog('notify','Log File: %s' % vars.log_file)
    
    
    if args.task != None:
        plog('notify','SwConfig to Flash: %s' % args.task)  
        
    if args.flash != True:
        plog('notify','Flash BIOS disabled')
    else:
        plog('notify','Flash BIOS enabled')
        
    if args.hton != True:
        plog('notify','HTON disabled')
    else:
        plog('notify','HTON enabled')
        
    if args.htoff != True:
        plog('notify','HTOFF disabled')
    else:
        plog('notify','HTOFF enabled')
        
        
    if args.unlock != True:
        plog('notify','Unlock System After Boot disabled')
    else:
        plog('notify','Unlock System After Boot enabled')
        
    secFooter('PatchRegression Snapshot') 
      
    
def CopyOrgBios():
    
    plog('info','Checking if original BIOS had previously been copied')
    BinPathForOrgBios = '%s\RawBios' % os.path.split(vars.pathToSaveLog)[0]
    if os.path.isdir(BinPathForOrgBios) == False:
        os.makedirs(BinPathForOrgBios)
    else:
        plog('warn','RawBios path exists.\nNo need to create directory')
    OrgBiosName = os.path.split(args.bios)[1]
    CopiedOrgBios = '%s\%s' % (BinPathForOrgBios, OrgBiosName)
    if os.path.isfile(CopiedOrgBios) == False: 
        patchname, cpid, pname, baseName = '','','',''
        try:
            patchname = re.search("([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", CopiedOrgBios).group()
        except:
            pass
        try:
            cpid = re.search("([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", CopiedOrgBios).group().split('_')[0]
        except:
            pass
        try:
            pname = re.search("([0-9a-fA-F]{5})_([0-9a-fA-F]{8})", CopiedOrgBios).group().split('_')[1]
        except:
            pass
        try:
            baseName = re.search("([A-Za-z]{4})([0-9]{1})", CopiedOrgBios).group()
        except:
            pass
           
        if patchname == '' and cpid == '' and pname == '' and baseName == '':
            secHeader('Copy Original BIOS')
            copyWithProgres(args.bios, CopiedOrgBios)
            secFooter('Original BIOS copied')
        

    else:
        plog('warn','Original BIOS exists\nNo need to copy binary')
        
    return(CopiedOrgBios)
    
        
def removeOldBios():
    #Remove old bios from xmlcli folder before creating new bios
    plog('info','Removing old binary files from CLI and Temp directories')
    for path in [vars.cli_bios_path, r'C:\Temp',r'C:\Users\lab_an4cafe\AppData\Local\Temp\1\XmlCliOut']:      
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                if filename.endswith('.bin'): 
                    os.remove('%s\\%s' % (dirpath,filename))
                             

def htProg():
    
    an_knobstitch_path = config['AN_KNOBSTITCH_PATH']
    biosOutdir = an_knobstitch_path['biosOutdir']
    biosOutdir = biosOutdir.replace('/','\\')
    # getProj(vars.destBiospath)
    ht_error = False   
    msgNeeded = True
    
    if args.ucode == None and args.swconfigs == None:
        binName = args.bios
    else:
        newlist_of_files = glob.glob('%s\\*' % vars.destBiospath)
        binName = max(newlist_of_files, key=os.path.getctime)
    
    pth = os.path.split(binName)[0]
    
    for x in vars.products:
        if x in binName:
            vars.project = x
            break
        else:
            if x in os.path.split(args.bios)[0]:
                vars.project = x
                break

    newBiosPth = ''
    if args.hton == True:
        if 'HTON' in binName:
            plog('warn','BIOS already has HT ON, skipping knob stitch')
            return(newBiosPth)
    elif args.htoff == True:
        if 'HTOFF' in binName:
            plog('warn','BIOS already has HT OFF, skipping knob stitch')
            return(newBiosPth)
    
    plog('notify','Checking if correct BIOS is used to prog HT knobs')
    if vars.project in vars.products:
        plog('success','Correct BIOS is used for HT option') 
        plog('info','Removing old BIOS in cli out directory')
        removeOldBios() 
        # try:
    
    if args.hton == True:
        try:
            secHeader('Stitching HT ON Knob')
            exitCode = cli.CvProgKnobs("ProcessorHyperThreadingDisable=0x0", binName, 'HTON', False, vars.cli_bios_path)

            if exitCode == 0:
                secFooter('HT ON Knob Stitch')
            else:
                plog('error','Failed to stitch HT Knob')
                
        except:
            plog('error','Error in HT ON Knob Stitch')

        fp = listBins()
        if args.bios == fp:
            fp = ''
        if fp == '':
            if 'HTOFF' in binName:
                bios = binName.replace('_HTOFF','')
                os.raname(binName, bios)
                newBiosPth = bios
            else:
                if 'HTON' in binName:
                    plog('info','BIOS has HTON in name')
                    newBiosPth = binName
                else:  
                    new = '%s_HTON.bin' % binName.split('.bin')[0]
                    if os.path.isfile(new) == False:
                        os.rename(binName, new)
                        newBiosPth = new
                    else:
                        plog('warn','Binary file exists with HTON\nBIOS: %s'% new)
                        newBiosPth = new
                        msgNeeded = True
        else:
            if 'HTOFF' in fp:
                bios = fp.replace('_HTOFF','')
                b = '%s\\%s' % (pth, bios.split('\\')[-1])
                newBiosPth = copyWithProgres(fp, b)
                vars.pathToSaveLog = os.path.split(b)[0].rsplit('\\',1)[0]
            elif 'HTON' in fp:
                plog('info','BIOS created with CLI has HTON in name') 
                copyTo = '%s/%s' % (pth, os.path.split(fp)[1])
                newBiosPth = copyWithProgres(fp, copyTo)
                vars.pathToSaveLog = os.path.split(copyTo)[0].rsplit('\\',1)[0]

    elif args.htoff == True:    
        try:
            secHeader('Stitching HT OFF Knob')
            exitCode = cli.CvProgKnobs("ProcessorHyperThreadingDisable=0x1", binName, 'HTOFF', False, vars.cli_bios_path)

            if exitCode == 0:
                secFooter('HT OFF Knob Stitch')
            else:
                plog('error','Failed to stitch HT Knob')
                
        except:
            plog('error','Error in HT OFF Knob Stitch')

            
        fp = listBins()
        if args.bios == fp:
            fp = ''
        if fp == '':
            if 'HTON' in binName:
                bios = binName.replace('_HTON','')
                os.raname(binName, bios)
                newBiosPth = bios
            else:
                if 'HTOFF' in binName:
                    plog('info','BIOS has HTOFF in name')
                    newBiosPth = binName
                else:  
                    new = '%s_HTOFF.bin' % binName.split('.bin')[0]
                    if os.path.isfile(new) == False:
                        os.rename(binName, new)
                        newBiosPth = new
                    else:
                        plog('warn','Binary file exists with HTON\nBIOS: %s' % new)
                        newBiosPth = new
                        msgNeeded = True
        else:
            if 'HTON' in fp:
                bios = fp.replace('_HTON','')
                a = os.path.split(bios)[1]
                b = '%s\\%s' % (pth, bios.split('\\')[-1])
                newBiosPth = copyWithProgres(fp, b)
                vars.pathToSaveLog = os.path.split(b)[0].rsplit('\\',1)[0]
            elif 'HTOFF' in fp:
                plog('info','BIOS created with CLI has HTOFF in name')
                copyTo = '%s/%s' % (pth, os.path.split(binName)[1].replace('.bin','_HTOFF.bin'))
                newBiosPth = copyWithProgres(fp, copyTo)
                vars.pathToSaveLog = os.path.split(copyTo)[0].rsplit('\\',1)[0]

        updatedBinFile = listBins()
        binFileName = os.path.split(binName)[1].split('.bin')[0]
        updatedBinFile.split(binFileName)[0]
        
        removeFileIfduplicate(binName)
        
        if msgNeeded == False:
            plog('info','\nBIOS updated:\n %s' % newBiosPth)
        if args.hton == True:
            hyperStatus = 'HTON'
        elif args.htoff == True:
            hyperStatus = 'HTOFF'
        if msgNeeded == False:
            plog('notify','Updated BIOS with %s knob set' % hyperStatus)

    else:
        if ht_error == False:
            plog('error','Incorrect BIOS, HT option cannot be used')
    vars.finalBios = newBiosPth
    vars.destBiospath = os.path.split(newBiosPth)[0]
    
    return(newBiosPth)


def removeFileIfduplicate(binName):
    import os, time, sys
    #Check if file is created within last 60 seconds before it is deleted.
    #This is the delete the file if there is one without HT knob in name
    fp = os.path.split(binName)[0]
    list_of_files = os.listdir(fp)
    list_of_files = [x for x in list_of_files if x != '']
    now = time.time()

    for f in list_of_files:
        if f == os.path.split(binName)[1]:
            if os.stat('%s\%s' % (fp, f)).st_mtime < now - 60:
                if os.path.isfile('%s\%s' % (fp, f)):
                    os.remove(os.path.join(fp, f))
          
  
def flashingBios():

    an_paths = config['AN_PATHS']
    all_projects = config['PROJECTS']
    taglist = config['TAGLIST']
    tags = taglist['tags']
    tags = tags.split(',')
    
    #Use latest bios package to flash bios. using hardcoded biospackage path


    task = vars.allTags
    flashBIOS = ''

    list_of_files = glob.glob('%s\\*' % vars.destBiospath)

    tsk = []
    if ',' in task:
        tsk = task.split(',')
    else:
        if type(task) == list:
            tsk = task
        else:
            tsk.append(task)
    try:
        tsk = [x for x in tsk if x != '']
    except:
        pass
    try:
        tsk = [x.strip(',') for x in tsk]
    except:
        pass
    try:   
        qtsk = [x.strip(' ') for x in tsk]
    except:
        pass

    try:
        for file in list_of_files:
            pth, fle = os.path.split(file)[0], os.path.split(file)[1]
            baseName = re.search("([A-Za-z]{4})([0-9]{1})", fle).group()
            baseNameUpper = baseName.upper()
            nfile = fle.replace(baseName, baseNameUpper)
            newFle = '%s\%s' % (pth, nfile)
            os.rename(file, newFle)
    except:
        pass
        
    for file in list_of_files:
        fl = os.path.split(file)[1]
        x = 0
        count = 0
        tg = ''
        for tg in tags:
            if '%s' % tg in fl:
                x += 1

        try:
            if x == len(tsk):
                for t in tsk:
                    if t.upper() in file:
                        count += 1
                if count == x:
                    flashBIOS = file
                    flashBIOS = flashBIOS.replace('/','\\')
                    break
        except:
            pass

    if flashBIOS == '':
        plog('warn','BIOS does not have all the desired tags needed or does not exist for this SwConfig')
        return('BIOS not located')

    else:
        
        decision = 'yes'
        if vars.project != os.environ['SiliconFamily']:
            plog('error', 'You are about to flash an %s bios on a system used for %s silicon' % (vars.project, os.environ['SiliconFamily']))
            if '2.7' in vars.ver:
                decision = str.lower(raw_input ('Do you wish to continue: [y]/n: '))
            else:
                decision = str.lower(input ('Do you wish to continue: [y]/n: '))

        if decision == 'yes' or decision == 'y':  
        
            plog('info','Checking if BIOS is valid before flashing')
            if os.path.isfile(flashBIOS) == True:
                plog('success','Bios is Valid')
                #Flash BIOS section
               
                call_flasher(flashBIOS)

            else:
                plog('error', 'Invalid BIOS')
                vars.ulockCheck = False
        else:
            plog('warn','User chose not to continue flashing')
            vars.ulockCheck = False


def copyWithProgres(src_file, dst_file):
    file_size = os.path.getsize(src_file)
    chunk_size = 1024 * 1024  # 1 MB
    with open(src_file, 'rb') as src, open(dst_file, 'wb') as dst:
        bytes_copied = 0
        while True:
            buf = src.read(chunk_size)
            if not buf:
                break
            dst.write(buf)
            bytes_copied += len(buf)
            progress = (bytes_copied / file_size) * 100
            if '2.7' in vars.ver:
                sys.stdout.write("\rProgress: %.2f%%" % progress)
                sys.stdout.flush()
            else:
                print("\rProgress: {:.2f}%".format(progress), end="", flush=True)
    print("\rProgress: 100.00%")
    return dst_file
       
    
def plog(level, message):
    #Ued for logging and changing color of output to screen
    if level == 'warn':
        print ('\033[1;33;40m')
        logger.info('%s' % message)
    elif level == 'error':
        print ('\033[1;31;40m')
        logger.error('%s' % message)
    elif level == 'notify':
        print ('\033[1;36;40m')
        logger.info('%s' % message)
    elif level == 'success':
        print ('\033[1;32;40m')
        logger.info('%s' % message)
    elif level == 'info': 
        logger.info('%s' % message)
    #reset color after logging and output of message
    print('\033[1;37;40m')
 
 
def secHeader(section):
    #printing and logging header of each section
    logger.info('####################################')
    logger.info('##### %s has started #####' % section)
    logger.info('####################################')
    
    
def secFooter(section):
    #print and log ending of each section
    plog('success','=== %s was successful ===\n' % section)

 
def PostCode():
    #Function created to use TTK API instead of scratchpad from BIOS
    cfg = ConfigManager()
    pltObj = cfg.LoadXml(r"C:\SVSHARE\User_Apps\TTK2\Xml Configurations\MiniPort80_smbus.xml")

    try:
        p80Interface = Port_80()
        if p80Interface:
            p80Interface.OpenPort80Interface(pltObj)
            p= p80Interface.Read()
            pcode = p[0].Result[0]
            return(hex(pcode))
    except:
        plog('warn','Could Not Read Post Code')


def unlock():
    
    plog('info','Getting Ready to Unlock Automation')
    xwrapper_post_code = hex(0xf6)
    satellite_post_code = hex(0xf5)
    stuck = hex(0x0)
    counter = 0
    #Path to unlocker exe    
    unlocker = config['AN_UNLOCK_PATH']
    
    #Loops to check for final post code for Xwrapper or Satellite. 
    #Errors out if post code reaches times specified in ini file
    while counter <= 20:
        time.sleep(int(unlocker['sleep']))

        post_code = PostCode()

        plog('notify','Post Code: %s' % post_code)
        if post_code == stuck and counter >= int(unlocker['times_at_postcode']):
            plog('error','Platform is stuck at Post Code: %s' % post_code)
            plog('warn','Unlocker will be skipped')
            break
            return('Unlocker Failed')
        else:    
            if post_code != stuck:
                counter = 0
                stuck = post_code
            if post_code == xwrapper_post_code or post_code == satellite_post_code:
                plog('success','Post Code %s reached\n' % post_code)
                
                secHeader('Unlocker')
                unlock = unlocker['unlocker']
                unlock = unlock.replace('/','\\')
                plog('info','Calling Unlocker\n%s\n' % unlock)
                subprocess.check_call(unlocker['unlocker'])
                secFooter('Unlocker Automation')
                break
            
            else:
                counter += 1
    
    
def create_log_file():
    #Creates log file for logging script activity
    import logging
    an_paths = config['AN_PATHS']
    if args.log == None:
        an_paths = config['AN_PATHS']
        log_file = '%s' % an_paths['log_file']
    else:
        if '"' in args.log:
            args.log = args.log.replace('"','')
        log_file = args.log
        

    log_path = log_file.split(os.path.basename(log_file))[0]
    global logger
    #check if log directory exists. if not create it
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    now = datetime.now()

    log_file =  '%s\%s_%s' % (log_file.split(os.path.basename(log_file))[0], 
    now.strftime('%Y_%m_%d_%H_%M_%S'),os.path.basename(log_file))

    open(log_file,'w')
        
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
      
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    global formatter 
    #Fomats the each line logged
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(logging.StreamHandler())

  
def getProj():
    an_paths = config['AN_PATHS']
    all_projects = config['PROJECTS']
    if vars.project == '':
        for proj in all_projects:
            if all_projects[proj].split('_')[0] in args.bios:
                vars.project = all_projects[proj].split('_')[0]
        if vars.project == '':
            cpuidList = dict(config.items('PROJECTS')).keys()
            for cpid in cpuidList:
                if cpid in args.bios:
                    vars.project = all_projects[cpid].split('_')[0]
  
  
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 
    '''
    Usage:
    This script will update the BIOS with the Patch provided in the command line.
    ''')
    parser.add_argument('-b', '--bios',help = '''BIOS path needs to be a full valid path to binary.''',
                                                default = None, type = str)
    parser.add_argument('-u', '--ucode',help = '''Ucode path needs to be a full valid path to pdb file''',
                                                default = None, type = str)
    parser.add_argument('-sc', '--swconfigs',help = '''SwConfig needs to have full path to use user specified knobs.
                                                    This must be used with -c or --copy option.''',
                                                default = None, type = str)
    parser.add_argument('-f', '--flash',help = '''Argument is used to trigger BIOS flash
                                                    If not used flash feature will be skipped''',
                                                action = 'store_true')
    parser.add_argument('-t', '--task',help = '''The Task or software config is used for BIOS flashing.
                                                    If left blank it will be read from SwConfig env var''',
                                                default = None, type = str)
    parser.add_argument('-c', '--copy',help = '''Argument is used to trigger the copy of both Binary and Patch to share drive''',
                                                action = 'store_true')
    parser.add_argument('-hn', '--hton',help = '''This argument will unlock the system in automation.''',
                                                action = 'store_true')
    parser.add_argument('-hf', '--htoff',help = '''This argument will unlock the system in automation.''',
                                                action = 'store_true')
    parser.add_argument('-ul', '--unlock',help = '''This argument will unlock the system in automation.''',
                                                action = 'store_true')
    parser.add_argument('-l',  '--log',help = '''Log file created for script. User can specify log file full path to be used
                                                if left blank the file from ini will be used''',
                                                default = None, type = str)
    parser.add_argument('-d', '--delpatch',help = '''delete all previous patches in BIOS.
                                                if left blank it will update the CPUID from patch''',
                                                action = 'store_true')                                            
                                                
    args = parser.parse_args()
    raw_bios_used = False
    
    #Create log at beginning of each run
    create_log_file()
    
    #Get cli path for python27 or python3
    an_paths = config['AN_PATHS']
    cli_bios_path = an_paths['cli_bios_path']
    vars.cli_bios_path = cli_bios_path.replace('/','\\')
    vars.ver = sys.version
    if '2.7' in vars.ver:
        vars.cli_bios_path = vars.cli_bios_path.replace('python37','python27')
        
    
    plog('notify','\n\n*****Patch Regression Has Started*****\n')

    #Check if ucode provided is valid and rids of any quotes and spaces
    if args.ucode != None and args.ucode != '': 
        if "/" in args.ucode:
            args.ucode = args.ucode.replace('/','\\')
        if '"' in args.ucode:
            args.ucode = args.ucode.replace('"','')
        if ' ' in args.ucode:
            args.ucode = args.ucode.strip()
        if ":" in os.path.split(args.ucode)[0]:
            args.ucode = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync' + args.ucode.split(':')[1]
        if os.path.isfile(args.ucode) == False:
            plog('warn','Invalid Ucode provided')
            exit()
          
    
    #Check if BIOS provided is valid and rids of any quotes and spaces
    if args.bios != None and args.bios != '':
        baseName = ''
        # try:
                
            # baseName = re.search("([A-Za-z]{4})([0-9]{1})", args.bios).group()
        # except:
            # pass
        tasks = config['TASKLIST']
        for t in tasks:
            if t in args.bios:
                baseName = t
                break
        if baseName != '':
            plog('warn','Only BIOS with default knobs should be used')
            if '2.7' in vars.ver:
                decision = str.lower(raw_input ('Do you wish to flash Raw Bios? [y]/n: '))
            else:
                decision = str.lower(input ('Do you wish to flash Raw Bios? [y]/n: '))
                
            if decision == 'yes' or decision == 'y': 
                raw_bios_used = True
                
            else:    
                exit()

        if '"' in args.bios:
            args.bios = args.bios.replace('"','')
        if ' ' in args.bios:
            args.bios = args.bios.strip()
        if ":" in os.path.split(args.bios)[0]:
            args.bios = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync' + args.bios.split(':')[1]
        if os.path.isfile(args.bios) == False:
            plog('warn','Invalid BIOS provided')
            exit()
                
            
    #Check if SwConfig provided is valid and rids of any quotes and spaces    
    getProj()
    if args.swconfigs != None and args.swconfigs != '':
        if vars.project not in vars.products:
        
            if "/" in args.swconfigs:
                args.swconfigs = args.swconfigs.replace('/','\\')
            if '"' in args.swconfigs:
                args.swconfigs = args.swconfigs.replace('"','')
            if ' ' in args.swconfigs:
                args.swconfigs = args.swconfigs.strip()
            if ":" in os.path.split(args.swconfigs)[0]:
                args.swconfig = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync' + args.swconfig.split(':')[1]
            if args.swconfigs.endswith('.ini'):
                if os.path.isfile(args.swconfigs) == False:
                    plog('warn','Invalid SwConfig provided')
                    exit()
            else:
                if os.path.isdir(args.swconfigs) == False:
                    plog('warn','Invalid SwConfig Directory provided')
                    exit()
        else:
            plog('warn','This BIOS does not use SwConfigs')
            exit()
   
   
    #Take snapshot of setup from GUI
    setupSnapshot()
    
    
    #delete old bios from cli and temp directory
    removeOldBios()
    
    
    #Perform BIOS modification using ifwistitcher
    if raw_bios_used == False:
        if args.ucode != None or args.swconfigs != None:
            knobandstitch()
    
    
        #Check if HTON or HTOFF options are set and can be used for bios
        if args.hton == True or args.htoff == True:
            htProg()


    #Flash BIOS if user selected
    if args.flash == True:
        if args.ucode == None and args.swconfigs == None:
            if args.hton == False and args.htoff == False:
                call_flasher(args.bios)
            else:
                flashingBios()
        else:
            if args.hton == False and args.htoff == False:
                checkTask()
                flashingBios()
            else:
                flashingBios()
    
    
    #Unlock system if user selected
    if vars.ulockCheck != False:
        if args.unlock == True:
            exit_code = unlock()
    else:
        plog('warn','Unlocker was skipped due to flashing error')
  
  
      #Copy original BIOS to Raw BIOS directory under Project/CpuStep
    CopyOrgBios()
        
        
    #print the final updated BIOS for user.
    if vars.finalBios.endswith('.bin'):
        # latest_file = vars.finalBIOS
        finalBios = vars.finalBios
    else:
        newlist_of_files = glob.glob('%s\\*' % vars.destBiospath)
        finalBios = max(newlist_of_files, key=os.path.getctime)

    plog('notify','Final Updated BIOS: %s' % finalBios)
    
    
    if vars.changemade == True:
        #Create a log file for modified BIOS
        pathtoLog = '%s/Logs' % vars.destBiospath.rsplit('\\',1)[0]
        logFileName = os.path.split(vars.log_file)[1]
        if os.path.isdir(pathtoLog) == False:
            os.makedirs(pathtoLog)
        
        newPathToLog = '%s/%s' % (pathtoLog, logFileName)
        shutil.copyfile(vars.log_file, newPathToLog)

        
    
    

