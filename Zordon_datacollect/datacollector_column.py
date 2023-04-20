#!/usr/bin/python3
###############################################################################
#  Data collector
#  By Carlos - Core Team
#
# This script loops through all hosts in hostlist.txt, collects Zordon JSON 
# information, and generates a collect_list_column.csv file containing all elements 
# specified in the conf.yaml file. Since the Zordon JSON has a complex list of 
# key-value pairs, you can configure the conf.yaml file as needed. 
# This was created per Borislav's request to assist with your debugging tasks.
# 
###############################################################################

import json
import csv
import yaml
import getpass
import base64
import logging
import argparse
import sys
import wmi
from datetime import datetime, timedelta
from prettytable import PrettyTable
from argparse import RawTextHelpFormatter
import textwrap
import subprocess
import time
from pathlib import Path


class DataCollect:
    def __init__(self):
        self.date = datetime.now().strftime('%Y_%m_%d_%H%M')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.log_format = '%(asctime)s %(message)s'
        self.logger = logging.getLogger()
        self.conf_file = r"conf\conf.yaml"
        self.collect_list = r"results\collect_list_column.csv"
        #logging.basicConfig(filename=f"DataCollect_{self.date}.log", format=self.log_format, datefmt='%Y-%m-%d %H:%M:%S') 

    def get_login(self):
        self.user = input('\nPlease enter user name: ')
        self.password = getpass.getpass('\nPlease enter password: ')
        user_pass = self.user + self.password
        authCred = base64.b64encode(user_pass.encode('utf-8'))
        authCred_str = str(authCred)
        file = open(r'password\password.txt', 'r')
        password = file.read()
        if authCred_str == password:
            return [self.user, self.password]
        else:
            print("\nUser or password is not valid.\n")
            self.get_login()
        return 1
    
    def ping_system(self):
        try:
            alive = subprocess.check_output(["powershell.exe", f"Test-Connection -ComputerName {self.host} -Count 1 -ErrorAction SilentlyContinue"])
            if alive != '':
                return 0
        except:
            return 1
        time.sleep(0.4)
    
    def load_hostlist(self):
        try:
            parser = argparse.ArgumentParser(description='''***This script loops through all hosts in hostlist.txt, collects Zordon JSON 
# information, and generates a collect_list_column.csv file containing all key elements 
# specified in the conf.yaml file.***\n \
                                             \n ex: datacollector.py -l hostlist.txt \n''', formatter_class=argparse.RawTextHelpFormatter)
            parser.add_argument('-l', '--hostlist', type=argparse.FileType('r'), help='List of Hosts (hostlist.txt).')
            args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
            host_list = args.hostlist
            self.hostlist = host_list.readlines()
            if len(self.hostlist) == 0:
                print("\nHost list is empty!!!\n")
            self.get_login()
            if self.user and self.password:
                if self.hostlist:
                    key_value_lists = []
                    for self.host in self.hostlist:
                        try:
                            if self.ping_system():
                                connect = wmi.WMI(f'{self.host.strip()}', user=self.user, password=self.password)
                                json_file = r"\\{}\c$\SVSHARE\ExecutionScripts\CurrentZordonSystem\ZordonSystem.json".format(self.host.strip())
                                json_data = self.process_json_file(json_file)
                                key_value_lists.append(self.collect_key_value_pairs(json_data, []))
                                #print(key_value_lists)
                                print(f'{self.host.strip()} - Collecting data')
                            else:
                                continue
                        except Exception as ex:
                            print(str(ex))
                    self.get_conf_extract(key_value_lists)
                else:
                    print("Error loading hostlist.txt") 
            else:
                print("Missing User or passwrod")
    
        except KeyboardInterrupt:
            self.logger.info('User stopped program.')
            print('User stopped program.')
   
    def collect_key_value_pairs(self, json_data, key_value_list):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                key_value_list.append({key: value})
                self.collect_key_value_pairs(value, key_value_list)
        elif isinstance(json_data, list):
            for item in json_data:
                self.collect_key_value_pairs(item, key_value_list)
        return key_value_list    
   
    def get_conf_extract(self, key_value_lists):
        with open(self.conf_file, "r") as conf_file:
            conf_data = yaml.safe_load(conf_file)
    
        with open(self.collect_list, "w", newline="") as csvfile:
            header = ["Key"] + [f"Host: {host.strip()}" for host in self.hostlist]
            csvfile.write(",".join(header) + "\n")
            keys = list(conf_data)
            count = 0
            for key in keys:
                csvfile.write(key + ",")
                for idx, key_value_list in enumerate(key_value_lists):
                    value = ""
                    for key_value in key_value_list:
                        if key in key_value:
                            if 'Socket' in key_value and key_value['Socket'] is None:
                                value = count
                            else:
                                value = key_value[key]
                            key_value.pop(key)
                            break
                    if isinstance(value, list):
                        new_value = '\n'.join(item for item in value)
                        csvfile.write(f"\"{new_value}\"")
                    else:
                        csvfile.write(str(value))
                    if idx < len(key_value_lists) - 1:
                        csvfile.write(",")
                if key == 'Socket':
                    count += 1
                csvfile.write("\n")
        if sys.exit(0):
            return "passed"
        else:
            return "failed"

                
    def process_json_file(self, json_file):
        with open(json_file, "r") as f:
            self.json_data = json.load(f)
        return self.json_data 
                
    def main(self):
        self.load_hostlist()
        print("\n{} created.".format(self.host.strip()))
        
if __name__ == "__main__":
    run = DataCollect()
    run.main()
    
