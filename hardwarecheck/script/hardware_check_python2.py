#!/usr/bin/python2
###############################################################################
#  Hardware Check
#  By Carlos - Core Team
#
#"This script automatically compares the '{project}.json' file with the 'ZordonSystem.json' 
# output file generated by BoardInfo. The script will generate two output files: 
#'hardware_.log' and 'hardware_verify.html'. The '{project}.json' file needs to 
# be manually created using the same JSON structure as 'data.json'."
#
###############################################################################
from __future__ import print_function
from __future__ import absolute_import
import sys, json, os
from prettytable import PrettyTable
from datetime import datetime
import time
try:
    import yaml
except ImportError:
    import subprocess 
    import importlib
    subprocess.call(['pip', 'install', './yaml/PyYAML-5.4.1-cp27-cp27m-win_amd64.whl'])
    #importlib.import_module('yaml')
    import yaml

data_ = r'C:\SVSHARE\ExecutionScripts\CurrentZordonSystem\ZordonSystem.json'
if os.path.isfile(data_):
    os.remove(data_)
while not os.path.isfile(data_):
    time.sleep(5)
data_ = r'C:\SVSHARE\ExecutionScripts\CurrentZordonSystem\ZordonSystem.json'


class HardwareChecker:
    pathfolder_ = r'C:\SVSHARE\User_Apps'
    log_ = r'%s\Hardwarecheck\Hardwarecheck_fail.log' % pathfolder_
    html_ = r'%s\Hardwarecheck\Hardwarecheck_fail.html' % pathfolder_
    config_ = r'%s\Hardwarecheck\conf' % pathfolder_
    log_path = r'%s\Hardwarecheck' % pathfolder_
    
    def __init__(self, data):
        self.por_list = []
        self.por_ = ""
        self.data_list = []
        self.date = datetime.now().strftime('%m/%d/%y at %H:%M')
        self.data_json = data
        self.por_yaml = {}
        
    def dict_generator(self, adict, pre=None):
        pre = pre[:] if pre else []
        if isinstance(adict, dict):
            for key, value in adict.items():
                if isinstance(value, dict):
                    for result in self.dict_generator(value, pre + [key]):
                        yield result
                elif isinstance(value, (list, tuple)):
                    for v in value:
                        for result in self.dict_generator(v, pre + [key] + [value.index(v)]):
                            yield result
                else:
                    yield pre + [key, value]
        else:
            yield pre + [adict]

    def get_str_ptr(self,l):
        s = ""
        for i in range(len(l)):
            if isinstance(l[i], int):
                s += "["+str(l[i])+"]"
            else:
                s += "[\""+l[i]+"\"]"
        return str(s)
        
    def create_table(self):
        table = PrettyTable()
        table.field_names = ["Items", "%s" % self.proj, "ZordonSystem.json"]
        table.field_names = ["Items", "%s" % self.proj, "ZordonSystem.json"]
        table.title = "Differences between required %s (expected) and collected data ZordonSystem.json (actual). Log created: %s" % (self.proj, self.date)
        table.padding_width = 1
        table._max_width = {"Items": 50, "por_json": 64, "data_json": 64}
        table.format = True
        with open(self.log_, 'w') as fp:
            fp.write("\nDifferences between required %s (expected) and collected ZordonSystem.json (actual)\n" % self.proj)
            for item in self.names:
                tmp = item
                for i in reversed(range(len(tmp))):
                    tmp = tmp[:-1]
                    try:
                        v = eval("self.data_json"+self.get_str_ptr(tmp))
                    except:
                        v = None
                    if v is not None:
                        table.add_row(
                            ['%s' % item, '%s' % eval("self.por_yaml"+self.get_str_ptr(tmp)), '%s' % v])
                        table.add_row(['-'*50,'-'*64,'-'*64])
                        break
                    elif i == 1:
                        table.add_row(
                            ['%s' % item, '%s' % eval("self.por_yaml"+self.get_str_ptr(tmp)), 'Not present'])
                        table.add_row(['-'*50,'-'*64,'-'*64])
                        break

            for key, item in self.por_yaml.items():
                if isinstance(item, list):
                    p = len(item)
                    try:
                        d = len(self.data_json[key])
                    except:
                        d = None
                    if (d is not None) and (d != p):
                        table.add_row(['[%s]' % str(key), 'Required %s' % p, 'Found %s' % d])
                        table.add_row(['-'*50,'-'*64,'-'*64])
            fp.write(str(table))

        htmlCode = table.get_html_string(attributes={"class":"table"}, format=True)
        fo = open(self.html_, "w")
        fo.write(htmlCode)
        fo.close()

        
    def get_project(self):
        data = self.dict_generator(self.data_json)
        for data_item in data:
            self.data_list.append(data_item)
        with open(self.por_, 'r') as f:
            self.por_yaml = yaml.load(f, Loader=yaml.FullLoader)
        por = self.dict_generator(self.por_yaml)
        for por_item in por:
            self.por_list.append(por_item)
        for data_item in data:
            self.data_list.append(data_item)

        #shows por_json elements
        self.names = ([x for x in self.por_list if x not in self.data_list])
        if not self.names:
            print("\n[INFO] - HARDWARE_CHECK PASSED!")
        else:
            print("[WARNING] - HARDWARE_CHECK FAILED!")
            print("[WARNING] - Log files created at %s" % self.log_path)
            self.create_table()
            sys.exit(1)

    def main(self):
        arg = sys.argv[1]
        self.proj = self.data_json['SiliconFamily']
    
        if arg != 'True' or arg == '':
            self.por_ = os.path.join(self.config_, arg)
            self.proj = self.data_json['SiliconFamily']
            self.get_project()
            
        else:    
            self.siliconfamily = self.data_json['SiliconFamily']
            family_to_path = {
                "CLX": {1: "CLX_UP.yaml", 2: "CLX_DP.yaml"},
                "SKX": {1: "SKX_UP.yaml", 2: "SKX_DP.yaml"},
                "CPX": {1: "CPX_UP.yaml", 2: "CPX_DP.yaml"},
                "ICX": {1: "ICX_UP.yaml", 2: "ICX_DP.yaml"},
                "SPR": {1: "SPR_UP.yaml", 2: "SPR_DP.yaml"},
                "EMR": {1: "EMR_UP.yaml", 2: "EMR_DP.yaml"},
                "GNR": {1: "GNR_UP.yaml", 2: "GNR_DP.yaml"},
            }
            
            if self.siliconfamily in family_to_path:
                if isinstance(family_to_path[self.siliconfamily], str):
                    self.por_ = self.config_+"/"+ family_to_path[self.siliconfamily]
                    self.proj = family_to_path[self.siliconfamily]
                    self.get_project()
                elif isinstance(family_to_path[self.siliconfamily], dict):
                    if len(self.data_json['BoardInfo']['Units']) == 2:
                        self.por_ = self.config_+"/"+ family_to_path[self.siliconfamily][2]
                        self.proj = family_to_path[self.siliconfamily][2]
                        self.get_project()
                    else:
                        self.por_ = self.config_+"/"+ family_to_path[self.siliconfamily][1]
                        self.proj = family_to_path[self.siliconfamily][1]
                        self.get_project()
            else:
                raise ValueError("Unknown SiliconFamily: {}".format(self.siliconfamily))


if __name__ == '__main__':
    with open(str(data_), 'r') as f:
        data_json = json.load(f)
    run = HardwareChecker(data_json)
    try:
        run.main()
    except Exception as ex:
        print(str(ex))
        sys.exit(-1)
    sys.exit(0)