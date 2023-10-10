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
    project = ''
    cpustep = ''
    binName = ''
    updatedBin = ''

vars = VARIABLES()  

def listBins():
    #check if binary exists in the out path of xmlcli\out
    fullPth = None
    fle = os.listdir(vars.new_bios_path)
    for x in fle:
        if x.endswith('.bin'):
            fullPth = (vars.new_bios_path +'\\'+ x)
    # if binary does not exist then use the binary provided in cmd line
    if fullPth == None:
        return(args.bios)
    # if a binary exists then use the modified one in xmlcli\out 
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
        print('#### %s \n#####' % fp)
        if fp != bios_path:
            l = fp.split('_')[0:-2]
            fullPath = r'%s.bin' % "_".join(l)
            os.rename(fp, fullPath)
        else:
            # if no pathces were removed from BIOS then use the original bios
            fullPath = bios_path
        # print('\n### %s ###' % fullPath)
        # print('### %s ###' % bios_path)

    except:
        print('\nNo patch detected in BIOS')
        
    try:
        # Try to update new BIOS with new patch from argument
        print('\nUpdating Ucode')
        print('\n### %s ###' % fullPath)
        print('### %s ###' % bios_path)
        cli.ProcessUcode("update", fullPath.strip(), ucode_path)
        # Get new BIOS from directory
        print('\n#### after update of bios \n#####')
        vars.updatedBin = listBins()
        print('\nUpdated Bios: %s' % vars.updatedBin)
   
    except:
        print('\nError in Ucode update')
        
    return(vars.updatedBin)
    
        
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
    
    # if args.project == None or args.project == '':
        # project = os.environ['SiliconFamily']
    # else:
        # project = args.project
    
    # if args.step == None or args.step == '':
        # cpustep = os.environ['CpuStep']
    # else:
        # cpustep = args.step
    
    
    fullpatchname = args.ucode.split('\\')[-1]
    patch = fullpatchname.split('.')[0]
    
    if os.path.exists('%s\\%s\\%s\\%s' % (root, vars.project, vars.cpustep, patch)) == False:
        os.makedirs('%s\\%s\\%s\\%s' % (root, vars.project, vars.cpustep, patch))
    else:
        print('\nUcode Patch path exists')
        print('Ucode Path: %s\\%s\\%s\\%s' % (root, vars.project, vars.cpustep, patch))
    
    newPath = '%s\\%s\\%s\\%s' % (root, vars.project, vars.cpustep, patch)
    vars.binName = '%s\\%s'% (newPath, fullPth.split('\\')[-1])
    print('##### \n%s \n#####' % vars.binName)
    ucodeName = '%s\\%s' % (newPath, fullpatchname)
    
    from shutil import copyfile
    try:
        if os.path.exists(vars.binName) == False:
            copyfile(fullPth, vars.binName)
            print('\nFile Copied to share drive')
        # print(fullPth)
        else:
            print('\nBinary File path exists: \n%s\nNo need to copy binary' % vars.binName)
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
        
        
def knobStitch():

    # python Y:\sv_hardware\Personal_Folders\Tommy\IfwiStitcher\IfwiStitcher.py 
    # -op KnobChange 
    # -m Offline 
    # -b L:\Cafe_FV\2_BIOS\CPX\CPX6\16.P77\WLYDINT.PB1.86B.WD.64.2020.30.3.03.0008_0016.P77_P0001d_LBG_SPS_CPX.bin 
    # -ki L:\Cafe_FV\Personal_Folders\tcasti1\CPX_SWConfigs\TargetConfig__CXP1.ini 
    # -o C:\python37\Lib\site-packages\pysvtools\xmlcli\out
    
    
    biosOutdir = r'\\amr\ec\proj\C2DG\CoreIP_IDC_AN_Sync\Cafe_FV\2_BIOS'
    root =  r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_SYNC\IDC\Utilities\Core-IP\SwConfigs'
    stitcher_path= r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_IDC_Sync\IDC\Utilities\Core-IP\IfwiStitcher'
    swconfigs = r'\\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_Sync\IDC\Utilities\Core-IP\BiosPackage\BinFiles\ICX\21WW16.1\D0'
    
    if args.knobs == False:
        print('No knobs path provided')
    else:
        #find latest version of ifwistitcher
        import os, glob
        latest_stitcher = max(glob.glob(os.path.join(stitcher_path, '*/')), key=os.path.getmtime)
        stitcher = '%s\\ifwistitcher.py' % latest_stitcher
        
        #build command to run ifwistitcher
        BIOSpath = ('%s\\%s\\%s' %(biosOutdir, vars.project, vars.cpustep))
        
        subprocess.run('python %s -op KnobChange -m Offline -b %s ki %s -o %s' % (stitcher, vars.binName, swconfigs, BIOSpath))
        # print('python %s -op KnobChange -m Offline -b %s ki %s -o %s' % (stitcher, vars.binName, swconfigs, BIOSpath))
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 
    '''
    Usage:
    This script will update the BIOS with the patch provided in the command line.
    You must provide the BIOS and Ucode for script to work.
    ''')
    parser.add_argument('-b', '--bios',help = '''BIOS path needs to be the full path to binary.''',
                                                type = str)
    parser.add_argument('-u', '--ucode',help = '''Ucode path needs to be full path to pdb file''',
                                                type = str)
    parser.add_argument('-p', '--project',help = '''Project is where BIOS will be copied. 
                                                    If left blank it will read project from env var .''',
                                                default = None, type = str)
    parser.add_argument('-f', '--flash',help = '''Argument is used to trigger BIOS flash''',
                                                action = 'store_true')
    parser.add_argument('-c', '--copy',help = '''Argument is used to trigger the copy of bin and patch to share drive''',
                                                action = 'store_true')
    parser.add_argument('-k', '--knobs',help = '''Path to BIOS knobs for each software config. 
                                                    if blank then this option will be skipped.''',
                                                default = None, type = str)
    parser.add_argument('-t', '--task',help = '''The project task is for software config. 
                                                    A task must be provided to flash bios .''',
                                                default = None, type = str)
    parser.add_argument('-s', '--step',help = '''Cpu step is used when copying BIOS to share drive. 
                                                    If left blank it will read CpuStep from env var .''',
                                                default = None, type = str)

    args = parser.parse_args()
    if args.bios != None and args.ucode != None:
        args.new_bios_path = removeOldBios()
        vars.updatedBin = ucodeUpdate(args.bios, args.ucode)
       
        if args.project == None or args.project == '':
            vars.project = os.environ['SiliconFamily']
        else:
            vars.project = args.project
            
        if args.step == None or args.step == '':
            vars.cpustep = os.environ['CpuStep']
        else:
            vars.cpustep = args.step
            
        if args.flash == True and args.task == True: 
            flashBios(vars.updatedBin)
        else:
            print('\nFlashing disabled or SW Config not provided')
            
        if args.copy == True:   
            copyBin(vars.updatedBin)
            # args.new_bios_path = removeOldBios()
        else:
            print('\nCopying file is disabled')
        if args.knobs == True:
            knobStitch()
        else:
            print('\nKnob stitching disabled')
    else:
        print('\nInvalid BIOS or Ucode path')
        
    
            
        
