from __future__ import print_function
import sys
import glob
import os
import argparse
import subprocess
import pdb

def CheckErrorCode(retcode, msg):
    if retcode != 0:
        print(msg)
        raise Exception(msg)

def InitialXmlCliStubMode():
    try:
        from pysvtools.xmlcli import XmlCli
        XmlCli.clb._setCliAccess("stub")
        return XmlCli
    except Exception as ex:
        print("Failed to initialize XmlCli")
        raise ex

def InitialXmlCliOnlineMode():
    try:
        from pysvtools.xmlcli import XmlCli as cli
        cli.clb._setCliAccess("ipc")
        return cli
    except Exception as ex:
        print("Failed to initialize XmlCli")
        raise ex

def RestoreKnobsToDefaultOnline():
    try:
        cli.CvLoadDefaults()
        print("Knobs were restore to default values successfully")
    except Exception as ex:
        print("Failed to restore knobs to default")
        raise ex

def exludeRemarks(linesList):
    tmp = []
    for line in linesList:
        if (not line.startswith((r"/", r"#", r";",r"["))):
            if len(line.split(r'/')) > 1:
                tmp.append(line.split(r'/')[0])
            elif len(line.split(r'#')) > 1:
                tmp.append(line.split(r'#')[0])
            elif len(line.split(r';')) > 1:
                tmp.append(line.split(r';')[0])
            else:
                tmp.append(line)
    return tmp


def getKnobsFromFile(swcfg):
    try:
        with open(swcfg) as knobfile:
            content = knobfile.readlines()
            content = exludeRemarks(content)
            content = [x.strip() for x in content]
            return ','.join(content)
    except Exception as ex:
        print("Failed to parse SwConfig knob file" + swcfg)
        raise ex
    finally:
        knobfile.close()


def StitchIfwiForSwConfigs():
    try:
        if args.knob_input == 'Disable':
            print("No knobs input file\\folder was received. Use --knob_input=<Path_To_Directory_Or_File>")
        swConfigLocations = []
        if os.path.isdir(args.knob_input):
            if args.mode.upper() == "ONLINE":
                ex = "Knobs input folder format is supported only for Offline mode. For Online mode, please provide full path to specific txt\\ini SwConfig definition file"
                print (ex)
                raise ex
            swConfigLocations = glob.glob(args.knob_input + r'\*.txt')
            swConfigLocations.extend(glob.glob(args.knob_input + r'\*.ini'))
        else:
            swConfigLocations.append(args.knob_input)
        cli.prs.ExitOnAlienKnobs = True #setting this to ensure CvProgKnobs will fail if unknown knobs are present
        for swcfg in swConfigLocations:
            knobfilename = swcfg.split('\\')[-1].rsplit('.', 1)[0]
            requiredKnobString = getKnobsFromFile(swcfg)
            if args.mode.upper() == "OFFLINE":
                if (os.path.isdir(args.out) != True):
                    try:
                        os.mkdir(args.out)
                    except OSError:
                        print("Creation of the directory %s failed" % args.out)
                retcode = cli.CvProgKnobs(requiredKnobString, args.bin,
                                BiosOut=args.out + '\\' +args.bin.split('\\')[-1].replace(".bin", "") + '_' + knobfilename + '.bin')
                CheckErrorCode(retcode, "Failed to program all knobs due to unknown knob. Check output for which knobs were not recognized.")
            else: #Online
                cli.CvProgKnobs(requiredKnobString) #does not need to check returncode. This flow thru online programming handles it gracefully.
                if args.reset != "Disable":
                    print("reset argument was provided. Going to reset target")
                    reset_script_path = args.reset.split(';')[0].split()
                    reset_script_args = args.reset.split(';')[1].split()
                    reset_script_path.extend(reset_script_args)
                    # reset_script_args.insert(0, reset_script_path)
                    subprocess.call(reset_script_path)
                DumpXmlKnobs()
    except Exception as ex:
        print("Failed to stitch IFWI with SwConfig knob sets")
        raise ex

def DumpXmlKnobs():
    if (os.path.isdir(r'C:\SVSHARE\Bios_Knob') != True):
        try:
            os.mkdir(r'C:\SVSHARE\Bios_Knob')
        except OSError:
            print("Creation of the directory %s failed" % args.out)
    print(r'Creating dump knobs file')
    try:
        if args.mode.upper() == "OFFLINE":
            cli.savexml(r'C:\SVSHARE\Bios_Knob\Bios_Knob.xml', args.bin)
        else:
            cli.savexml(r'C:\SVSHARE\Bios_Knob\Bios_Knob.xml')
        print(r'File was save successfully. file path: C:\SVSHARE\Bios_Knob\Bios_Knob.xml')
    except Exception as ex:
        print("Failed to save xml knobs")
        raise ex


def StitchIfwiWithNewPatch(file):

    try:
        if args.patch_input_file == 'Disable':
            ex = "No patch was provided. Please provide the following parameter: -p=<Full_Path_To_Patch>"
            print (ex)
            raise ex
        patch_name = args.patch_input_file.split('\\')[-1].split('.')[0]
        if args.mode.upper() == "ONLINE":
            result = cli.ProcessUcode("update", 0, args.patch_input_file, outPath=args.out + "\\" + file.split('\\')[-1].replace(".bin", "") + "" + patch_name + '.bin')
            if result:
                raise Exception('Failed to update patch')
        else: # Offline mode
            print('Going to remove the existing patches and update with a new one')
            binDir = r'C:\Temp\{0}'.format(args.bin.split('\\')[-1].replace(".bin", "") + "_delAllUc" + '.bin')
            # binDir = r'C:\Temp\{0}'.format(file.split('\\')[-1].replace(".bin", "") + "_" + 'delAllUc' + '.bin')
            if os.path.exists(binDir):
                os.remove(binDir)
            cli.ProcessUcode("deleteall", file, outPath=r'C:\Temp')
            list_of_bins = glob.glob(r'C:\Temp\*.bin')
            print(list_of_bins)
            for extension in list_of_bins:
                if file.split('\\')[-1].replace(".bin", "") in extension:
                    binDir = extension
            result = cli.ProcessUcode("update", binDir, args.patch_input_file, outPath=args.out + "\\" + file.split('\\')[-1].replace('_NewFit','').replace(".bin", "") + "_" + patch_name + '.bin')
            if result:
                raise Exception('Failed to update patch after deleting all existing patches from IFWI')
    except Exception as ex:
        print("Failed to stitch IFWI with new patch")
        print(ex)
        raise ex


def StitchIfwiForSwConfigsWithNewPatch():

    StitchIfwiForSwConfigs()
    bin_files = glob.glob(args.out + "\\*.bin")
    
    newlist_of_files = glob.glob('%s\\*' % args.out)
    binary = max(newlist_of_files, key=os.path.getctime)
    # for binary in bin_files:
    StitchIfwiWithNewPatch(binary)
    bin_count = len(glob.glob(args.out + "\\*.bin"))
    if bin_count > len(bin_files):
        os.remove(binary)


def parse_args():
    parser = argparse.ArgumentParser(description='Parsing all arguments')
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument('-o', '--out', help=r'The directory to which the new IFWI binaries will be saved. This argument is mandatory for Offline mode.',
                               default='Disable')
    requiredNamed.add_argument('-op', '--operation',
                               help=r'The operation needed. Available values: KnobChange\PatchChange\KnobAndPatchChange\RestoreKnobsToDefault\dumpxmlknobs',
                               required=True)
    requiredNamed.add_argument('-m', '--mode',
                               help=r'The operation mode needed. Available values: Online\Offline. Online mode will make changes on top of current flashed IFWI. Offline mode, will create IFWI with relevant changes (Need to provide IFWI)',
                               required=True)
    parser.add_argument('-b', '--bin',
                               help=r'Input IFWI binary file to modify --bin=<full_path_to_your_binary_ifwi>. This argument is mandatory for Offline mode.',
                               default='Disable')
    parser.add_argument('-ki', '--knob_input', default='Disable',
                        help=r'Path to directory contains knob input files txt files Or full path to knob input file. This argument is mandatory for Operation KnobChange\KnobAndPatchChange')
    parser.add_argument('-p', '--patch_input_file', default='Disable',
                        help=r'Path to required patch. Valid file types are .inc or .pdb. This argument is mandatory for PatchChange\KnobAndPatchChange')
    parser.add_argument('-r', '--reset', default='Disable',
                        help=r'Path to reset script including parameters if needed. e.g --reset="python C:\SVShare\User_Apps\TMTCommonServices\CommonServices\Managers\BootManager\run_boot_manager.py;-r cold -l C:\SVShare\boot_log.log" This switch is relevant only in Online mode')
    return parser.parse_args()


if __name__ == '__main__':
    global args
    args = parse_args()
    global cli
    if args.mode.upper() == "OFFLINE":
        if args.bin == 'Disable':
            ex = "For Offline mode, --bin argument is must. Please provide binary IFWI to modify"
            print(ex)
            raise ex
        if args.out == 'Disable':
            ex = "For Offline mode, --out argument is must. Please provide Output dir"
            print(ex)
            raise ex
        cli = InitialXmlCliStubMode()
    elif args.mode.upper() == "ONLINE":
        cli = InitialXmlCliOnlineMode()
    else:
        ex = "{0} is not valid value for --mode argument. Please choose Online\Offline".format(args.mode)
        print(ex)
        raise ex
    if (len(glob.glob(args.out + r'*.bin')) > 0):
        ex = "There is already binary files located in the output folder. Please provide output folder with no binaries inside"
        print(ex)
        raise ex
    if args.operation.lower() == "restoreknobstodefault":
        if args.mode.upper() == "OFFLINE":
            print ("Restore knobs to default values is not supported for offline mode by XmlCli. This is valid operation only for Online mode")
        else:
            RestoreKnobsToDefaultOnline()
    elif (args.operation.lower() == "knobchange"):
        StitchIfwiForSwConfigs()
    elif (args.operation.lower() == "patchchange"):
        StitchIfwiWithNewPatch(args.bin)
    elif (args.operation.lower() == "knobandpatchchange"):
        StitchIfwiForSwConfigsWithNewPatch()
    elif (args.operation.lower() == "dumpxmlknobs"):
        DumpXmlKnobs()
    print("Finished Successfully")

