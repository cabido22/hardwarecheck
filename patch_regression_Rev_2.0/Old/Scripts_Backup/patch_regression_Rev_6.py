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
os.system("")
from os import path
import time
from datetime import datetime, timedelta
import subprocess
time.sleep(.5)
import glob
import logging

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


def listBins():
    # an_paths = config['AN_PATHS']
    # new_bios_path = an_paths['new_bios_path']
   
    fullPth = None
    fle = os.listdir(new_bios_path)
    for x in fle:
        if x.endswith('.bin'):
            fullPth = (new_bios_path +'\\'+ x)
    if fullPth == None:
        return(args.bios)
    else:
        return(fullPth)



def ucodeUpdate(bios_path, ucode_path):
    # an_paths = config['AN_PATHS']
    # new_bios_path = an_paths['new_bios_path']
    
    import pysvtools.xmlcli.XmlCli as cli
    
    if args.delpatch == True:
        # Try to remove old patches from BIOS in argument 
        try:
            secHeader('Removing Old Ucode patches')
            cli.ProcessUcode("deleteall", bios_path)
            secFooter('Remove Old Ucode patches')
        except:

            plog('error','Error in removing old patches from binary')
            
    try:
        # Rename new BIOS with now patches 
        fp = listBins()
                  
        if fp != bios_path:
            l = fp.split('\\')[-1].split('_',5)[0:5]
            binName = ucode_path.split('\\')[-1]
            strippedBin = r'%s.bin' % ("_".join(l))
            fullPath = '%s\\%s' % (new_bios_path, strippedBin)
            os.rename(fp, fullPath)
        else:
            # if no pathces were removed from BIOS then use the original bios
            fullPath = bios_path
    except:
        plog('warn', 'No patch detected in BIOS')
        
    try:
        # Try to update new BIOS with new patch from argument
        secHeader('Ucode Patch Updating')
        cli.ProcessUcode("update", fullPath.strip(), ucode_path)
        # Get new BIOS from directory
        updatedBin = listBins()
        plog('info','Updated Bios: %s' % updatedBin)
        secFooter('Ucode Patch Update')
        return(updatedBin)
    except:
        plog('error', 'Error in Ucode update')
        
    
        
def removeOldBios():
    #Remove old bios from xmlcli folder before creating new bios
    # an_paths = config['AN_PATHS']
    # new_bios_path = an_paths['new_bios_path']
    fle = os.listdir(new_bios_path)
    secHeader('Remove Old Bios')
    for x in fle:
        if x.endswith('.bin'):
            os.remove('%s\\%s' % (new_bios_path,x))
            
    secFooter('Remove Old Bios')
        
def getPath(newBios):
    #getting path to BIOS if the swconfig knobs were not stitched
    an_knobstitch_path = config['AN_KNOBSTITCH_PATH']
    biosOutdir = an_knobstitch_path['biosOutdir']
    #Get project from user or env var
    if args.project == None or args.project == '':
        project = os.environ['SiliconFamily']
    else:
        project = args.project
    #Get task from user or env var
    if args.cpustep == None or args.cpustep == '':
        cpustep = os.environ['CpuStep']
    else:
        cpustep = args.cpustep
        
    patch = args.ucode.split('\\')[-1].split('.')[0]
    BIOSname = newBios.split('\\')[-1]
    
    movedBiosPath = '%s\\%s\\%s\\%s' % (biosOutdir, project, cpustep, patch)
    #Check if path to binary exists
    if os.path.exists(movedBiosPath) == False:
        os.makedirs(movedBiosPath)
    else:
        plog('warn', 'Stitched BIOS path path exists')
   
    sharedrive_Bios = ('%s\\%s' % (movedBiosPath, BIOSname))
    #Copy BIOS to share drive
    try:
        if os.path.exists(sharedrive_Bios) == False:
            secHeader('Copying stitched binary to Share Drive')
            shutil.copyfile(newBios, sharedrive_Bios)
            secFooter('Copying stitched binary')
        else:
            plog('warn', 'Binary File path exists: \n%s\nNo need to copy binary' % sharedrive_Bios)
    except:
        plog('error', 'Error in copying bin files to shared dir')
        
    return(movedBiosPath)
        
    
def flashingBios(stitchedBiosPth, task):

    an_paths = config['AN_PATHS']
    
    #Use latest bios package to flash bios. using hardcoded biospackage path
    # latest_stitcher = max(glob.glob(os.path.join(an_paths['BiosPackage_Path'], '*/')), key=os.path.getmtime)
    flasher = '%s\\BiosPackage.py' % an_paths['BiosPackage_Path']
    
    latest_file = ''
    flashBIOS = ''
    # if user is not copying binaries to new path then bios in arg will be used
    if args.copy == None:
        flashBIOS = args.bios
        plog('notify','Using Raw BIOS provided')

    else:
        #Check if binary with task(swconfig) located in dir
        list_of_files = glob.glob('%s\\*' % stitchedBiosPth)
        for file in list_of_files:
            if task in file:
                flashBIOS = file

    if flashBIOS == '':
        plog('warn', 'No BIOS specified per SwConfig')
    else:
        plog('warn', 'BIOS to be Flashed: %s' % flashBIOS)
        plog('info','Checking if BIOS is valid before flashing')
        if os.path.isfile(flashBIOS) == True:
            #Flash BIOS section
            try:
                plog('info','flash command: ' + flasher + ' -b ' + flashBIOS)
                os.system(flasher + ' -b ' + flashBIOS)
            except:
                plog('error', 'Error with flashing BIOS')
        else:
            plog('error', 'Invalid BIOS')

    
def copyBin(fullPth):
    
    #Read ini file to get ucod directory
    an_paths = config['AN_PATHS']
    ucode_dir = an_paths['ucode_dir']
    # #Get project from user or env var
    # if args.project == None:
        # project = os.environ['SiliconFamily']
    # else:
        # project = args.project
    #Get cpu step from command line
    if args.cpustep == None or args.cpustep == '':
        cpustep = os.environ['CpuStep']
    else:
        cpustep = args.cpustep
    
    if args.copy == None or args.copy == '':
        plog ('error','No CPUID provided')
    else:
        cpuid = args.copy
        
    fullpatchname = args.ucode.split('\\')[-1]
    patch = fullpatchname.split('.')[0]
    #Check if path exists 
    if os.path.exists('%s\\%s\\%s_%s\\%s' % (ucode_dir, project, cpuid, cpustep, patch)) == False:
        os.makedirs('%s\\%s\\%s_%s\\%s' % (ucode_dir, project, cpuid, cpustep, patch))
    else:
        plog('warn', 'Ucode Patch path exists: \n%s\\%s\\%s\\%s\nNo need to create directory' % (ucode_dir, project, cpustep, patch))
        
    newPath = '%s\\%s\\%s_%s\\%s' % (ucode_dir, project, cpuid, cpustep, patch)
    binName = '%s\\%s'% (newPath, fullPth.split('\\')[-1])
    ucodeName = '%s\\%s' % (newPath, fullpatchname)
    #Copy ucode and binary to share drive
    from shutil import copyfile
    try:
        if os.path.exists(binName) == False:
            secHeader('Copying binary to Share Drive')
            copyfile(fullPth, binName)
            secFooter('Copying binary')

        else:
            plog('warn','Binary File path exists: %s\nNo need to copy binary' % binName)
    except:
        plog('error', 'Error in copying bin files to dir')
        
    try:
        if os.path.exists(ucodeName) == False:
            secHeader('Copying Patch File to Share Drive')
            copyfile(args.ucode, ucodeName)
            plog('info','Patch file: %s' % ucodeName)
            secFooter('Copying Patch File to Share Drive')
        else:
            plog('warn','Patch file exists: %s\nNo need to copy patch file to share drive' % ucodeName)

    except:
        plog('error', 'Error in copying patch file to dir')
    
       
    return(binName)
    
    
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

 
def getCpustep():
    #get CpuStep from argument provided or from env var
    if args.cpustep == None or args.cpustep == '':
        cpustep = os.environ['CpuStep']
    else:
        cpustep = args.cpustep
    # strip cpu step to the letter and add 0. SwConfigs all are named by letter and 0 stepping  
    if '_' in cpustep:
        cpu = cpustep.split('_')[0]
        step = '%s0' % list(cpu)[0]
    else:
        step = '%s0' % list(cpustep)[0]
 
    return(step)
 
def knobStitch(project, newPath):
    
    an_knobstitch_path = config['AN_KNOBSTITCH_PATH']
    biosOutdir = an_knobstitch_path['biosOutdir']
    SwConfig_Path = an_knobstitch_path['SwConfig_Path']
    ifwistitcher_path = an_knobstitch_path['ifwistitcher_path']
    stitcher_path = an_knobstitch_path['stitcher_path']
    swconfigs = an_knobstitch_path['swconfigs']
   
    try:
        #find latest version of ifwistitcher. Changed ifwistitcher_path to stitcher_path
        
        # latest_stitcher = max(glob.glob(os.path.join(ifwistitcher_path, '*/')), key=os.path.getmtime)
        stitcher = '%s\\ifwistitcher.py' % stitcher_path

    except:
        plog('error', 'Trouble locating latest ifwistitcher')
        
    step = getCpustep()
    cpustep = args.cpustep
    
    try:
        if args.swconfigs == None:
            #find lastest swconfig
            latest_swconfigs = max(glob.glob(os.path.join(SwConfig_Path, '*/')), key=os.path.getmtime)
            swconfig = '%s%s\\%s' % (latest_swconfigs, project, step)
        else:
            swconfigs = args.swconfigs

    except:
        plog('error', 'Trouble locating latest SwConfigs')
    
    if os.path.exists(swconfigs) == True:
        
        fullPth = None
        fullpatchname = args.ucode.split('\\')[-1]
        patch = fullpatchname.split('.')[0]
        #build command to run ifwistitcher
        BIOSpath = ('%s\\%s\\%s\\%s' % (biosOutdir, project, cpustep, patch))
        if os.path.exists(BIOSpath) == False:
            os.makedirs(BIOSpath)
            plog('notify','Directory created for ifwistitcher')

        else:
            plog('info','BIOS out path exists and ready for ifwistitcher')
        
            #Check if binaries already exist in new path
        fle = os.listdir(BIOSpath)
        
        if args.task == None or args.task == '':
            task = os.environ['SWConfig']
        else:
            task = args.task
        #Check if Binary exists per software config
        for x in fle:
            if task in x:
                fullPth = (BIOSpath +'\\'+ x)
        #if binary does not exist then run stitcher
        if fullPth == None:
            try:
                      
                secHeader('IfwiStitcher')
                plog('info','python %s -op KnobChange -m Offline -b %s -ki %s -o %s\n' % (stitcher, newPath, swconfigs, BIOSpath))
                
                subprocess.run('python %s -op KnobChange -m Offline -b %s -ki %s -o %s' % (stitcher, newPath, swconfigs, BIOSpath))

            except:
                plog('error','Knob stitching failed')
                
        else:
            plog('warn','Binaries already exist for this Patch: %s\nIfwistitcher will be skipped' % BIOSpath)
        
    else:
        plog('error','Invalid path to swconfig')
        
    return(BIOSpath)
 

def PostCode():
    #Function created to use TTK API instead of scratchpad from BIOS
    cfg = ConfigManager()
    pltObj = cfg.LoadXml(r"C:\SVSHARE\User_Apps\TTK2\Xml Configurations\MiniPort80_smbus.xml")

    try:
        p80Interface = Port_80()
        if p80Interface:
            p80Interface.OpenPort80Interface(pltObj)
            #p80Interface.OpenPort80Interface()
            p= p80Interface.Read()
            # print(p[0].Result[0])
            pcode = p[0].Result[0]
            return(hex(pcode))
    except:
        plog('warn','Could Not Read Post Code')

 

def unlock(project):
    
    # time.sleep(5)
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
            os.rename(log_file, '%s\\%s_%s' % (log_file.split(os.path.basename(log_file))[0], 
            now.strftime('%Y_%m_%d_%H_%M_%S'),os.path.basename(log_file)))
            open(log_file,'w')
        else:
            print('Using current log file: %s' % log_file)
        
    
    else:
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
                                                    If left blank it will read from ini file.''',
                                                default = None, type = str)
    parser.add_argument('-p', '--project',help = '''Project is used to build path where BIOS will be copied to share drive. 
                                                    If left blank it will read project from env var.
                                                    List of valid projects in ini file. (Example: ICX)''',
                                                default = None, type = str)
    parser.add_argument('-s', '--cpustep',help = '''Cpu step is used when copying BIOS to share drive. 
                                                    If left blank script will not work.
                                                    (Example: D3_XCC)''',
                                                default = None, type = str)
    parser.add_argument('-f', '--flash',help = '''Argument is used to trigger BIOS flash
                                                    If not used flash feature will be skipped''',
                                                action = 'store_true')
    parser.add_argument('-t', '--task',help = '''The Task or software config is used for BIOS flashing.
                                                    If left blank it will be read from SwConfig env var''',
                                                default = None, type = str)
    parser.add_argument('-c', '--copy',help = '''Argument is used to trigger the copy of both Binary and Patch to share drive.
                                                    CPUID must be used for path creations to copy files over''',
                                                default = None, type = str)
    parser.add_argument('-k', '--knobs',help = '''Argument used to trigger ifwistitcher.''',
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
    
    create_log_file()
    #logs beginning of run
    plog('notify','\n\n*****Patch Regression Has Started*****\n')

    global new_bios_path
    
    an_paths = config['AN_PATHS']
    new_bios_path = an_paths['new_bios_path']
    
    ver = sys.version
    if '2.7' in ver:
        new_bios_path = new_bios_path.replace('python37','python27')

    if args.project == None:
        project = os.environ['SiliconFamily']
    else:
        project = args.project

    if args.bios != None:
        
        if args.ucode != None:
    
            if os.path.isfile(args.bios) == True and os.path.isfile(args.ucode) == True:
                #Get project from user or env var
                    #Check if project is valid from ini file
                if args.project != None:
                    proj = ''
                    projects = config['PROJECTS']
                    for key in projects:
                        if key.upper() == project.upper():
                            plog('notify','Project: %s' % key.upper())
                            proj = key.upper()
                    if proj == '':
                        plog ('error', 'Invalid Project')
                        sys.exit('Project: %s' % args.project.upper())

                #Remove old bios from out dir and then update BIOS
                removeOldBios()
                updatedBin = ucodeUpdate(args.bios, args.ucode)
                    
                
                if args.copy != None and if len(args.copy) >= 5:   
                    if args.cpustep != None:
                        newPath = copyBin(updatedBin)

                        if args.knobs == True:
                            stitchedBiosPth = knobStitch(project, newPath)
                        else:
                            plog('notify', 'Knob Stitch is disabled')
                    else:
                        plog('error','No CPU Step provided')
                
                else:
                    plog('notify','Incorrect or no CPUID provided')
                        
                        
                
            
            else:
                plog('error','Invalid BIOS or Ucode path')
        else:
            plog('warn','Ucode is missing')
        
        if args.flash == True:  
            if args.copy == None:
                stitchedBiosPth = args.bios
            else:
                if args.knobs == False:
                    plog('info','BIOS will be copied to share drive')
                    stitchedBiosPth = getPath(newPath)
                    plog('info','New path: ' + stitchedBiosPth)
                else:
                    plog('info','Using BIOS from knobStitch')
            if args.task == None or args.task == '':
                task = os.environ['SWConfig']
            else:
                task = args.task

            flashingBios(stitchedBiosPth, task)
            
        else:
            plog('notify','Flashing disabled')
    else:
        plog('warn','BIOS is missing')
    
    if args.unlock == True:
        # print(project)
        unlock(project)
    else:
        plog('notify','Unlocker disabled')
