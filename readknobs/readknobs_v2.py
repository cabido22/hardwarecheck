'''This scrip gathering knobs form PlatformConfig.xml and create an knobs.html
file to easy search.

import pysvtools.xmlcli.XmlCli as cli
cli.CvReadKnobs()

Core Team - Carlos - 10/13/2022

- Added html output - 12/16/2022
'''
from __future__ import print_function
from __future__ import absolute_import
import prettytable as pt
import xml.etree.ElementTree as ET
import os
import sys
import subprocess
from pathlib import Path
import re

# know the python version
ver = os.path.dirname(sys.executable)
html_ = Path()
dir_path = Path(html_)
html_ = ''.join(str(dir_path.parent)+'\knobs.html')

def create_platformconfig():
    '''Need Halt'''
    import pysvtools.xmlcli.XmlCli as cli
    cli.CvReadKnobs()
    read_knobs_from_platformconfig()
    
def read_knobs_from_bios(bios):
    '''No Halt'''
    import pysvtools.xmlcli.XmlCli as cli
    cli.savexml(BiosBin = bios)
    read_knobs_from_platformconfig()

def read_knobs_from_platformconfig():
    ''' No Halt'''
    tree = ET.parse(r'%s\lib\site-packages\pysvtools\xmlcli\out\PlatformConfig.xml' % ver)  # full path
    root = tree.getroot()
    print("[INFO] - Gathering knobs from PlatformConfig.xml !!")
    options = ''
    with open('knobs.txt', 'w') as f:
        f.write('"Knob Name", "Current Value", "Options", "Description"\n')
        for x in root.iter('knob'):
            if 'name' in x.attrib.keys() and 'description' in x.attrib.keys() != '':
                for item in x.findall('options'):
                    options = ''
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

    with open('knobs.txt', 'r') as file:
        p = pt.from_csv(file)
        p.align = "l"
        p.title = 'Knobs List'
    with open('knobs.txt', 'w') as g:
        g.write(str(p))
        
    htmlCode = p.get_html_string(attributes={"class":"table"}, format=True)
    fo = open(html_, "w")
    fo.write(htmlCode)
    os.remove(''.join(str(dir_path.parent)+'\knobs.txt'))
    fo.close()

    print('[INFO] - {} was created from PlatformConfig.xml!!'.format(html_))
     

if __name__ == "__main__":
    opt = int(input('''Enter 1 to Fetching Firmware Info from the given Bios Binary
Enter 2 to Create PlatformConfig.xml and ReadKnobs ***Need HALT***\n'''))
    
    if opt == 1:
        version = re.search(r'\d+', ver)
        if version:
            python27 = version.group()
        if python27 == '27':
            bios = raw_input("Enter Bios path: ")
            read_knobs_from_bios(bios)  # Use this funtion to read knobs from bios file and save to PlatformConfig.xml. 
                                                                              # Doesn't need HALT
        else:
            read_knobs_from_bios(bios=str(input("Enter Bios path: ")).strip('"'))
    elif opt == 2:
        create_platformconfig()                                           # Use this funtion to read knobs. NEED HALT. PlatformConfig.xml will be created.
    else:
        print("Invalid Option")