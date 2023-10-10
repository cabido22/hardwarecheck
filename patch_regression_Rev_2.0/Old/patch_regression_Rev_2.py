#!/usr/bin/python3
################################################################################
#  PatchRegression
#  By Tommy Castilleja
#
#
#  This script is to automatically perform regressions
#   1. Remove old pathces stitched in BIOS and stitches new patch
#   2. Copies ucode and stitched bios to share drive in ini file
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
import time
import subprocess
time.sleep(.5)
import glob

import configparser
config = configparser.ConfigParser()
print(os.path.realpath(sys.argv[0]))
script_path = os.path.realpath(sys.argv[0])
ini_path = '%s\\patch_regression.ini' % '\\'.join(script_path.split('\\')[0:-1])
config.read(ini_path)

# project = os.environ['SiliconFamily']

import namednodes
namednodes.settings.PROJECT="icelakex"
sv = namednodes.sv


def listBins():
    an_paths = config['AN_PATHS']
    new_bios_path = an_paths['new_bios_path']
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
    an_paths = config['AN_PATHS']
    new_bios_path = an_paths['new_bios_path']
    
    import pysvtools.xmlcli.XmlCli as cli
    
    # Try to remove old patches from BIOS in argument 
    try:
        secHeader('Removing Old Ucode patches')
        cli.ProcessUcode("deleteall", bios_path)
        secFooter('Remove Old Ucode patches')
    except:
        print(' \033[1;31;40m \nError in removing old patches from binary \033[1;37;40m')
      
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
        print('\033[1;31;40m \nNo patch detected in BIOS \033[1;37;40m')
        
    try:
        # Try to update new BIOS with new patch from argument
        secHeader('Ucode Patch Updating')
        cli.ProcessUcode("update", fullPath.strip(), ucode_path)
        # Get new BIOS from directory
        updatedBin = listBins()
        print('\nUpdated Bios: %s' % updatedBin)
        secFooter('Ucode Patch Update')
        return(updatedBin)
    except:
        print(' \033[1;31;40m \nError in Ucode update \033[1;37;40m')
        
    
        
def removeOldBios():
    #Remove old bios from xmlcli folder before creating new bios
    an_paths = config['AN_PATHS']
    new_bios_path = an_paths['new_bios_path']
    fle = os.listdir(new_bios_path)
    secHeader('Remove Old Bios')
    for x in fle:
        if x.endswith('.bin'):
            os.remove('%s\\%s' % (new_bios_path,x))
            
    secFooter('Remove Old Bios')
            
    
def flashingBios(stitchedBiosPth, task):

    an_paths = config['AN_PATHS']
    
    #Use latest bios package to flash bios. using hardcoded biospackage path
    # latest_stitcher = max(glob.glob(os.path.join(an_paths['BiosPackage_Path'], '*/')), key=os.path.getmtime)
    flasher = '%s\\BiosPackage.py' % an_paths['BiosPackage_Path']
    
    latest_file = ''
    
    if args.copy == False:
        flashBIOS = args.bios
        print('\033[1;36;40m \nUsing Raw BIOS provided \033[1;37;40m')
    else:
        
        #get latest BIOS from directory
        list_of_files = glob.glob('%s\\*' % stitchedBiosPth)
        latest_file = max(list_of_files, key=os.path.getmtime)
        
        # print('\033[1;36;40m \nUsing new BIOS with correct SwConfig to flash \033[1;37;40m')
        # #rename latest bios with task provided
        # chop = latest_file.split('_')
        # chop.remove(chop[-2])
        # chop.insert(-1, task)
        # flashBIOS = '_'.join(chop)
        
        print('\033[1;36;40m \nUsing new BIOS with correct SwConfig to flash \033[1;37;40m')
        #rename latest bios with task provided
        chop = latest_file.split('_')
        chop.remove(chop[-2])
        chop.insert(-1, task)
        flashBIOS = '_'.join(chop)
        
    print ('\033[1;33;40m \nBIOS to be Flashed: %s \033[1;37;40m' % flashBIOS)
    if os.path.isfile(flashBIOS) == True:
        
   
        try:
            # print('\nFlashing BIOS')
            print('\nflash command: ' + flasher + ' -b ' + flashBIOS)

            os.system(flasher + ' -b ' + flashBIOS)

        except:
            print('Error with flashing BIOS')
            
    else:
        print('\033[1;31;40m \nInvalid BIOS \033[1;37;40m')

    
def copyBin(fullPth):
    import shutil
    from pathlib import Path as p
    
    #Read ini file to get ucod directory
    an_paths = config['AN_PATHS']
    ucode_dir = an_paths['ucode_dir']
    
    if args.project == None or args.project == '':
        project = os.environ['SiliconFamily']
    else:
        project = args.project
    
    if args.cpustep == None or args.cpustep == '':
        cpustep = os.environ['CpuStep']
    else:
        cpustep = args.cpustep
    
    
    fullpatchname = args.ucode.split('\\')[-1]
    patch = fullpatchname.split('.')[0]
    
    if os.path.exists('%s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch)) == False:
        os.makedirs('%s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch))
    else:
        print('\nUcode Patch path exists')
        print('Ucode Path: %s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch))

    newPath = '%s\\%s\\%s\\%s' % (ucode_dir, project, cpustep, patch)
    binName = '%s\\%s'% (newPath, fullPth.split('\\')[-1])
    ucodeName = '%s\\%s' % (newPath, fullpatchname)
    
    from shutil import copyfile
    try:
        if os.path.exists(binName) == False:
            secHeader('Copying binary to Share Drive')
            copyfile(fullPth, binName)
            secFooter('Copying binary')

        else:
            print('\033[1;33;40m \nBinary File path exists: \n%s\nNo need to copy binary \033[1;37;40m' % binName)
    except:
        print ('\033[1;31;40m \nError in copying bin files to dir \033[1;37;40m')
        
    try:
        if os.path.exists(ucodeName) == False:
            secHeader('Copying Patch File to Share Drive')
            copyfile(args.ucode, ucodeName)
            print('\nPatch file:\n%s' % ucodeName)
            secFooter('Copying Patch File to Share Drive')
        else:
            # print('\nPatch file exists:\n%s\nNo need to copy patch' % ucodeName)
            print('\033[1;33;40m \nPatch file exists:\n%s\nNo need to copy patch \033[1;37;40m' % ucodeName)
    except:
        print ('\033[1;31;40m \nError in copying patch file to dir \033[1;37;40m')
    
       
    return(project, binName)
        
 
def secHeader(section):
    print('\n####################################')
    print('\n##### %s has started #####' % section)
    print('\n####################################')
    
    
def secFooter(section):
    print('\033[1;32;40m \n=== %s was successful === \033[1;37;40m \n' % section)

 
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
    
    try:
        #find latest version of ifwistitcher. Using hardcoded stitcher_path instead
        # latest_stitcher = max(glob.glob(os.path.join(ifwistitcher_path, '*/')), key=os.path.getmtime)
        stitcher = '%s\\ifwistitcher.py' % stitcher_path
    except:
        print('\033[1;31;40m \nTrouble locating latest ifwistitcher \033[1;37;40m')
        
    step = getCpustep()
    cpustep = args.cpustep
    
    try:
        #find lastest swconfig
        latest_swconfigs = max(glob.glob(os.path.join(SwConfig_Path, '*/')), key=os.path.getmtime)
        swconfig = '%s%s\\%s' % (latest_swconfigs, project, step)

    except:
        print('\033[1;31;40m Trouble locating latest SwConfigs \033[1;37;40m')
    
    if os.path.exists(swconfig) == True:
        
        fullpatchname = args.ucode.split('\\')[-1]
        patch = fullpatchname.split('.')[0]
        #build command to run ifwistitcher
        BIOSpath = ('%s\\%s\\%s\\%s' % (biosOutdir, project, cpustep, patch))
        if os.path.exists(BIOSpath) == False:
            os.makedirs(BIOSpath)
            print('\nDirectory created for ifwistitcher')
        else:
            print('\nBIOS out path exists and ready for ifwistitcher')
        
        #Check if binaries already exist in new path
        fullPth = None
        fle = os.listdir(BIOSpath)
        for x in fle:
            if x.endswith('.bin'):
                fullPth = (BIOSpath +'\\'+ x)
        if fullPth == None:
            try:
                      
                secHeader('IfwiStitcher')
                print('\npython %s -op KnobChange -m Offline -b %s -ki %s -o %s\n' % (stitcher, newPath, swconfig, BIOSpath))
                
                subprocess.run('python %s -op KnobChange -m Offline -b %s -ki %s -o %s' % (stitcher, newPath, swconfig, BIOSpath))
                # secFooter('IfwiStitcher')
            except:
                print('\033[1;31;40m \nKnob stitching failed \033[1;37;40m')
            
        else:
            print('\033[1;33;40m \nBinaries already exist for this Patch.\n%s\nIfwiStitcher will be skipped \033[1;37;40m' % BIOSpath)
    
    else:
        print ('\033[1;31;40m \nInvalid path to swconfig \033[1;37;40m')
        
    return(BIOSpath)
    

def unlock():
    
    sv.refresh()
    time.sleep(5)
    xwrapper_post_code = 0xf6000000
    satellite_post_code = 0xf5000000
    stuck = 0x0
    counter = 0
        
    unlocker = config['AN_UNLOCK_PATH']
   
    while counter <= 20:
        time.sleep(int(unlocker['sleep']))
        post_code = sv.socket0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
        print('\nPost Code: %s' % post_code)
        if post_code == stuck and counter >= int(unlocker['times_at_postcode']):
            print ('\033[1;31;40m \nPlatform is stuck at Post Code: %s \033[1;37;40m' % post_code)
            print ('\033[1;33;40m \nUnlocker will be skipped \033[1;37;40m')
            break
            return('Unlocker Failed')
        else:    
            if post_code != stuck:
                counter = 0
                stuck = post_code
            if post_code == xwrapper_post_code or post_code == satellite_post_code:
                print('\033[1;32;40m \nPost Code had been reached: %s\n \033[1;37;40m' % post_code)
                
                secHeader('Unlocker')
                subprocess.run(unlocker['unlocker'])
                secFooter('Unlocker Automation')
                break
            
            else:
                counter += 1
                # print ('counter: %s' % counter)
    
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 
    '''
    Usage:
    This script will update the BIOS with the patch provided in the command line.
    You must provide the BIOS and Ucode for script to work.
    ''')
    parser.add_argument('-b', '--bios',help = '''BIOS path needs to be the full path to binary.''',
                                                default = None, type = str)
    parser.add_argument('-u', '--ucode',help = '''Ucode path needs to be full path to pdb file''',
                                                default = None, type = str)
    parser.add_argument('-p', '--project',help = '''Project is where BIOS will be copied. 
                                                    If left blank it will read project from env var.
                                                    (Example: ICX)''',
                                                default = None, type = str)
    parser.add_argument('-s', '--cpustep',help = '''Cpu step is used when copying BIOS to share drive. 
                                                    If left blank it will read CpuStep from env var .''',
                                                default = None, type = str)
    parser.add_argument('-f', '--flash',help = '''Argument is used to trigger BIOS flash''',
                                                action = 'store_true')
    parser.add_argument('-t', '--task',help = '''The project task is for software config. 
                                                    A task must be provided to flash bios.
                                                    If left blank it will be read from SwConfig env var''',
                                                default = None, type = str)
    parser.add_argument('-c', '--copy',help = '''Argument is used to trigger the copy of bin and patch to share drive''',
                                                action = 'store_true')
    parser.add_argument('-k', '--knobs',help = '''Path to BIOS knobs for each software config. 
                                                    if blank then this option will be skipped.''',
                                                action = 'store_true')
    parser.add_argument('-ul', '--unlock',help = '''Path to BIOS knobs for each software config. 
                                                    if blank then this option will be skipped.''',
                                                action = 'store_true')

    args = parser.parse_args()
    if args.bios != None and args.ucode != None:
    
        if os.path.isfile(args.bios) == True and os.path.isfile(args.ucode) == True:

            if args.cpustep != None:
            
                removeOldBios()
                updatedBin = ucodeUpdate(args.bios, args.ucode)
                    
                if args.copy == True:   
                    project, newPath = copyBin(updatedBin)

                else:
                    print ('\033[1;36;40m \nCopying file is disabled \033[1;37;40m')
                    
                if args.knobs == True:
                    stitchedBiosPth = knobStitch(project, newPath)
                else:
                    print ('\033[1;36;40m \nKnob Stitch is disabled \033[1;37;40m')
                    
                if args.flash == True:  
                    if args.copy == False:
                        stitchedBiosPth = args.bios
                    else:
                        print('\nBIOS will be copied to share drive')
                    if args.task == None or args.task == '':
                        task = os.environ['SWConfig']
                    else:
                        task = args.task
       
                    flashingBios(stitchedBiosPth, task)
                    
                else:
                    print ('\033[1;36;40m \nFlashing disabled \033[1;37;40m')
            
            else:
                print('\033[1;31;40m \nNo CPU Step provided \033[1;37;40m')
        
        else:
            print ('\033[1;31;40m \nInvalid BIOS or Ucode path \033[1;37;40m')
    
    else:
        print ('\033[1;31;40m \nBIOS or Ucode is missing \033[1;37;40m')
    
    if args.unlock == True:
        unlock()
    else:
        print ('\033[1;36;40m \nUnlocker disabled \033[1;37;40m')

