#!/usr/bin/python3
######################################################
#  PatchRegression
#  By Tommy Castilleja
#
#
#  This script is to automatically perform regressions
#
#
######################################################

from __future__ import print_function
from __future__ import absolute_import
import argparse
import os
os.system("")
import time
import subprocess
time.sleep(10)
import glob

class VARIABLES:
    new_bios_path = r'c:\python37\lib\site-packages\pysvtools\xmlcli\out'

vars = VARIABLES()  

def listBins():

    fullPth = None
    fle = os.listdir(vars.new_bios_path)
    for x in fle:
        if x.endswith('.bin'):
            fullPth = (vars.new_bios_path +'\\'+ x)
    if fullPth == None:
        return(args.bios)
    else:
        return(fullPth)



def ucodeUpdate(bios_path, ucode_path):
    import pysvtools.xmlcli.XmlCli as cli
    
    # Try to remove old patches from BIOS in argument 
    try:
        print('\nRemoving old ucode patches')
        cli.ProcessUcode("deleteall", bios_path)
        
        # Rename new BIOS with now patches 
        fp = listBins()
                  
        if fp != bios_path:
            l = fp.split('\\')[-1].split('_',5)[0:5]
            binName = ucode_path.split('\\')[-1]
            strippedBin = r'%s.bin' % ("_".join(l))
            fullPath = '%s\\%s' % (vars.new_bios_path, strippedBin)
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
   
    except:
        print(' \033[1;31;40m \nError in Ucode update \033[1;37;40m')
        
    return(updatedBin)
    
        
def removeOldBios():
    fle = os.listdir(vars.new_bios_path)
    for x in fle:
        if x.endswith('.bin'):
            secHeader('Remove Old Bios')
            os.remove('%s\\%s' % (vars.new_bios_path,x))
            secFooter('Remove Old Bios')
            
            
    
def flashingBios(stitchedBiosPth, task):
    # nb = os.listdir(vars.new_bios_path)
    # for x in nb:
        # if x.endswith('.bin'):
            # stitchedBiosPth = (vars.new_bios_path +'\\'+ x)

    #Use bios package to flash bios
    flash = r'\\amr.corp.intel.com\ec\proj\ha\sa\sa_laboratory\SA_FM_SYNC\IDC\Utilities\Core-IP\BiosPackage'
    latest_stitcher = max(glob.glob(os.path.join(flash, '*/')), key=os.path.getmtime)
    flasher = '%s\\BiosPackage.py' % latest_stitcher
    
    latest_file = ''
    
    if args.copy == False:
        flashBIOS = args.bios
        print('\n##### Flashing BIOS provided')
    else:
        stitchedBiosPth
        list_of_files = glob.glob('%s\\*' % stitchedBiosPth)
        latest_file = max(list_of_files, key=os.path.getmtime)
    
        chop = latest_file.split('_')
        chop.remove(chop[-3])
        chop.insert(-2, task)
        flashBIOS = '_'.join(chop)
        
    print ('\n##### BIOS: \n%s' % flashBIOS)
    if os.path.isfile(flashBIOS) == True:
        
   
        try:
            print('\nFlashing BIOS')
            print('\nflash command: ' + flasher + ' -b ' + flashBIOS)
            # subprocess.run(flasher + ' -b ' + flashBIOS)
            
            os.system(flasher + ' -b ' + flashBIOS)
            
        except:
            print('Error with flashing BIOS')
            
    else:
        print('\033[1;31;40m \nInvalid BIOS \033[1;37;40m')

    
def copyBin(fullPth):
    import shutil
    from pathlib import Path as p
    
    root = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync\Cafe_FV\1_uCode_Patches'
    
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
    
    if os.path.exists('%s\\%s\\%s\\%s' % (root, project, cpustep, patch)) == False:
        os.makedirs('%s\\%s\\%s\\%s' % (root, project, cpustep, patch))
    else:
        print('\nUcode Patch path exists')
        print('Ucode Path: %s\\%s\\%s\\%s' % (root, project, cpustep, patch))

    newPath = '%s\\%s\\%s\\%s' % (root, project, cpustep, patch)
    binName = '%s\\%s'% (newPath, fullPth.split('\\')[-1])
    ucodeName = '%s\\%s' % (newPath, fullpatchname)
    
    from shutil import copyfile
    try:
        if os.path.exists(binName) == False:
            secHeader('Copying binary to Share Drive')
            copyfile(fullPth, binName)
            secFooter('Copying binary')
        # print(fullPth)
        else:
            print('\nBinary File path exists: \n%s\nNo need to copy binary' % binName)
    except:
        print ('\033[1;31;40m \nError in copying bin files to dir \033[1;37;40m')
        
    try:
        if os.path.exists(ucodeName) == False:
            secHeader('Copying Patch File to Share Drive')
            copyfile(args.ucode, ucodeName)
            print('\nPatch file:\n%s' % ucodeName)
            secFooter('Patch File')
        else:
            print('\nPatch file exists:\n%s\nNo need to copy patch' % ucodeName)
    except:
        print ('\033[1;31;40m \nError in copying patch file to dir \033[1;37;40m')
    
    try:
        removeOldBios()
        
    except:
        print ('\033[1;31;40m \nCould not remove old BIOS \033[1;37;40m')
        
    return(project, binName)
        
 
def secHeader(section):
    print('\n####################################')
    print('\n##### %s has started #####' % section)
    print('\n####################################')
    
    
def secFooter(section):
    # print('\n=====================================')
    print('\033[1;32;40m === %s was successful === \033[1;37;40m \n' % section)
    # print('\n=====================================')
    
 
def knobStitch(project, newPath):

    # python Y:\sv_hardware\Personal_Folders\Tommy\IfwiStitcher\IfwiStitcher.py 
    # -op KnobChange 
    # -m Offline 
    # -b L:\Cafe_FV\2_BIOS\CPX\CPX6\16.P77\WLYDINT.PB1.86B.WD.64.2020.30.3.03.0008_0016.P77_P0001d_LBG_SPS_CPX.bin 
    # -ki L:\Cafe_FV\Personal_Folders\tcasti1\CPX_SWConfigs\TargetConfig__CXP1.ini 
    # -o C:\python37\Lib\site-packages\pysvtools\xmlcli\out
    # example = L:\Cafe_FV\2_BIOS\ICX\D2_XCC
    
    
    biosOutdir = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync\Cafe_FV\2_BIOS'
    root =  r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_Sync\IDC\Utilities\Core-IP\SwConfigs'
    stitcher_path= r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_IDC_Sync\IDC\Utilities\Core-IP\IfwiStitcher'
    swconfigs = r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_Sync\IDC\Utilities\Core-IP\BiosPackage\BinFiles\ICX\21WW16.1\D0'
    
    binPth = updatedBin.split('\\')[-1]
    
    if args.knobs == False:
        print ('\033[1;31;40m No knobs path provided \033[1;37;40m')
    else:
        #find latest version of ifwistitcher

        latest_stitcher = max(glob.glob(os.path.join(stitcher_path, '*/')), key=os.path.getmtime)
        stitcher = '%s\\ifwistitcher.py' % latest_stitcher
        
        # if args.task == None:
            # task = os.environ['SWConfig']
        # else:
            # task = args.task
            
        if args.cpustep == None or args.cpustep == '':
            cpustep = os.environ['CpuStep']
        else:
            cpustep = args.cpustep
            
        #find lastest swconfig
        latest_swconfigs = max(glob.glob(os.path.join(root, '*/')), key=os.path.getmtime)
        swconfig = '%s%s\\%s' % (latest_swconfigs, project, cpustep)
        
        #using swconfigs will use hard coded path. Using swconfig will use path specified 
        if os.path.exists(swconfig) == True:
            
            #build command to run ifwistitcher
            BIOSpath = ('%s\\%s\\%s' %(biosOutdir, project, cpustep))
            if os.path.exists(BIOSpath) == False:
                os.makedirs(BIOSpath)
                print('\nDirectory created for ifwistitcher')
            else:
                print('\nBIOS path exists and ready for ifwistitcher')
            secHeader('IfwiStitcher')
            print('\npython %s -op KnobChange -m Offline -b %s -ki %s -o %s\n' % (stitcher, newPath, swconfigs, BIOSpath))
            subprocess.run('python %s -op KnobChange -m Offline -b %s -ki %s -o %s' % (stitcher, newPath, swconfigs, BIOSpath))
            # print('python %s -op KnobChange -m Offline -b %s ki %s -o %s' % (stitcher, vars.binName, swconfigs, BIOSpath))
            secFooter('IfwiStitcher')
            
        else:
            print ('\033[1;31;40m \nInvalid path to swconfigs \033[1;37;40m')
            
        return(BIOSpath)
        
        
        
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
                                                    If left blank it will read project from env var .''',
                                                default = None, type = str)
    parser.add_argument('-s', '--cpustep',help = '''Cpu step is used when copying BIOS to share drive. 
                                                    If left blank it will read CpuStep from env var .''',
                                                default = None, type = str)
    parser.add_argument('-f', '--flash',help = '''Argument is used to trigger BIOS flash''',
                                                action = 'store_true')
    parser.add_argument('-c', '--copy',help = '''Argument is used to trigger the copy of bin and patch to share drive''',
                                                action = 'store_true')
    parser.add_argument('-k', '--knobs',help = '''Path to BIOS knobs for each software config. 
                                                    if blank then this option will be skipped.''',
                                                action = 'store_true')
    parser.add_argument('-t', '--task',help = '''The project task is for software config. 
                                                    A task must be provided to flash bios .''',
                                                default = None, type = str)

    args = parser.parse_args()
    if args.bios != None or args.bios != '' and args.ucode != None or args.ucode != '':
    
        if os.path.isfile(args.bios) == True and os.path.isfile(args.ucode) == True:

            if args.cpustep != None:
            
                args.new_bios_path = removeOldBios()
                updatedBin = ucodeUpdate(args.bios, args.ucode)
                    
                if args.copy == True:   
                    project, newPath = copyBin(updatedBin)
                    # args.new_bios_path = removeOldBios()
                else:
                    print('\nCopying file is disabled')
                    
                if args.knobs == True:
                    stitchedBiosPth = knobStitch(project, newPath)
                else:
                    print('\nKnob Stitch is disabled')
                    
                if args.flash == True:  
                    if args.copy == False:
                        stitchedBiosPth = args.bios
                    else:
                        print('\nBIOS will be copied to share drive')
                    if args.task == None or args.task == '':
                        task = os.environ['SWConfig']
                    else:
                        task = args.task
                    # print('BIOS PATH: %s' % stitchedBiosPth)       
                    flashingBios(stitchedBiosPth, task)
                    
                else:
                    print('\nFlashing disabled')
                
            
            else:
                print('\033[1;31;40m \nNo CPU Step provided \033[1;37;40m')
        
        else:
            print ('\033[1;31;40m \nInvalid BIOS or Ucode path \033[1;37;40m')
    
    else:
        print ('\033[1;31;40m \nBIOS or Ucode is missing \033[1;37;40m')
    
    # print('\033[1;37;40m ') #Revert color back to normal
