from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
import errors_handler
from Project.SKL import SKL
import UnitInfo
import logging
import os
import yaml
from yaml import SafeLoader

logger = logging.getLogger('BoardInfoLog')


class CLX(SKL):
    def __init__(self, avoid_forcereconfig=False):
        self.avoid_forcereconfig = avoid_forcereconfig
        self.initializeSKL()
        return None

    def getCpuInfo(self):
        return self.get_unit_info()

    def get_unit_info(self):
        result = super(CLX, self).get_unit_info()
        return result

    def initializeSKL(self):
        super(CLX, self).initializeSKL(device_list_index=0, uncore_index=0)

    def get_platform_id(self):
        return super(CLX, self).get_platform_id()

    def getMicroCodePatch(self):
        return super(CLX, self).getMicroCodePatch()
        
    def get_straps(self, count):
        try:
            import components.socket
            sockets = components.socket.getAll()
            strap_list = []
            if sockets[count].pcudata.io_poc_reset_straps.bist_enable != 1:
                strap_list.append('Strap_BIST_ENABLE: OFF')
            else:
                strap_list.append('Strap_BIST_ENABLE: ON')

            if sockets[count].pcudata.io_poc_reset_straps.safe_mode_boot == 0:
                strap_list.append('Strap_SAFE_MODE_BOOT: OFF')
            else:
                strap_list.append('Strap_SAFE_MODE_BOOT: ON')

            if sockets[count].pcudata.io_poc_reset_straps.txt_plten != 1:
                strap_list.append('Strap_TXT_PLT_EN: OFF')
            else:
                strap_list.append('Strap_TXT_PLT_EN: ON')

            if sockets[count].pcudata.io_poc_reset_straps.txt_agent != 1:
                strap_list.append('Strap_TXT_AGENT: OFF')
            else:
                strap_list.append('Strap_TXT_AGENT: ON')
            return strap_list
        except Exception as e:
            error_msg = r'Failed to read platform straps: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Straps', error_msg)
            
    def get_memory(self):
        self.get_memoryinfo()
        self.get_activememory()
        
    def get_activememory(self):
        import pysvtools.bitmanip as bm
        import cascadelakex.mc.clxAddressTranslator as at
        activeMemSize = []
        processed_sockets = set()
        for mem_object in self.Memory:
            socket = mem_object.__dict__['socket']
            if socket in processed_sockets:
                continue
            processed_sockets.add(socket)
            try:
                logger.info('Scanning Active Memory Size for Socket{}.'.format(socket))
                act_mem_size = at.getActiveMemorySize(socket)
                readable_size = bm.number2readable(act_mem_size, 'G').coef
                activeMemSize.append(readable_size)
            except Exception as e:
                error_msg = r'Memory: {}'.format(str(e))
                logger.error(error_msg)
                errors_handler.ErrorsHandler.add_error('Failed to read active memory size:', error_msg)
        self.total_mem_size = sum(activeMemSize)
        self.total_mem_size = "{:.0f}Gb".format(self.total_mem_size)
        return self.total_mem_size
            
    def get_pcie(self):
        try:
            import cascadelakex.pcie.ltssm_clx as ltssm
            cards_mapping_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pcie', 'cards_mapping.yaml')
            list_items = ['Socket', 'Slot', 'Width', 'Gen']
            list_pcie = []
            with open(cards_mapping_path) as f:
                pcieconf = yaml.load(f, Loader=SafeLoader)
            pcie = ltssm.getavailableports()
            for item in pcie:
                if 'b2d00f0' in item[1]:
                    continue
                else:
                    dct_pcie = {key: (value if isinstance(value, (int, str)) else value.value if hasattr(value, 'value') else value) if not isinstance(value, int) else value for (key, value) in zip(list_items, item)}
                    dct_pcie['CardName'] = 'Unknown'
                    for it in pcieconf:
                        if it['Gen'] == dct_pcie['Gen']:
                            dct_pcie.update(it)
                            dct_pcie['CardName'] = it['CardName']
                            break
                    dct_pcie['Socket'] = item[0]
                    list_pcie.append(dct_pcie)
            self.pcie = list_pcie
        except Exception as e:
            error_msg = r'Failed to read pcie cards: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('PCIe', error_msg)

    def get_memoryinfo(self):
        try:
            import namednodes
            import memory.memory as memory_object
            import cascadelakex.mc.clxdimminfo as dimminfo
            all_eeprom = dimminfo.dimms.getAll()
            list_of_eeprom = []
            for eeprom in all_eeprom:
                mem_obj = memory_object.Memory()
                mem_obj.socket = eeprom.socket
                mem_obj.channel = eeprom.channel
                mem_obj.slot = eeprom.slot
                mem_obj.dram_manufacturing_date = str(eeprom.decode('DimmMfgDate')).strip()
                mem_obj.dimm_vendor = str(eeprom.decode('DimmMfg')).strip()
                mem_obj.dimm_register_vendor = str(eeprom.decode('RegMfg')).strip()
                mem_obj.dimm_type = str(eeprom.decode('ModuleType')).strip()
                mem_obj.dram_vendor = str(eeprom.decode('DramMfg')).strip()
                mem_obj.dram_stepping = str(eeprom.decode('DramStep')).strip()
                mem_obj.dram_type = str(eeprom.decode('DRAMtype')).strip()
                mem_obj.dram_manufacturing_part_number = str(eeprom.decode('DimmPartNum')).strip()
                mem_obj.dimm_serial_number = str(eeprom.decode('DimmSerNum')).strip()
                mem_obj.dram_max_frequency = str(eeprom.decode('MaxDDRFreq')).strip()
                if mem_obj.dram_type.upper() == 'DDRT2':
                    mem_obj.dram_density = str(eeprom.decode('NVMsize')).strip()
                    mem_obj.device_width = str(eeprom.decode('NvmDieWidth')).strip()
                    mem_obj.device_ranks = -1
                else:
                    mem_obj.dram_density = str(eeprom.decode('SDRAMsize')).strip()
                    mem_obj.device_width = str(eeprom.decode('DeviceWidth')).strip()
                    mem_obj.device_ranks = str(eeprom.decode('NumRanks')).strip()
                list_of_eeprom.append(mem_obj)
            self.Memory = list_of_eeprom
        except Exception as e:
            error_msg = r'Failed to read platform memory data: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Memory', error_msg)
            return []

    def _get_cpu(self, itp):
        try:
            cpu_info = []
            num_of_cpus = len(itp.uncores)
            for i in range(0, num_of_cpus):
                name = itp.uncores[i].name
                did = itp.devicelist[name].did
                for j in range(0, len(itp.devicelist)):
                    try:
                        if itp.devicelist[j].alias == name:
                            skl = super(CLX, self)._get_cpu(itp,did)
                            cpu_info.append(skl)
                    except Exception as e:
                        logger.debug("CLX get Cpu [" + str(i) + "] exception: " + str(e))
            return cpu_info
        except Exception as e:
            error_msg = r"_Get_Cpu exception on CNL:  {}".format(str(str(e)))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            return UnitInfo("", "", "", "")

    def _get_pch(self, itp):
        super(CLX, self)._get_pch(itp)

    def ensure_unlock(self, itp):
        clx_device = ''
        return super(CLX, self).ensure_unlock(itp, clx_device)

    def getPlatformInfo(self):
        import cascadelakex.fuse.clxFuseUtility as fu
        try:
            self.MicroCodePatch = self.getMicroCodePatch()
            logger.info("getting platform info")
            self.itp = self.get_itp()
            dic = []
            threads = 0
            unit_index = 0
            unit_name = ''
            while unit_index < 2:
                qdf = fu.fusedQDF()[unit_index]
                self.CpuInfo.Cpus[unit_index].qdf = qdf
                self.CpuInfo.Cpus[unit_index].socket_number = unit_index
                for t in self.itp.itp.threads:
                    if unit_name != str(t.name).split('_')[0]:
                        if unit_name != '':
                            # first core to be initialized
                            self.CpuInfo.Cpus[unit_index].num_of_threads = threads
                            self.CpuInfo.Cpus[unit_index].num_of_cores = len(dic)
                            unit_index += 1
                        unit_name = str(t.name).split('_')[0]
                        threads = 0
                        dic = []
                    temp = str(t.name).split('_')[1].split('_')[0]
                    if temp[1:].isdigit() and temp[0].upper() == 'C':
                        threads += 1
                        if not dic.__contains__(temp):
                            dic.append(temp)
                self.CpuInfo.Cpus[unit_index].num_of_threads = threads
                self.CpuInfo.Cpus[unit_index].num_of_cores = len(dic)
                self.CpuInfo.Cpus[unit_index].Straps = self.get_straps(unit_index)
                logger.info(
                    "unit[{}]: #cores={} #threads={}".format(unit_index, self.CpuInfo.Cpus[unit_index].num_of_cores,
                                                             self.CpuInfo.Cpus[unit_index].num_of_threads))
                unit_index += 1
                threads = 0
                dic = []

            logger.info("finished platform info: MicroCodePatch={}".format(self.MicroCodePatch))
        except Exception as e:
            error_msg = r'could not get num_of_cores and num_of_threads from itp: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)

    def getDokPlatformInfo(self):
        return super(CLX, self).getDokPlatformInfo()

    def getIfwiInfo(self):
        return super(CLX, self).getIfwiInfo()
