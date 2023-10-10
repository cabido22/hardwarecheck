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
import os, sys
from io import open
os.system(u"")
from os import path
import time
from datetime import datetime, timedelta
import subprocess
time.sleep(.5)
import glob
import logging

import ConfigParser
config = ConfigParser.ConfigParser()
print os.path.realpath(sys.argv[0])
script_path = os.path.realpath(sys.argv[0])
ini_path = u'%s\\patch_regression.ini' % u'\\'.join(script_path.split(u'\\')[0:-1])
config.read(ini_path)

import shutil
from pathlib import Path as p


def listBins():
    an_paths = config[u'AN_PATHS']
    new_bios_path = an_paths[u'new_bios_path']
    fullPth = None
    fle = os.listdir(new_bios_path)
    for x in fle:
        if x.endswith(u'.bin'):
            fullPth = (new_bios_path +u'\\'+ x)
    if fullPth == None:
        return(args.bios)
    else:
        return(fullPth)



def ucodeUpdate(bios_path, ucode_path):
    an_paths = config[u'AN_PATHS']
    new_bios_path = an_paths[u'new_bios_path']
    
    import pysvtools.xmlcli.XmlCli as cli
    
    if args.delpatch == True:
        # Try to remove old patches from BIOS in argument 
        try:
            secHeader(u'Removing Old Ucode patches')
            cli.ProcessUcode(u"deleteall", bios_path)
            secFooter(u'Remove Old Ucode patches')
        except:

            plog(u'error',u'Error in removing old patches from binary')
            
    try:
        # Rename new BIOS with now patches 
        fp = listBins()
                  
        if fp != bios_path:
            l = fp.split(u'\\')[-1].split(u'_',5)[0:5]
            binName = ucode_path.split(u'\\')[-1]
            strippedBin = ur'%s.bin' % (u"_".join(l))
            fullPath = u'%s\\%s' % (new_bios_path, strippedBin)
            os.rename(fp, fullPath)
        else:
            # if no pathces were removed from BIOS then use the original bios
            fullPath = bios_path
    except:
        plog(u'warn', u'No patch detected in BIOS')
        
    try:
        # Try to update new BIOS with new patch from argument
        secHeader(u'Ucode Patch Updating')
        cli.ProcessUcode(u"update", fullPath.strip(), ucode_path)
        # Get new BIOS from directory
        updatedBin = listBins()
        plog(u'info',u'Updated Bios: %s' % updatedBin)
        secFooter(u'Ucode Patch Update')
        return(updatedBin)
    except:
        plog(u'error', u'Error in Ucode update')
        
    
        
def removeOldBios():
    #Remove old bios from xmlcli folder before creating new bios
    an_paths = config[u'AN_PATHS']
    new_bios_path = an_paths[u'new_bios_path']
    fle = os.listdir(new_bios_path)
    secHeader(u'Remove Old Bios')
    for x in fle:
        if x.endswith(u'.bin'):
            os.remove(u'%s\\%s' % (new_bios_path,x))
            
    secFooter(u'Remove Old Bios')
        
def getPath(newBios):
    #getting path to BIOS if the swconfig knobs were not stitched
    an_knobstitch_path = config[u'AN_KNOBSTITCH_PATH']
    biosOutdir = an_knobstitch_path[u'biosOutdir']
    #Get project from user or env var
    if args.project == None or args.project == u'':
        project = os.environ[u'SiliconFamily']
    else:
        project = args.project
    #Get task from user or env var
    if args.cpustep == None or args.cpustep == u'':
        cpustep = os.environ[u'CpuStep']
    else:
        cpustep = args.cpustep
        
    patch = args.ucode.split(u'\\')[-1].split(u'.')[0]
    BIOSname = newBios.split(u'\\')[-1]
    
    movedBiosPath = u'%s\\%s\\%s\\%s' % (biosOutdir, project, cpustep, patch)
    #Check if path to binary exists
    if os.path.exists(movedBiosPath) == False:
        os.makedirs(movedBiosPath)
    else:
        plog(u'warn', u'Stitched BIOS path path exists')
   
    sharedrive_Bios = (u'%s\\%s' % (movedBiosPath, BIOSname))
    #Copy BIOS to share drive
    try:
        if os.path.exists(sharedrive_Bios) == False:
            secHeader(u'Copying stitched binary to Share Drive')
            shutil.copyfile(newBios, sharedrive_Bios)
            secFooter(u'Copying stitched binary')
        else:
            plog(u'warn', u'Binary File path exists: \n%s\nNo need to copy binary' % sharedrive_Bios)
    except:
        plog(u'error', u'Error in copying bin files to shared dir')
        
    return(movedBiosPath)
        
    
def flashingBios(stitchedBiosPth, task):

    an_paths = config[u'AN_PATHS']
    
    #Use latest bios package to flash bios. using hardcoded biospackage path
    # latest_stitcher = max(glob.glob(os.path.join(an_paths['BiosPackage_Path'], '*/')), key=os.path.getmtime)
    flasher = u'%s\\BiosPackage.py' % an_paths[u'BiosPackage_Path']
    
    latest_file = u''
    flashBIOS = u''
    # if user is not copying binaries to new path then bios in arg will be used
    if args.copy == False:
        flashBIOS = args.bios
        plog(u'notify',u'Using Raw BIOS provided')

    else:
        #Check if binary with task(swconfig) located in dir
        list_of_files = glob.glob(u'%s\\*' % stitchedBiosPth)
        for file in list_of_files:
            if task in file:
                flashBIOS = file

    if flashBIOS == u'':
        plog(u'warn', u'No BIOS specified per SwConfig')
    else:
        plog(u'warn', u'BIOS to be Flashed: %s' % flashBIOS)
        plog(u'info',u'Checking if BIOS is valid before flashing')
        if os.path.isfile(flashBIOS) == True:
            #Flash BIOS section
            try:
                plog(u'info',u'flash command: ' + flasher + u' -b ' + flashBIOS)
                os.system(flasher + u' -b ' + flashBIOS)
            except:
                plog(u'error', u'Error with flashing BIOS')
        else:
            plog(u'error', u'Invalid BIOS')

    
def copyBin(fullPth):
    
    #Read ini file to get ucod directory
    an_paths = config[u'AN_PATHS']
    ucode_dir = an_paths[u'ucode_dir']
    # #Get project from user or env var
    # if args.project == None:
        # project = os.environ['SiliconFamily']
    # else:
        # project = args.project
    #Get cpu step from command line
    if args.cpustep == None or args.cpustep == u'':
        cpustep = os.environ[u'CpuStep']
    else:
        cpustep = args.cpustep
    
    
    fullpatchname = args.ucode.split(u'\\')[-1]
    patch = fullpatchname.split(u'.')[0]
    #Check if path exists 
    if os.path.exists(u'%s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch)) == False:
        os.makedirs(u'%s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch))
    else:
        plog(u'warn', u'Ucode Patch path exists: \n%s\\%s\\%s\\%s\nNo need to create directory' % (ucode_dir, project, cpustep, patch))
        
    newPath = u'%s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch)
    binName = u'%s\\%s'% (newPath, fullPth.split(u'\\')[-1])
    ucodeName = u'%s\\%s' % (newPath, fullpatchname)
    #Copy ucode and binary to share drive
    from shutil import copyfile
    try:
        if os.path.exists(binName) == False:
            secHeader(u'Copying binary to Share Drive')
            copyfile(fullPth, binName)
            secFooter(u'Copying binary')

        else:
            plog(u'warn',u'Binary File path exists: %s\nNo need to copy binary' % binName)
    except:
        plog(u'error', u'Error in copying bin files to dir')
        
    try:
        if os.path.exists(ucodeName) == False:
            secHeader(u'Copying Patch File to Share Drive')
            copyfile(args.ucode, ucodeName)
            plog(u'info',u'Patch file: %s' % ucodeName)
            secFooter(u'Copying Patch File to Share Drive')
        else:
            plog(u'warn',u'Patch file exists: %s\nNo need to copy patch file to share drive' % ucodeName)

    except:
        plog(u'error', u'Error in copying patch file to dir')
    
       
    return(binName)
    
    
def plog(level, message):
    #Ued for logging and changing color of output to screen
    if level == u'warn':
        print u'\033[1;33;40m'
        logger.info(u'%s' % message)
    elif level == u'error':
        print u'\033[1;31;40m'
        logger.error(u'%s' % message)
    elif level == u'notify':
        print u'\033[1;36;40m'
        logger.info(u'%s' % message)
    elif level == u'success':
        print u'\033[1;32;40m'
        logger.info(u'%s' % message)
    elif level == u'info': 
        logger.info(u'%s' % message)
    #reset color after logging and output of message
    print u'\033[1;37;40m'
 
def secHeader(section):
    #printing and logging header of each section
    logger.info(u'####################################')
    logger.info(u'##### %s has started #####' % section)
    logger.info(u'####################################')
    
    
def secFooter(section):
    #print and log ending of each section
    plog(u'success',u'=== %s was successful ===\n' % section)

 
def getCpustep():
    #get CpuStep from argument provided or from env var
    if args.cpustep == None or args.cpustep == u'':
        cpustep = os.environ[u'CpuStep']
    else:
        cpustep = args.cpustep
    # strip cpu step to the letter and add 0. SwConfigs all are named by letter and 0 stepping  
    if u'_' in cpustep:
        cpu = cpustep.split(u'_')[0]
        step = u'%s0' % list(cpu)[0]
    else:
        step = u'%s0' % list(cpustep)[0]
 
    return(step)
 
def knobStitch(project, newPath):
    
    an_knobstitch_path = config[u'AN_KNOBSTITCH_PATH']
    biosOutdir = an_knobstitch_path[u'biosOutdir']
    SwConfig_Path = an_knobstitch_path[u'SwConfig_Path']
    ifwistitcher_path = an_knobstitch_path[u'ifwistitcher_path']
    stitcher_path = an_knobstitch_path[u'stitcher_path']
    swconfigs = an_knobstitch_path[u'swconfigs']
   
    try:
        #find latest version of ifwistitcher. Changed ifwistitcher_path to stitcher_path
        
        # latest_stitcher = max(glob.glob(os.path.join(ifwistitcher_path, '*/')), key=os.path.getmtime)
        stitcher = u'%s\\ifwistitcher.py' % stitcher_path

    except:
        plog(u'error', u'Trouble locating latest ifwistitcher')
        
    step = getCpustep()
    cpustep = args.cpustep
    
    try:
        if args.swconfigs == None:
            #find lastest swconfig
            latest_swconfigs = max(glob.glob(os.path.join(SwConfig_Path, u'*/')), key=os.path.getmtime)
            swconfig = u'%s%s\\%s' % (latest_swconfigs, project, step)
        else:
            swconfigs = args.swconfigs

    except:
        plog(u'error', u'Trouble locating latest SwConfigs')
    
    if os.path.exists(swconfigs) == True:
        
        fullPth = None
        fullpatchname = args.ucode.split(u'\\')[-1]
        patch = fullpatchname.split(u'.')[0]
        #build command to run ifwistitcher
        BIOSpath = (u'%s\\%s\\%s\\%s' % (biosOutdir, project, cpustep, patch))
        if os.path.exists(BIOSpath) == False:
            os.makedirs(BIOSpath)
            plog(u'notify',u'Directory created for ifwistitcher')

        else:
            plog(u'info',u'BIOS out path exists and ready for ifwistitcher')
        
            #Check if binaries already exist in new path
        fle = os.listdir(BIOSpath)
        
        if args.task == None or args.task == u'':
            task = os.environ[u'SWConfig']
        else:
            task = args.task
        #Check if Binary exists per software config
        for x in fle:
            if task in x:
                fullPth = (BIOSpath +u'\\'+ x)
        #if binary does not exist then run stitcher
        if fullPth == None:
            try:
                      
                secHeader(u'IfwiStitcher')
                plog(u'info',u'python %s -op KnobChange -m Offline -b %s -ki %s -o %s\n' % (stitcher, newPath, swconfigs, BIOSpath))
                
                subprocess.run(u'python %s -op KnobChange -m Offline -b %s -ki %s -o %s' % (stitcher, newPath, swconfigs, BIOSpath))

            except:
                plog(u'error',u'Knob stitching failed')
                
        else:
            plog(u'warn',u'Binaries already exist for this Patch: %s\nIfwistitcher will be skipped' % BIOSpath)
        
    else:
        plog(u'error',u'Invalid path to swconfig')
        
    return(BIOSpath)
    

def unlock(project):
    
    import namednodes
    projects = config[u'PROJECTS']
    namednodes.settings.PROJECT = u'%s' % projects.get(os.environ[u'SiliconFamily'])
    print u'\033[1;36;40m \nProject: %s \033[1;37;40m' % projects.get(os.environ[u'SiliconFamily'])

    l = [u'SKX',u'CLX']
    if any(project == proj for proj in l):
        import components.socket
        sockets=components.socket.getAll()
    else:
        sockets = namednodes.sv.socket.get_all()

    time.sleep(5)
    xwrapper_post_code = 0xf6000000
    satellite_post_code = 0xf5000000
    stuck = 0x0
    counter = 0
    #Path to unlocker exe    
    unlocker = config[u'AN_UNLOCK_PATH']
    #Loops to check for final post code for Xwrapper or Satellite. 
    #Errors out if post code reaches times specified in ini file
    while counter <= 20:
        time.sleep(int(unlocker[u'sleep']))
        post_code = sockets[0].uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
        # post_code = sv.socket0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
        plog(u'notify',u'Post Code: %s' % post_code)
        if post_code == stuck and counter >= int(unlocker[u'times_at_postcode']):
            plog(u'error',u'Platform is stuck at Post Code: %s' % post_code)
            plog(u'warn',u'Unlocker will be skipped')
            break
            return(u'Unlocker Failed')
        else:    
            if post_code != stuck:
                counter = 0
                stuck = post_code
            if post_code == xwrapper_post_code or post_code == satellite_post_code:
                plog(u'success',u'Post Code had been reached: %s\n' % post_code)
                
                secHeader(u'Unlocker')
                subprocess.run(unlocker[u'unlocker'])
                secFooter(u'Unlocker Automation')
                break
            
            else:
                counter += 1
    
def create_log_file():
    #Creates log file for logging script activity
    import logging
    an_paths = config[u'AN_PATHS']
    if args.log == None:
        an_paths = config[u'AN_PATHS']
        log_file = u'%s' % an_paths[u'log_file']
    else:
        log_file = arg.log

    log_path = log_file.split(os.path.basename(log_file))[0]
    global logger
    #check if log file exists. if not create it
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    if os.path.isfile(log_file):
        #check if log file is over a day old
        one_day_ago = datetime.now() - timedelta(days=1)
        filetime = datetime.fromtimestamp(path.getctime(log_file))

        if filetime < one_day_ago:
            # print "File is more than one day old"
            now = datetime.now()
            os.rename(log_file, u'%s\\%s_%s' % (log_file.split(os.path.basename(log_file))[0], 
            now.strftime(u'%Y_%m_%d_%H_%M_%S'),os.path.basename(log_file)))
            open(log_file,u'w')
        else:
            print u'Using current log file: %s' % log_file
        
    
    else:
        open(log_file,u'w')
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
      
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    global formatter 
    #Fomats the each line logged
    formatter = logging.Formatter(u'%(asctime)s - %(levelname)s - %(message)s', datefmt=u'%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(logging.StreamHandler())

        
if __name__ == u'__main__':

    parser = argparse.ArgumentParser(description = 
    u'''
    Usage:
    This script will update the BIOS with the Patch provided in the command line.
    ''')
    parser.add_argument(u'-b', u'--bios',help = u'''BIOS path needs to be a full valid path to binary.''',
                                                default = None, type = unicode)
    parser.add_argument(u'-u', u'--ucode',help = u'''Ucode path needs to be a full valid path to pdb file''',
                                                default = None, type = unicode)
    parser.add_argument(u'-sc', u'--swconfigs',help = u'''SwConfig needs to have full path to use user specified knobs.
                                                    If left blank it will read from ini file.''',
                                                default = None, type = unicode)
    parser.add_argument(u'-p', u'--project',help = u'''Project is used to build path where BIOS will be copied to share drive. 
                                                    If left blank it will read project from env var.
                                                    List of valid projects in ini file. (Example: ICX)''',
                                                default = None, type = unicode)
    parser.add_argument(u'-s', u'--cpustep',help = u'''Cpu step is used when copying BIOS to share drive. 
                                                    If left blank script will not work.
                                                    (Example: D3_XCC)''',
                                                default = None, type = unicode)
    parser.add_argument(u'-f', u'--flash',help = u'''Argument is used to trigger BIOS flash
                                                    If not used flash feature will be skipped''',
                                                action = u'store_true')
    parser.add_argument(u'-t', u'--task',help = u'''The Task or software config is used for BIOS flashing.
                                                    If left blank it will be read from SwConfig env var''',
                                                default = None, type = unicode)
    parser.add_argument(u'-c', u'--copy',help = u'''Argument is used to trigger the copy of both Binary and Patch to share drive''',
                                                action = u'store_true')
    parser.add_argument(u'-k', u'--knobs',help = u'''Argument used to trigger ifwistitcher.''',
                                                action = u'store_true')
    parser.add_argument(u'-ul', u'--unlock',help = u'''This argument will unlock the system in automation.''',
                                                action = u'store_true')
    parser.add_argument(u'-l',  u'--log',help = u'''Log file created for script. User can specify log file full path to be used
                                                if left blank the file from ini will be used''',
                                                default = None, type = unicode)
    parser.add_argument(u'-d', u'--delpatch',help = u'''delete all previous patches in BIOS.
                                                if left blank it will update the CPUID from patch''',
                                                action = u'store_true')                                            
                                                
    args = parser.parse_args()
    
    create_log_file()
    #logs beginning of run
    plog(u'notify',u'\n\n*****Patch Regression Has Started*****\n')

    if args.project == None:
        project = os.environ[u'SiliconFamily']
    else:
        project = args.project

    if args.bios != None:
        
        if args.ucode != None:
    
            if os.path.isfile(args.bios) == True and os.path.isfile(args.ucode) == True:
                #Get project from user or env var
                    #Check if project is valid from ini file
                proj = u''
                projects = config[u'PROJECTS']
                for key in projects:
                    if key.upper() == project.upper():
                        plog(u'notify',u'Project: %s' % key.upper())
                        proj = key.upper()
                if proj == u'':
                    plog (u'error', u'Invalid Project')
                    sys.exit(u'Project: %s' % args.project.upper())

                #Remove old bios from out dir and then update BIOS
                removeOldBios()
                updatedBin = ucodeUpdate(args.bios, args.ucode)
                    
                
                if args.copy == True:   
                    if args.cpustep != None:
                        newPath = copyBin(updatedBin)

                        if args.knobs == True:
                            stitchedBiosPth = knobStitch(project, newPath)
                        else:
                            plog(u'notify', u'Knob Stitch is disabled')
                    else:
                        plog(u'error',u'No CPU Step provided')
                
                else:
                    plog(u'notify',u'Copying file is disabled')
                        
                        
                
            
            else:
                plog(u'error',u'Invalid BIOS or Ucode path')
        else:
            plog(u'warn',u'Ucode is missing')
        
        if args.flash == True:  
            if args.copy == False:
                stitchedBiosPth = args.bios
            else:
                if args.knobs == False:
                    plog(u'info',u'BIOS will be copied to share drive')
                    stitchedBiosPth = getPath(newPath)
                    plog(u'info',u'New path: ' + stitchedBiosPth)
                else:
                    plog(u'info',u'Using BIOS from knobStitch')
            if args.task == None or args.task == u'':
                task = os.environ[u'SWConfig']
            else:
                task = args.task

            flashingBios(stitchedBiosPth, task)
            
        else:
            plog(u'notify',u'Flashing disabled')
    else:
        plog(u'warn',u'BIOS is missing')
    
    if args.unlock == True:
        # print(project)
        unlock(project)
    else:
        plog(u'notify',u'Unlocker disabled')
