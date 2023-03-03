'''This scrip gathering knobs form PlatformConfig.xml and create an knobs.txt
file to easy search.

import pysvtools.xmlcli.XmlCli as cli
cli.CvReadKnobs()

Core Team - Carlos - 10/13/2022

- Added html output - 12/16/2022
'''

import prettytable as pt
import xml.etree.ElementTree as ET
import os
import sys
import subprocess
from pathlib import Path


# know the python version
ver = os.path.dirname(sys.executable)
html_ = Path()
dir_path = Path(html_)
html_ = ''.join(str(dir_path.parent)+'\knobs.html')

try:

    tree = ET.parse(
        r'%s\lib\site-packages\pysvtools\xmlcli\out\PlatformConfig.xml' % ver)  # full path
    root = tree.getroot()
    print("[INFO] - Gathering knobs from PlatformConfig.xml !!")

    with open('knobs.txt', 'w', encoding='UTF8') as f:
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

    with open('knobs.txt', 'r', encoding='UTF8') as file:
        p = pt.from_csv(file)
        p.align = "l"
        p.title = 'Knobs List'
    with open('knobs.txt', 'w', encoding='UTF8') as g:
        g.write(str(p))
        
    htmlCode = p.get_html_string(attributes={"class":"table"}, format=True)
    fo = open(html_, "w")
    fo.write(htmlCode)
    fo.close()

    print("[INFO] - knobs.txt and knobs.html was created from PlatformConfig.xml!!")

except:
    print("\nNo PlatformConfig.xml has been created on this system.")
    print("Use these commands to create PlatformConfig.xml")
    print(""" \nimport pysvtools.xmlcli.XmlCli as cli
cli.CvReadKnobs()""")
