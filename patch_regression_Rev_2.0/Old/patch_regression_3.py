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
import time
import subprocess
time.sleep(10)

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
        
        # if fp != bios_path:
            # l = fp.split('\\')[-1].split('_',5)[0:5]
            # binName = ucode_path.split('\\')[-1]
            # strippedBin = r'%s_%s.bin' % ("_".join(l), binName)
            # fullPath = '%s\\%s' % (vars.new_bios_path, strippedBin)
            # os.rename(fp, fullPath)
                    
        if fp != bios_path:
            l = fp.split('\\')[-1].split('_',5)[0:5]
            binName = ucode_path.split('\\')[-1]
            strippedBin = r'%s.bin' % ("_".join(l))
            fullPath = '%s\\%s' % (vars.new_bios_path, strippedBin)
            os.rename(fp, fullPath)
        else:
            # if no pathces were removed from BIOS then use the original bios
            fullPath = bios_path
        print('\n### %s ###' % fullPath)
        print('### %s ###' % bios_path)

    except:
        print('\nNo patch detected in BIOS')
        
    try:
        # Try to update new BIOS with new patch from argument
        print('\nUpdating Ucode')
        cli.ProcessUcode("update", fullPath.strip(), ucode_path)
        # Get new BIOS from directory
        updatedBin = listBins()
        print('\nUpdated Bios: %s' % updatedBin)
   
    except:
        print('\nError in Ucode update')
        
    return(updatedBin)
    
        
def removeOldBios():
    fle = os.listdir(vars.new_bios_path)
    for x in fle:
        if x.endswith('.bin'):
            os.remove('%s\\%s' % (vars.new_bios_path,x))
            
            
    
def flashBios(fullPth):
    # nb = os.listdir(vars.new_bios_path)
    # for x in nb:
        # if x.endswith('.bin'):
            # fullPth = (vars.new_bios_path +'\\'+ x)
            
    print(fullPth)
    #Use bios package to flash bios
    flash = r'\\amr.corp.intel.com\ec\proj\ha\sa\sa_laboratory\SA_FM_SYNC\IDC\Utilities\Core-IP\BiosPackage\21.09.22.1\BiosPackage.py'
    try:
        print('\nFlashing BIOS')
        print('\nflash command: ' + flash + ' -b ' + fullPth)
        # subprocess.run(flash + ' -b ' + fullPth)
        
        os.system(flash + ' -b ' + fullPth)
        
    except:
        print('Error with flashing BIOS')
        
    try:
        print('\nCopying BIOS to share drive')
        copyBin(fullPth)
    except:
        print('\nCould not copy file to directory')
    
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
            copyfile(fullPth, binName)
            print('\nFile Copied to share drive')
        # print(fullPth)
        else:
            print('\nBinary File path exists: \n%s\nNo need to copy binary' % binName)
    except:
        print ('\nError in copying bin files to dir')
        
    try:
        if os.path.exists(ucodeName) == False:
            copyfile(args.ucode, ucodeName)
            print('\nPatch file copied to new directory:\n%s' % ucodeName)
        else:
            print('\nPatch file exists:\n%s\nNo need to copy patch' % ucodeName)
    except:
        print('\nError in copying patch file to dir')
    
    try:
        removeOldBios()
        
    except:
        print('\nCould not remove old BIOS')
        
    return(project, binName)
        
        
def knobStitch(project, newPath):

    # python Y:\sv_hardware\Personal_Folders\Tommy\IfwiStitcher\IfwiStitcher.py 
    # -op KnobChange 
    # -m Offline 
    # -b L:\Cafe_FV\2_BIOS\CPX\CPX6\16.P77\WLYDINT.PB1.86B.WD.64.2020.30.3.03.0008_0016.P77_P0001d_LBG_SPS_CPX.bin 
    # -ki L:\Cafe_FV\Personal_Folders\tcasti1\CPX_SWConfigs\TargetConfig__CXP1.ini 
    # -o C:\python37\Lib\site-packages\pysvtools\xmlcli\out
    # example = L:\Cafe_FV\2_BIOS\ICX\D2_XCC
    
    
    biosOutdir = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync\Cafe_FV\2_BIOS'
    root =  r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_SYNC\IDC\Utilities\Core-IP\SwConfigs'
    stitcher_path= r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_IDC_Sync\IDC\Utilities\Core-IP\IfwiStitcher'
    swconfigs = r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_Sync\IDC\Utilities\Core-IP\BiosPackage\BinFiles\ICX\21WW16.1\D0'
    
    binPth = updatedBin.split('\\')[-1]
    
    if args.knobs == False:
        print('No knobs path provided')
    else:
        #find latest version of ifwistitcher
        import os, glob
        latest_stitcher = max(glob.glob(os.path.join(stitcher_path, '*/')), key=os.path.getmtime)
        stitcher = '%s\\ifwistitcher.py' % latest_stitcher
        
        if args.task == None:
            task = os.environ['SWConfig']
        else:
            task = args.task
            
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
            print('\nLaunching ifwistitcher')
            print('\npython %s -op KnobChange -m Offline -b %s -ki %s -o %s' % (stitcher, newPath, swconfigs, BIOSpath))
            subprocess.run('python %s -op KnobChange -m Offline -b %s -ki %s -o %s' % (stitcher, newPath, swconfigs, BIOSpath))
            # print('python %s -op KnobChange -m Offline -b %s ki %s -o %s' % (stitcher, vars.binName, swconfigs, BIOSpath))
            
        else:
            print('\nInvalid path to swconfigs')
            
        
        
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
    if args.bios != None and args.ucode != None:
        if os.path.isfile(args.bios) == True and os.path.isfile(args.ucode) == True:
            args.new_bios_path = removeOldBios()
            updatedBin = ucodeUpdate(args.bios, args.ucode)
            
            if args.copy == True:   
                project, newPath = copyBin(updatedBin)
                # args.new_bios_path = removeOldBios()
            else:
                print('\nCopying file is disabled')
                
            if args.knobs == True:
                knobStitch(project, newPath)
            else:
                print('\nKnob Stitch is disabled')
                
            if args.flash == True:   
                flashBios(updatedBin)
            else:
                print('\nFlashing disabled')
                
        else:
            print('\nInvalid BIOS or Ucode path')
    else:
        print('BIOS or Ucode is missing')
        
