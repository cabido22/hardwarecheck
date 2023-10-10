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
        print('Ucode Path: %s\\%s\\%s' % (root, project, patch))
    
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
    parser.add_argument('-cpu', '--cpustep',help = '''Cpu step is used when copying BIOS to share drive. 
                                                    If left blank it will read CpuStep from env var .''',
                                                default = None, type = str)
    parser.add_argument('-f', '--flash',help = '''Argument is used to trigger BIOS flash''',
                                                action = 'store_true')
    parser.add_argument('-c', '--copy',help = '''Argument is used to trigger the copy of bin and patch to share drive''',
                                                action = 'store_true')

    args = parser.parse_args()
    if args.bios != None and args.ucode != None:
        if os.path.isfile(args.bios) == True and os.path.isfile(args.ucode) == True:
            args.new_bios_path = removeOldBios()
            updatedBin = ucodeUpdate(args.bios, args.ucode)
            if args.flash == True:   
                flashBios(updatedBin)
            else:
                print('\nFlashing disabled')
            if args.copy == True:   
                copyBin(updatedBin)
                # args.new_bios_path = removeOldBios()
            else:
                print('\nCopying file is disabled')
        else:
            print('\nInvalid BIOS or Ucode path')
    else:
        print('BIOS or Ucode is missing')
        
