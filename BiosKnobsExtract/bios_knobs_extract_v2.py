# -----------------------------------------------------------------------------
# This scrip gathering knobs from PlatformConfig.xml and compare from each
# sysconfig ini file. The no-matching knobs are saved in result.txt

# \\ger.corp.intel.com\ec\proj\ha\sa\sa_laboratory\SA_IDC_SYNC\IDC\Utilities\Core-IP\SwConfigs
# \\amr\ec\proj\ha\sa\sa_laboratory\SA_AN_Sync\IDC\Utilities\Core-IP\SwConfigs\23.05.01.1_Rev245

# if PlatformConfig.xml is not prosent you need to open ITP/IPC and:
# import pysvtools.xmlcli.XmlCli as cli
# cli.CvReadKnobs()

# PlatformConfig.xml will be create in <python ver>\lib\site-packages\pysvtools\xmlcli\out\PlatformConfig.xml

# Core Team  - Carlos
# -----------------------------------------------------------------------------
from __future__ import print_function
from __future__ import absolute_import
import xml.etree.ElementTree as ET
import os
import sys
import subprocess
import re
import configparser
from pathlib import Path
import prettytable as pt


WIDTH = 70
ver = os.path.dirname(sys.executable)
print('-'*WIDTH)
print("            Bios knobs extractor and sysconfig check         ")
print('-'*WIDTH)
if sys.version_info[0] == 2:
    directory_path = raw_input("\nPlease enter full path of sysconfigs ini folder: ")
else:
    directory_path = input("\nPlease enter full path of sysconfigs ini folder:  ")
report_file_path = r"report.txt"
knobs_file_path = r"knobs.ini"
knobs_desc_path = r"knobs_desc.txt"
html_ = Path()
dir_path = Path(html_)
html_ = ''.join(str(dir_path.parent)+'\knobs.html')
platformconfig_xml = r'%s\lib\site-packages\pysvtools\xmlcli\out\PlatformConfig.xml' % ver

class BiosKnobs:
    def __init__(self):
        self.platformconfig_xml = platformconfig_xml
        self.directory_path = directory_path
        self.PlatformConfig_xml = ''
        self.report_file_path = report_file_path
        self.knobs_file_path = knobs_file_path
        self.knobs_desc_path = knobs_desc_path
        self.element = ''
        self.file_path = ''
        
    def create_platformconfig(self):
        '''Need Halt'''
        import pysvtools.xmlcli.XmlCli as cli
        cli.CvReadKnobs()
        self.extract_bios_knobs()
    
    def read_knobs_from_bios(self, bios):
        '''No Halt'''
        import pysvtools.xmlcli.XmlCli as cli
        cli.savexml(BiosBin = bios)
        self.extract_bios_knobs()
        
    def knobs_desc(self):
        tree = ET.parse(self.platformconfig_xml)
        root = tree.getroot()
        with open(self.knobs_desc_path, 'w') as f:
            f.write('"Knob Name", "Current Value", "Options", "Description"\n')
            for x in root.iter('knob'):
                if 'name' in x.attrib.keys() and 'description' in x.attrib.keys() != '':
                    options = ''
                    for item in x.findall('options'):
                        for i in item:
                            options += "{} : {}\n".format(i.attrib['text'], i.attrib['value'])
                        options += '-' * 37
                    f.write('"'+x.attrib['name']+'","'+x.attrib['CurrentVal'] +
                            '","'+options+'","'+x.attrib['description']+'"\n')
                            
                elif 'name' in x.attrib.keys() and 'description' in x.attrib.keys() == '':
                    for item in x.findall('options'):
                        for i in item:
                            options += "{} : {}\n".format(i.attrib['text'], i.attrib['value'])
                        options += '-' * 37
                    f.write('"'+x.attrib['name']+'","'+x.attrib['CurrentVal'] +
                            '","'+options+'"," "\n')
                else:
                    f.write('"'+x.attrib['name']+'","' +
                            x.attrib['CurrentVal']+'","'+options+'"," "\n')                 
        with open(self.knobs_desc_path, 'r') as file:
            p = pt.from_csv(file)
            p.align = "l"
            p.title = 'Knobs List'
        with open('knobs.txt', 'w') as g:
            g.write(str(p))
            
        htmlCode = p.get_html_string(attributes={"class":"table"}, format=True)
        fo = open(html_, "w")
        fo.write(htmlCode)
        os.remove(''.join(str(dir_path.parent)+'\knobs.txt'))
        os.remove(''.join(str(dir_path.parent)+'\knobs_desc.txt'))
        fo.close()

    def extract_bios_knobs(self):
        tree = ET.parse(self.platformconfig_xml)
        root = tree.getroot()
        print("[INFO] - Gathering knobs !!")
        #options = ''
        unique_knobs = set()
        with open(knobs_file_path, 'w') as f:
            f.write('[BiosKnobs]'+'\n')
            for x in root.iter('knob'):
                knob_name = x.attrib['name']
                if knob_name not in unique_knobs:
                    unique_knobs.add(knob_name)
                    f.write(knob_name+'='+x.attrib['CurrentVal'] + '\n')
            print("[INFO] - All Bios Knobs are saved in knobs.ini")

    def compare_ini_files(self):
        knobs_config = configparser.RawConfigParser()
        knobs_config.read(self.knobs_file_path)
        file_config = configparser.RawConfigParser()
        file_config.read(self.file_path)

        differences = {}
        for section in knobs_config.sections():
            for element in knobs_config[section]:
                if section in file_config and element in file_config[section]:
                    try:
                        knobs_value = int(knobs_config[section][element], 0)
                        file_value = int(file_config[section][element], 0)
                    except ValueError:
                        knobs_value = knobs_config[section][element]
                        file_value = file_config[section][element]

                    if knobs_value != file_value:
                        differences[element] = (
                            knobs_config[section][element], file_config[section][element])

        return differences

    def write_report(self, results):
        with open(self.report_file_path, 'w') as report:
            for file, differences in results.items():
                file_str = '{}:'.format(file)
                file_str = file_str.ljust(WIDTH - len("Bios Knobs:"))
                report.write("{}            Bios Knobs:\n".format(file_str))

                if not differences:
                    report.write("All knobs are the same.\n")
                    report.write('\n')
                    continue

                for self.element, (knobs_value, file_value) in differences.items():
                    comment = ''
                    if ';' in file_value:
                        file_value, comment = file_value.split(';', 1)
                        comment = "; {}".format(comment.strip())

                    try:
                        knobs_value_int = int(knobs_value, 0)
                        file_value_int = int(file_value, 0)

                        if knobs_value_int == file_value_int:
                            continue

                        knobs_value = hex(knobs_value_int)
                        file_value = hex(file_value_int)
                    except ValueError:
                        pass
                    element_str = "- {}={}{}".format(self.element, file_value, comment )
                    element_str = element_str.ljust(WIDTH)
                    report.write("{} {}={}\n".format(element_str, self.element, knobs_value ))
                report.write('\n')

    def main(self):
        opt = int(input('''Enter 1 to Fetching Firmware Info from the given Bios Binary
Enter 2 to Create PlatformConfig.xml and ReadKnobs ***Need HALT***\n'''))
        if opt == 1:
            version = re.search(r'\d+', ver)
            python27 = version.group()
            if python27 == '27':
                bios = raw_input("Enter Bios path: ")
                self.read_knobs_from_bios(bios)
            else:
                self.read_knobs_from_bios(bios=str(input("Enter Bios path: ")).strip('"'))
        elif opt == 2:
            self.create_platformconfig()
        else:
            print("Invalid Option")
        extract.knobs_desc()
        results = {}
        for root, _, files in os.walk(self.directory_path):
            for file in files:
                if file.endswith('.ini'):
                    self.file_path = os.path.join(root, file)
                    differences = self.compare_ini_files()
                    if differences:
                        results[file] = differences
        
        self.write_report(results)
        print('''[INFO] - report.txt has been created, containing all sysconfig ini files 
         and non-matching BIOS knob values.\n''')
        print('[INFO] report.txt path: {}'.format(self.report_file_path))
        

if __name__ == "__main__":
    extract = BiosKnobs()
    extract.main()
