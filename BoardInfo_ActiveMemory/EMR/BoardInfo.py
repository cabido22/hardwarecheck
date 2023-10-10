from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import shutil
from builtins import open
import importlib
import pkgutil
import sys

from UnitInfo.Device import Device
if sys.hexversion > 0x03060800:
    from helpers.tools.ttk_helper import TTK
from helpers.tools.uls_helper import ULS

try:
    from future import standard_library

    standard_library.install_aliases()
except:
    pass
from builtins import str
from builtins import object
import os
import loggerHelper
import logging
from collections import OrderedDict
import datetime
import json
import configparser
import errors_handler
import win32api
import string
import re
import xml.etree.ElementTree
import Project
import argparse

if sys.hexversion > 0x03060800:
    from sic.CSutInfo import CSutInfo
    from sic.InfoItemsDB import add_info_items


class BoardInfo(object):
    def __init__(self, avoid_forcereconfig, skip_closing_openipc, intrusive, write_json,
                 sic_items_dict=None, is_discrete=True, sic_enabled=False):
        # initialize dictionary for JSON file
        self.intrusive = intrusive
        self.sic = sic_enabled
        self.set_silicon_family()
        self.boardinfo_dict = {}
        self.num_of_cores = '0'
        self.num_of_threads = '0'
        self.init_boardinfo_dictionary()
        self.output_dict = None
        # get the project
        self.device = self.get_project_instance(avoid_forcereconfig)
        sic_result = {}
        if self.device is not None:
            try:
                # CPU info ---> unitUlt + unitStep
                self.device.CpuInfo = self.device.getCpuInfo()
                # get DOK platform info ---> boardType + boardSerial
                self.get_dok_platform_info()
                # get Platform info ---> number of threads+cores
                self.get_platform_info()
                # get Ifwi info ---> zypherId + biosVersion + microCodePatch
                self.get_ifwi_info()
                # get memory info
                self.get_memory()
                # - The following area is made for intrusive actions that requires halting the unit.
                # - Calls for functions that make intrusive actions should be added between the
                #   "self.device.safe_halt(ipc)" and "self.device.safe_go(ipc)" commands.
                # - Every function in the intrusive area should have an empty implementation in Devices.py and
                #   override to the function with actual logic in the project module.
                if self.intrusive:
                    ipc = None
                    try:
                        ipc = self.device.get_itp()
                        self.device.safe_halt(ipc)
                        # get PCIe Info
                        self.device.get_pcie()
                        ver = sys.version
                        if sic_enabled and sys.hexversion > 0x03060800:
                            sut_info = CSutInfo(ipc, logger)
                            if not sic_items_dict:
                                sic_items_list = self.get_sic_items_list()
                                if sic_items_list:
                                    sic_items_dict = dict.fromkeys(sic_items_list, None)
                            if sic_items_dict:
                                self.device.sic_result = sut_info.get_x(self.silicon_family, sic_items_dict,
                                                            is_discrete=is_discrete)
                    except Exception as e:
                        logger.error('Error occurred due to the following exception: {}'.format(e))
                    finally:
                        try:
                            self.device.safe_go(ipc)
                        except Exception as e:
                            logger.error('Could not resume unit due to the following exception: {}'.format(e))
                if self.device.lock_unit_when_finished:
                    self.device.itp.itp.lock()
            except Exception as ex:
                logger.error('Scanning failed due to the following exception: {}'.format(ex))
        else:
            self.check_port80()

        boardinfo_dict = self.set_dictionary(self.boardinfo_dict)
        if write_json:
            self.create_json(boardinfo_dict)
        self.output_dict = boardinfo_dict
        self._report_unit_location(boardinfo_dict)
        if hasattr(self.device, "itp") and not skip_closing_openipc:
            self.device.itp.CloseConnection()

    def get(self):
        return self.output_dict

    @staticmethod
    def check_port80():
        try:
            if sys.hexversion > 0x03060800:
                ttk = TTK()
                if ttk.is_port80_off():
                    raise Exception('Power is down')
            else:
                raise Exception('ttk_helper module supports python 3.6 and above only')
        except Exception as e:
            error_msg = 'Cannot determine power status using TTK: {}'.format(e)
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)

    def get_dok_platform_info(self):
        try:
            logger.info("Going to search for DOK with BoardInfo.dat\\xml\\txt file")
            drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
            detected_drive = None
            logger.info("Available drives: " + str(drives))
            for drive in drives:
                if os.path.exists(drive + "\\" + "BoardInfo.dat") or os.path.exists(
                        drive + "\\" + "BoardInfo.xml") or os.path.exists(drive + "\\" + "BoardInfo.txt"):
                    logger.info("BoardInfo file was found in drive " + drive)
                    detected_drive = drive
            if detected_drive is None:
                error_msg = r'could not find any drive which contains BoardInfo.dat file'
                logger.error(error_msg)
                self._BoardType = ''
                self._BoardSerial = ''
                errors_handler.ErrorsHandler.add_error('Board', error_msg)
                return self
            logger.info("getting DokPlatformInfo")
            path_xml = detected_drive + '\\BoardInfo.xml'
            path_txt = detected_drive + '\\BoardInfo.txt'
            path_dat = detected_drive + '\\BoardInfo.dat'
            path = ''
            win32api.GetVolumeInformation(detected_drive + "\\")
            if os.path.isfile(path_dat):
                path = path_dat
                logger.info("Found {} file on the host, about to parse it".format(str(path_dat)))
                with open(path_dat) as f:
                    content = f.read()
                # replace non-ascii characters with space, then split by spaces
                res = str(re.sub(r'[^\x00-\x7F]+', ' ', content))
                res = ''.join(list([x for x in res if x in string.printable])).strip().split()
                # removes all single chars and spaces
                res = (list([x for x in res if len(x) > 1]))
                # join all strings and split the last one from the rest - last one is the serial, the rest are the board
                res = str(" ".join(res)).rsplit(" ", 1)
                self._BoardType = res[0]
                self._BoardSerial = res[-1]
            elif os.path.isfile(path_xml):
                path = path_xml
                logger.info("Found {} file on the host, about to parse it".format(str(path_xml)))
                file = xml.etree.ElementTree.parse(path_xml).getroot()
                self._BoardType = self.get_board_type(file)
                self._BoardSerial = self._get_board_serial(file)
            elif os.path.isfile(path_txt):
                logger.info("Found {} file on the host, about to parse it".format(str(path_txt)))
                path = path_txt
                win32api.GetVolumeInformation("D:\\")
                with open(path) as f:
                    content = f.readlines()
                for line in content:
                    if line.__contains__("SerialNumber"):
                        self._BoardSerial = line.split('SerialNumber=')[1].strip()
                    if line.__contains__("BoardType"):
                        self._BoardType = line.split('BoardType=')[1].strip()
                    if line.__contains__("CpuSerial"):
                        self._CpuSerial = line.split('CpuSerial=')[1].strip()
            logger.info(
                "DokPlatformInfo: BoardType={}. BoardSerial={}".format(self._BoardType, self._BoardSerial))
        except Exception as e:
            error_msg = r'could not parse {} file{}'.format(str(path), str(e))
            logger.error(error_msg)
            self._BoardType = ''
            self._BoardSerial = ''
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return self

    def get_board_type(self, file):
        return file.get('type')

    def _get_board_serial(self, file):
        return file.get('serialNumber')

    def get_platform_info(self):
        try:
            logger.info("getting platform info")
            return self.device.getPlatformInfo()
        except Exception as e:
            error_msg = r'Failed to get num_of_cores and num_of_threads: {}'.format(str(e))
            logger.error(error_msg)
            self.num_of_cores = '0'
            self.num_of_threads = '0'
            errors_handler.ErrorsHandler.add_error('Board', error_msg)

    def get_memory(self):
        try:
            logger.info("getting memory info")
            return self.device.get_memory()
        except Exception as e:
            error_msg = r'Failed to read platform memory: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Memory', error_msg)

    def get_ifwi_info(self):
        self.device.getIfwiInfo()

    def get_platform_id(self):
        return self.device.get_platform_id()

    def get_cpu_info(self):
        try:
            return self.device.getCpuInfo()
        except Exception as e:
            error_msg = str(e)
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)

    def set_dictionary(self, boardinfo_dict):
        list_of_units = []
        list_of_pch = []
        list_of_packages = []
        list_of_memory = []
        list_of_pcie = []
        total_cores = 0
        total_threads = 0
        if hasattr(self.device, 'CpuInfo') and hasattr(self.device.CpuInfo, 'Cpus') and self.device.CpuInfo.Cpus:
            for cpu in self.device.CpuInfo.Cpus:
                unit = OrderedDict()
                unit['UnitSerial'] = ''
                unit['Product'] = ''
                unit['DataSource'] = ''
                if hasattr(cpu, "_unit_serial"):
                    unit['UnitSerial'] = cpu._unit_serial
                if hasattr(cpu, "_product"):
                    unit['Product'] = cpu._product
                if hasattr(cpu, "_product"):
                    unit['DataSource'] = cpu._datasource
                unit['Socket'] = cpu.socket_number
                unit['NumOfCores'] = cpu.num_of_cores
                unit['NumOfThreads'] = cpu.num_of_threads
                total_cores += cpu.num_of_cores
                total_threads += cpu.num_of_threads
                if cpu.Ult is not None:
                    unit['UnitUlt'] = cpu.Ult.replace('+', '')
                else:
                    unit['UnitUlt'] = ""
                unit['QDF'] = ''
                if hasattr(cpu, "qdf"):
                    unit['QDF'] = cpu.qdf
                unit['UnitStep'] = cpu.Step
                if hasattr(cpu, "CdieStep"):
                    unit['CdieStep'] = cpu.CdieStep
                unit['FuseRevision'] = cpu.FuseRev
                unit['NPKAddress'] = ''
                if hasattr(cpu, "NPKAddress"):
                    unit['NPKAddress'] = cpu.NPKAddress
                unit['CpuID'] = ''
                if hasattr(cpu, "CpuId"):
                    unit['CpuID'] = cpu.CpuId
                if hasattr(cpu, "atom_stepping"):
                    unit['AtomStepping'] = cpu.atom_stepping
                if hasattr(cpu, 'Straps'):
                    unit['Straps'] = cpu.Straps
                list_of_units.append(unit)

        # no cpu was found, all are blank - except ITP1 devices that got it from boardInfo.txt file
        else:
            unit = OrderedDict()
            unit['UnitSerial'] = ''
            unit['Product'] = ''
            unit['DataSource'] = ''
            unit['UnitUlt'] = ''
            unit['UnitStep'] = ''
            unit['FuseRevision'] = ''
            unit['QDF'] = ''
            unit['NumOfCores'] = 0
            unit['NumOfThreads'] = 0
            unit['NPKAddress'] = ''
            list_of_units.append(unit)
        if hasattr(self.device, 'CpuInfo') and hasattr(self.device.CpuInfo, 'Pch') and self.device.CpuInfo.Pch:
            for pch in self.device.CpuInfo.Pch:
                unit = OrderedDict()
                unit['UnitUlt'] = ''
                unit['UnitStep'] = ''
                unit['QDF'] = ''
                unit['UnitSerial'] = ''
                unit['Product'] = ''
                unit['DataSource'] = ''
                if hasattr(pch, "_unit_serial"):
                    unit['UnitSerial'] = pch._unit_serial
                if hasattr(pch, "_product"):
                    unit['Product'] = pch._product
                if hasattr(pch, "_product"):
                    unit['DataSource'] = pch._datasource
                if hasattr(pch, "qdf"):
                    unit['QDF'] = pch.qdf
                if pch.Ult is not None:
                    unit['UnitUlt'] = pch.Ult.replace('+', '')
                if hasattr(pch, "Step"):
                    unit['UnitStep'] = pch.Step
                list_of_pch.append(unit)
        else:
            unit = OrderedDict()
            unit['UnitUlt'] = ''
            unit['UnitSerial'] = ''
            unit['DataSource'] = ''
            unit['Product'] = ''
            unit['UnitStep'] = ''
            unit['QDF'] = ''
            list_of_pch.append(unit)

        if hasattr(self.device, 'CpuInfo') and hasattr(self.device.CpuInfo, 'packages') and self.device.CpuInfo.packages:
            for package in self.device.CpuInfo.packages:
                list_of_dies = []
                unit = OrderedDict()
                unit['Socket'] = ''
                unit['UnitStep'] = ''
                unit['UnitSerial'] = ''
                unit['DataSource'] = ''
                unit['Product'] = ''
                unit['QDF'] = ''
                if hasattr(package, "serial"):
                    unit['UnitSerial'] = package.serial
                if hasattr(package, "stepping"):
                    unit['UnitStep'] = package.stepping
                if hasattr(package, "socket"):
                    unit['Socket'] = package.socket
                if hasattr(package, "datasource"):
                    unit['DataSource'] = package.datasource
                if hasattr(package, "product"):
                    unit['Product'] = package.product
                if hasattr(package, "qdf"):
                    unit['QDF'] = package.qdf
                if hasattr(package, "dies") and package.dies:
                    for die in package.dies:
                        d = {}
                        if hasattr(die, "name"):
                            d['Name'] = die.name
                        if hasattr(die, "ult"):
                            d['ULT'] = die.ult
                        if hasattr(die, "qdf"):
                            d['QDF'] = die.qdf
                        if hasattr(die, "stepping"):
                            d['Stepping'] = die.stepping
                        list_of_dies.append(d)
                unit["Dies"] = list_of_dies
                list_of_packages.append(unit)
        else:
            unit = OrderedDict()
            unit['Socket'] = ''
            unit['UnitStep'] = ''
            unit['UnitSerial'] = ''
            unit['DataSource'] = ''
            unit['Product'] = ''
            unit['Dies'] = []
            list_of_packages.append(unit)

        if hasattr(self.device, 'Memory') and self.device.Memory:
            for item in self.device.Memory:
                mem = OrderedDict()
                mem['Socket'] = item.socket
                mem['Memory_Controller'] = item.memory_controller
                mem['Channel'] = item.channel
                mem['Slot'] = item.slot
                mem['DIMM_Vendor'] = item.dimm_vendor
                mem['DIMM_Register_Vendor'] = item.dimm_register_vendor
                mem['DIMM_Type'] = item.dimm_type
                mem['DRAM_Vendor'] = item.dram_vendor
                mem['DRAM_Stepping'] = item.dram_stepping
                mem['DRAM_Type'] = item.dram_type
                mem['DRAM_Manufacturing_Part_Number'] = item.dram_manufacturing_part_number
                mem['DIMM_Serial_Number'] = item.dimm_serial_number
                mem['DRAM_Manufacturing_Date'] = item.dram_manufacturing_date
                mem['DRAM_Max_Frequency'] = item.dram_max_frequency
                mem['DRAM_Density'] = item.dram_density
                mem['Device_Width'] = item.device_width
                mem['Device_Ranks'] = item.device_ranks
                list_of_memory.append(mem)

        if hasattr(self.device, 'pcie') and self.device.get_pcie:
            pcie = OrderedDict()
            for item in self.device.pcie:
                pcie = item
                list_of_pcie.append(pcie)

        boardinfo_dict["SiliconFamily"] = self.silicon_family
        boardinfo_dict["Units"] = list_of_units
        boardinfo_dict["PchUnits"] = list_of_pch
        boardinfo_dict["Packages"] = list_of_packages
        boardinfo_dict['Memory'] = list_of_memory
        boardinfo_dict['PCIe'] = list_of_pcie
        if hasattr(self.device, "MicroCodePatch"):
            boardinfo_dict['MicroCodePatch'] = self.device.MicroCodePatch
        if hasattr(self.device, 'total_mem_size'):
            boardinfo_dict["ActiveMemorySize"] = self.device.total_mem_size
        if hasattr(self.device, "PlatformId"):
            boardinfo_dict['PlatformId'] = self.device.PlatformId
        boardinfo_dict['NumOfCores'] = total_cores
        boardinfo_dict['NumOfThreads'] = total_threads
        if self.device is not None and hasattr(self.device, '_ZephyrId'):
            boardinfo_dict['zephyr_id'] = self.device.zephyr_id
        if self.device is not None and hasattr(self.device, '_BiosVersion'):
            boardinfo_dict['bios_version'] = self.device.bios_version
        if self.device is not None and hasattr(self.device, '_LagunaNumber'):
            boardinfo_dict['IoCards'] = self.device.laguna_number
        if self.device is not None and hasattr(self.device, 'kfir_card'):
            boardinfo_dict['Kfir'] = self.device.kfir_card
        if self is not None and hasattr(self, '_BoardType'):
            boardinfo_dict['BoardType'] = self._BoardType
        if self is not None and hasattr(self, '_BoardSerial'):
            boardinfo_dict['BoardSerial'] = self._BoardSerial
        if self.device is not None and hasattr(self.device, 'sic_result'):
            boardinfo_dict["SIC"] = self.device.sic_result    
        boardinfo_dict['Probe'] = Device.detect_connected_devices()
        errors = errors_handler.ErrorsHandler.get_errors()
        if errors != {}:
            boardinfo_dict['InternalErrors'] = errors
        return boardinfo_dict

    def set_silicon_family(self):
        try:
            if os.getenv("SiliconFamily") is not None and os.getenv("SiliconFamily") != '':
                silicon_family = os.getenv("SiliconFamily")
                silicon_family = self.silicon_family_wa(silicon_family)
            else:
                silicon_family = self.auto_detect_product()
            logger.info("silicon_family is {}".format(silicon_family))
            if silicon_family is not None and silicon_family != '':
                self.silicon_family = silicon_family
            else:
                self.silicon_family = ''
                error_msg = 'Failed to detect silicon family'
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as ex:
            errors_handler.ErrorsHandler.add_error('Board', str(ex))
            return None

    def silicon_family_wa(self, silicon_family):
        if silicon_family == 'CFL_8+2':
            return 'CFL'
        if silicon_family == 'SPR_HBM':
            return 'SPRHBM'
        return silicon_family

    def get_project_instance(self, avoid_forcereconfig):
        try:
            if self.silicon_family is None or self.silicon_family == '':
                raise Exception("No supported silicon family was detected therefore can not load any project")
            logger.info("getting project instance of {}".format(self.silicon_family))
            try:
                logger.info("{} project was detected".format(self.silicon_family))
                product = importlib.import_module('Project.{0}'.format(self.silicon_family))
                return eval(r'product.{0}({1})'.format(self.silicon_family, avoid_forcereconfig))
            except Exception as e:
                error_msg = 'Failed to load relevant module for product {0}'.format(product)
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as ex:
            errors_handler.ErrorsHandler.add_error('Board', str(ex))
            return None

    def create_json(self, boardinfo_dict):
        out_path = self.get_configuration_path()
        if not os.path.exists(out_path):
            os.makedirs(out_path)
            logger.info("Directory: " + out_path + " Created ")
        else:
            logger.info("Directory: " + out_path + " already exists")
        import io
        json_output_file = out_path + r'\data.json'
        with io.open(json_output_file, 'w', encoding="utf-8") as outfile:
            try: # Python 3 compatibility hack
                unicode('')
            except NameError:
                unicode = str
            outfile.write(unicode(json.dumps(boardinfo_dict, ensure_ascii=False, indent=4)))
        if os.path.exists(json_output_file):
            cm_dump_path = self.get_cm_data_dump_path()
            if not os.path.exists(cm_dump_path):
                os.makedirs(cm_dump_path)
            shutil.copy2(json_output_file,cm_dump_path)


    def init_boardinfo_dictionary(self):
        boardinfo_dict = OrderedDict()
        boardinfo_dict['Source'] = 'BoardInfo'
        boardinfo_dict['SiliconFamily'] = ''
        boardinfo_dict['NumOfCores'] = 0
        boardinfo_dict['NumOfThreads'] = 0
        boardinfo_dict['Units'] = []
        boardinfo_dict['PchUnits'] = []
        boardinfo_dict['Memory'] = []
        boardinfo_dict['PCIe'] = []
        boardinfo_dict['zephyr_id'] = ''
        boardinfo_dict['bios_version'] = ''
        boardinfo_dict['BoardType'] = ''
        boardinfo_dict['BoardSerial'] = ''
        boardinfo_dict['MicroCodePatch'] = ''
        boardinfo_dict['IoCards'] = ''
        boardinfo_dict['Kfir'] = ''
        boardinfo_dict['Probe'] = ''
        boardinfo_dict['ActiveMemorySize'] = ''
        boardinfo_dict['PlatformId'] = ''
        self.boardinfo_dict = boardinfo_dict

    def get_configuration_path(self):
        try:
            config = configparser.RawConfigParser()
            path = os.path.join(os.path.dirname(__file__), 'Configuration.ini')
            logger.info('About to parse xml file: {}'.format(path))
            config.read(path)
            return config.get('output', 'output_path')
        except Exception as ex:
            error_msg = 'could not get path from configuration file "Configuration.ini" {}'.format(str(ex))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return None


    def get_sic_items_list(self):
        try:
            config = configparser.RawConfigParser()
            path = os.path.join(os.path.dirname(__file__), 'Configuration.ini')
            logger.info('About to parse xml file: {}'.format(path))
            config.read(path)
            item_str = config.get('items', 'sic_items')
            return item_str.split(",")
        except Exception as ex:
            error_msg = 'could not get sic items list from configuration file "Configuration.ini" {}'.format(str(ex))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('sic_info', error_msg)
            return None

    def get_cm_data_dump_path(self):
        try:
            config = configparser.RawConfigParser()
            path = os.path.join(os.path.dirname(__file__), 'Configuration.ini')
            logger.info('About to parse xml file: {}'.format(path))
            config.read(path)
            return config.get('output', 'cm_data_dump_path')
        except Exception as ex:
            error_msg = 'could not get path from configuration file "Configuration.ini" {}'.format(str(ex))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return None

    def auto_detect_product(self):
        try:
            logger.info('SiliconFamily environment variable is not defined. Attempting to connect to OpenIPC to '
                        'detect product')
            import ipccli
            itp = ipccli.baseaccess()
            uncores_list = []
            detected_product = ''
            if itp.uncores and len(itp.uncores) > 0:
                for uncore in itp.uncores:
                    tmp = uncore.device.devicetype.split('_')[0]
                    if tmp not in uncores_list:
                        uncores_list.append(tmp.upper())
            else:
                relevant_devices = itp.devicelist.search("cltap")
                for dev in relevant_devices:
                    uncore_name = dev.devicetype.split('_')[0].upper()
                    # TODO: ARL returns MTL uncore. This is a WA for detecting ARL. Need to verify in PO if there is a better way to address it
                    if uncore_name == "MTL": #Need to check if the silicon is ARL or MTL which shares the same uncore device name
                        if len(itp.devicelist.search("ARL0_CDIE_CDU0")) > 0:
                            uncore_name = "ARL"
                    uncores_list.append(uncore_name)
            logger.info('Detected the following uncores: {}'.format(uncores_list))
            logger.info('Going to check if any of the detected uncores are supported projects in BoardInfo')
            supported_projects = self.get_supported_projects()
            logger.info('List of supported projects by BoardInfo: {}'.format(supported_projects))
            for uncore in uncores_list:
                if uncore in supported_projects:
                    return uncore
            if detected_product == '':
                error_msg = 'Failed to auto detect project using OpenIPC'
                raise Exception(error_msg)
        except Exception as ex:
            errors_handler.ErrorsHandler.add_error('Board', str(ex))
            return None

    def get_supported_projects(self):
        return [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(Project.__file__)])]

    @staticmethod
    def _report_unit_location(boardinfo_dict):
        try:
            uls = ULS(logger)
            for unit in boardinfo_dict['Units']:
                vid = unit['UnitSerial']
                uls.report_location(vid=vid) if vid else None
        except Exception as e:
            msg = '{0} Error reporting location: {1}'.format((__name__, e))
            logger.warning(msg)
            errors_handler.ErrorsHandler.add_error('General', msg)


def get_log_path():
    try:
        config = configparser.RawConfigParser()
        path = os.path.join(os.path.dirname(__file__), 'Configuration.ini')
        config.read(path)
        return config.get('output', 'log_path')
    except Exception as e:
        error_msg = 'could not get log path from configuration file "Configuration.ini" {}'.format(str(e))
        errors_handler.ErrorsHandler.add_error('Board', error_msg)
        return None


def create_lock_file():
    delete_lock_file()
    lock_file = r'C:\Temp\BoardInfo.lock'
    with open(lock_file, 'w') as f:
        f.write('')


def delete_lock_file():
    lock_file = r'C:\Temp\BoardInfo.lock'
    if (os.path.exists(lock_file)):
        try:
            os.remove(lock_file)
        except:
            logger.warning("Failed to delete lock file")


def create_board_info(avoid_forcereconfig=False, skip_closing_openipc=False, intrusive=False, write_json=True,
                      sic_enabled=False, sic_items_list=None, is_discrete=True):
    bi = None
    try:
        create_lock_file()
        logPath = get_log_path()
        loggerHelper.set_logger(logPath, 'Log_{}.log'.format(datetime.datetime.now().strftime("%d.%m.%Y__%H.%M.%S")))
        global logger
        logger = logging.getLogger('BoardInfoLog')
        logger.info("initializing BoardInfo")
        if not os.path.exists(logPath):
            os.makedirs(logPath)
            logger.info("Directory: " + logPath + " Created ")
        else:
            logger.info("Directory: " + logPath + " already exists")
        if isinstance(sic_items_list, list):
            sic_items_list = dict.fromkeys(sic_items_list, None)
        bi = BoardInfo(avoid_forcereconfig, skip_closing_openipc, intrusive, write_json, sic_enabled=sic_enabled,
                       sic_items_dict=sic_items_list, is_discrete=is_discrete)
    except Exception as e:
        err = 'error {}'.format(str(e))
        logger.error('Error on main {}'.format(err))
    finally:
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        delete_lock_file()
    return bi


def board_info_api(intrusive=True, enable_sic=True, write_json=True, sic_items_list=None, is_discrete=True, new_items_def=None):
    if sic_items_list:
        intrusive = True
    if new_items_def:
        add_info_items(new_items_def)
    bi = create_board_info(avoid_forcereconfig=False, skip_closing_openipc=False, intrusive=intrusive,
                           sic_enabled=enable_sic, write_json=write_json, sic_items_list=sic_items_list,
                           is_discrete=is_discrete)
    return bi.get()


def main(avoid_forcereconfig=False, skip_closing_openipc=False, intrusive=False, sic=False):
    create_board_info(avoid_forcereconfig, skip_closing_openipc, intrusive,
                      write_json=True, sic_enabled=sic, sic_items_list=None, is_discrete=True)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intrusive", help="This flag uses halt to gathering PCIe info. "
                                            "Usage: BoardInfo.py --intrusive", default=False, action='store_true')
    parser.add_argument("--sic", help="This flag enables the sic based scaning flow. It requires to pass down also the --intrusive argument"
                                            "Usage: BoardInfo.py --intrusive --sic", default=False, action='store_true')
    return parser.parse_known_args()


if __name__ == '__main__':
    args, unknown_args = parse_args()
    main(intrusive=args.intrusive, sic=args.sic)
