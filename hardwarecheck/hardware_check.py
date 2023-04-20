from __future__ import print_function
import argparse
import subprocess
import os, sys

script2_path = r"C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python2.py"
script3_path = r"C:\SVSHARE\User_Apps\hardwarecheck\script\hardware_check_python3.py"

ver = str(subprocess.check_output(['python', '--version'],  stderr=subprocess.STDOUT))

parser = argparse.ArgumentParser(description='Call hardware_check_python2.py or hardware_check_python3.py and handle errors.', formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('--stop_on_error', action='store_true', help='Stop execution if hardware check encounters an error.')
parser.add_argument('--continue_on_error', action='store_true', help='Continue execution if hardware check encounters an error.')
parser.add_argument('--user_yaml', metavar='filename', help=('Create a custom YAML configuration file. Save in the "conf" directory.\n'
                                                         '(e.g., GNR_DP_4DIMM.yaml).\n'
                                                         'This file will override the standard configuration file.\n'
                                                         'Example:\n'
                                                         '    hardware_check.py --stop_on_error --user_yaml GNR_DP_4DIMM.yaml\n'
                                                         '    hardware_check.py --continue_on_error --user_yaml GNR_DP_4DIMM.yaml'))
parser.add_argument('--no_flag', action='store_true', help='Use this flag when running hardwarecheck_withBoardinfo.py without any specific arguments.')

args = parser.parse_args(args=None if sys.argv[1:] else ['--no_flag'])
if '2.' in ver:
    if args.no_flag:
        return_code = subprocess.call(['python', script2_path, str(args.no_flag)])
    elif args.user_yaml:
        return_code = subprocess.call(['python', script2_path, str(args.user_yaml)])  
    elif args.stop_on_error:
        return_code = subprocess.call(['python', script2_path, str(args.stop_on_error)])
    elif args.continue_on_error:
        return_code = subprocess.call(['python', script2_path, str(args.continue_on_error)])

else:
    if args.no_flag:
        return_code = subprocess.call(['python', script3_path, str(args.no_flag)])
    elif args.user_yaml:
        return_code = subprocess.call(['python', script3_path, str(args.user_yaml)])  
    elif args.stop_on_error:
        return_code = subprocess.call(['python', script3_path, str(args.stop_on_error)])
    elif args.continue_on_error:
        return_code = subprocess.call(['python', script3_path, str(args.continue_on_error)])
             
if return_code == 0:
    pass
else:
    if args.stop_on_error:
        print('[WARNING] - Stopping execution due to --stop_on_error flag')
        sys.exit(1)
    elif args.continue_on_error:
        print('[WARNING] - Continuing execution due to --continue_on_error flag')
        sys.exit(0)
    elif args.no_flag:
        print('[INFO] - no_flag.')
        sys.exit(0)