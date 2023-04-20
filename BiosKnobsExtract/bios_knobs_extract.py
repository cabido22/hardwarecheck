# -----------------------------------------------------------------------------
# This scrip gathering knobs from PlatformConfig.xml and compare from each
# sysconfig ini file. The no-matching knobs are saved in result.txt

# \\ger.corp.intel.com\ec\proj\ha\sa\sa_laboratory\SA_IDC_SYNC\IDC\Utilities\Core-IP\SwConfigs

# if PlatformConfig.xml is not prosent you need to open ITP/IPC and:
# import pysvtools.xmlcli.XmlCli as cli
# cli.CvReadKnobs()

# PlatformConfig.xml will be create in <python ver>\lib\site-packages\pysvtools\xmlcli\out\PlatformConfig.xml

# Core Team  - Carlos
# -----------------------------------------------------------------------------

import os
import sys
import configparser
import xml.etree.ElementTree as ET
from pathlib import Path
import prettytable as pt


WIDTH = 70
ver = os.path.dirname(sys.executable)
print('-'*WIDTH)
print("            Bios knobs extractor and sysconfig check         ")
print('-'*WIDTH)
directory_path = input("\nPlease enter full path of sysconfigs ini folder:  ")
PlatformConfig_xml = r'%s\lib\site-packages\pysvtools\xmlcli\out\PlatformConfig.xml' % ver
if not os.path.exists(PlatformConfig_xml):
    print("""\nPlatformConfig.xml does not exist. 
Please run cli.CvReadKnobs() to create Platformconfig.xml from Bios""")
    sys.exit()
report_file_path = r"report.txt"
knobs_file_path = r"knobs.ini"
knobs_desc_path = r"knobs_desc.txt"
html_ = Path()
dir_path = Path(html_)
html_ = ''.join(str(dir_path.parent)+'\knobs.html')

class BiosKnobs:
    def __init__(self, directory_path, PlatformConfig_xml, report_file_path, knobs_file_path):
        self.directory_path = directory_path
        self.PlatformConfig_xml = PlatformConfig_xml
        self.report_file_path = report_file_path
        self.knobs_file_path = knobs_file_path
        self.element = ''
        self.file_path = ''
        
    def knobs_desc(self):
        tree = ET.parse(PlatformConfig_xml)
        root = tree.getroot()
        with open(knobs_desc_path, 'w', encoding='UTF8') as f:
            f.write('"Knob Name", "Current Value", "Options", "Description"\n')
            for x in root.iter('knob'):
                if 'description' in x.attrib.keys():
                    for item in x.findall('options'):
                        options = ''
                        for i in item:
                            options += f"{i.attrib['text']} : {i.attrib['value']}\n"
                        options += '-' * 81
                        f.write('"'+x.attrib['name']+'","'+x.attrib['CurrentVal'] +
                                '","'+options+'","'+x.attrib['description']+'"\n')

                else:
                    f.write('"'+x.attrib['name']+'","' +
                            x.attrib['CurrentVal']+'","'+options+'"," "\n')

        with open(knobs_desc_path, 'r', encoding='UTF8') as file:
            p = pt.from_csv(file)
            p.align = "l"
            p.title = 'Knobs List'
        with open('knobs.txt', 'w', encoding='UTF8') as g:
            g.write(str(p))
            
        htmlCode = p.get_html_string(attributes={"class":"table"}, format=True)
        fo = open(html_, "w")
        fo.write(htmlCode)
        fo.close()

    def extract_bios_knobs(self):
        tree = ET.parse(self.PlatformConfig_xml)
        root = tree.getroot()
        print("\n[INFO] - Gathering knobs from PlatformConfig.xml !!")

        with open(knobs_file_path, 'w', encoding='UTF8') as f:
            f.write('[BiosKnobs]'+'\n')
            for x in root.iter('knob'):
                if 'description' in x.attrib.keys():
                    for item in x.findall('options'):
                        options = ''
                        for i in item:
                            options += f"{i.attrib['text']} : {i.attrib['value']}\n"
                        f.write(x.attrib['name']+'=' +
                                x.attrib['CurrentVal'] + '\n')

                else:
                    f.write(x.attrib['name']+'='+x.attrib['CurrentVal'] + '\n')
            print("[INFO] - All Bios Knobs are saved in knobs.ini")

    def compare_ini_files(self):
        knobs_config = configparser.ConfigParser()
        knobs_config.read(self.knobs_file_path)
        file_config = configparser.ConfigParser()
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
                file_str = f"{file}:"
                file_str = file_str.ljust(WIDTH - len("Bios Knobs:"))
                report.write(f"{file_str}            Bios Knobs:\n")

                if not differences:
                    report.write("All knobs are the same.\n")
                    report.write('\n')
                    continue

                for self.element, (knobs_value, file_value) in differences.items():
                    comment = ''
                    if ';' in file_value:
                        file_value, comment = file_value.split(';', 1)
                        comment = f"; {comment.strip()}"

                    try:
                        knobs_value_int = int(knobs_value, 0)
                        file_value_int = int(file_value, 0)

                        if knobs_value_int == file_value_int:
                            continue

                        knobs_value = hex(knobs_value_int)
                        file_value = hex(file_value_int)
                    except ValueError:
                        pass

                    element_str = f"- {self.element}={file_value}{comment}"
                    element_str = element_str.ljust(WIDTH)
                    report.write(
                        f"{element_str} {self.element}={knobs_value}\n")
                report.write('\n')

    def main(self):
        self.extract_bios_knobs()

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
        print(f"report.txt path: {self.report_file_path}")


if __name__ == "__main__":
    extract = BiosKnobs(directory_path, PlatformConfig_xml,
                        report_file_path, knobs_file_path)
    extract.knobs_desc() #This creates knobs_desc.txt with knobs description in pretty table
    extract.main()
