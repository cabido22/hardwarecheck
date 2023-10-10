from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import chr
from builtins import str
import loggerHelper
import UnitInfo
from DebugSwInterface import IPC
import errors_handler
from UnitInfo import Device
from unit_info import UnitInfo
import binascii as _binascii
import logging
from Project import ADL
import os
import yaml
from yaml import SafeLoader

logger = logging.getLogger('BoardInfoLog')


class CPX(Device.Device):
    def __init__(self, avoid_forcereconfig=False):
        self.avoid_forcereconfig = avoid_forcereconfig
        logger.info("initializing CPX project")
        return None

    def getCpuInfo(self):
        return self.get_unit_info()

    def get_itp(self):
        return IPC.IPC()

    def get_unit_info(self):
        return super(CPX, self).get_unit_info()

    def _get_pch(self, itp):
        pass

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
        import cooperlakex.mc.cpxAddressTranslator as at
        activeMemSize = []
        processed_sockets = set()
        for mem_object in self.Memory:
            socket = mem_object.__dict__['socket']
            if socket not in processed_sockets: 
                logger.info('Scanning Active Memory Size for Socket{}.'.format(socket))
                processed_sockets.add(socket)
            try:
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
            import cooperlakex.pcie.ltssm_cpx as ltssm
            cards_mapping_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pcie', 'cards_mapping.yaml')
            list_items = ['Socket', 'Slot', 'Width', 'Gen']
            list_pcie = []
            with open(cards_mapping_path) as f:
                pcieconf = yaml.load(f, Loader=SafeLoader)
            pcie = ltssm.getavailableports()
            for item in pcie:
                if 'dmi' in item[1]:
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
            import cooperlakex.mc.cpxdimminfo as dimminfo
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
        import components.socket
        import cooperlakex.toolext.bootscript.toolbox.fuse_utility as fuu
        cpu = components.socket.getAll()
        try:
            logger.info("Get cpu (CPX)")
            unit_info_list = []
            count = -1
            current_c_state_value = self._get_current_cstate()
            if current_c_state_value is None:
                raise Exception("Failed to get Current Cstate")
            logger.info("Current CState value is {}".format(str(current_c_state_value)))
            if current_c_state_value > 1:
                logger.info("Setting current CState value to 1")
                self._set_cstate(1)
            for uncores in itp.uncores:
                count += 1
                unit_info = UnitInfo(uncores.device.stepping, uncores.device.devicetype, None)
                unit_info.socket_number = count
                # This read requires halt and therefore it can be skipped for CPX
                # If it is required anyway, we can deal with it later
                # unit_info.NPKAddress = str(self.getNPKAddress(count))
                unit_info.CpuId = str(self.getCpuId(count))
                unit_info.Ult = str(fuu.getUlt(cpu[count])['textStr'].replace('_', ' '))
                new_did = itp.devicelist['CPX{}_UC0'.format(str(count))].did
                unit_info.Straps = self.get_straps(count)

                if new_did is None:
                    unit_info_list.append(unit_info)
                    continue
                cpu_ult = itp.irdrscan(int(new_did), 0x45, 56, None, itp.BitData(56, 0x00000000000000))
                if cpu_ult == 0x0 or cpu_ult is None:
                    # return unit_info
                    unit_info_list.append(unit_info)
                    continue  
                #ult_str = self._decode_ult(cpu_ult)
                if ult_str == "":
                    logger.error("can not decode cpu ult info")
                    # return unit_info
                    unit_info_list.append(unit_info)
                    continue
                return unit_info
                unit_info_list.append(unit_info)
                continue

            self._set_cstate(current_c_state_value)
            return unit_info_list
            
        except Exception as e:
            error_msg = r"_Get_Cpu exception on CPX:  {}".format(str(e))
            logger.error(error_msg)
            if current_c_state_value is not None:
                logger.warn(
                    "Reverting to original Cstate after exception,to value = {}".format(str(current_c_state_value)))
                self._set_cstate(current_c_state_value)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            unit_info_list = []
            unit_info_list.append(UnitInfo("", "", "", ""))
            return unit_info_list

    def getMicroCodePatch(self):
        try:
            logger.info("Getting MicroCodePatch (CPX)")
            import components.socket
            cpu = components.socket.getAll()[0]
            micro = str(cpu.core0.thread0.scp_patch_rev_id)
            return micro
        except Exception as e:
            error_msg = r'MicroCodePatch - OpenIPC - {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return ''

    def ensure_unlock(self, itp):
        # device is the parameter for itp unlock()
        cpx_device = 'CPX0_UC0'
        return super(CPX, self).ensure_unlock(itp, cpx_device)

    def getPlatformInfo(self):
        return super(CPX, self).getPlatformInfo()

    def get_platform_id(self):
        try:
            import components.socket
            cpu = components.socket.getAll()[0]
            platform_id_cr = cpu.uncore0.pcu_cr_platform_id
            logger.info(f'Platform ID CR value is {platform_id_cr}')
            return super(CPX, self).get_platform_id(platform_id_cr)
        except Exception as e:
            error_msg = r'Error reading platform_id -  {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return ''

    def getDokPlatformInfo(self):
        return super(CPX, self).getDokPlatformInfo()

    def getIfwiInfo(self):
        return super(CPX, self).getIfwiInfo()

    def getNPKAddress(self, index):
        try:
            loggerHelper.initilaizeLoggerAgain()
            import components.spch as spch
            sv_pch = spch.getAll()[0]
            i = sv_pch.npk.scrpd1
            i.get_value()
            return i
        except Exception as e:
            error_msg = r'Error getting NPKAddress -  {}'.format(str(e))
            logger.warn(error_msg)
            return ''

    def getCpuId(self, index):
        try:
            loggerHelper.initilaizeLoggerAgain()
            import components.socket
            cpu = components.socket.getAll()[0]
            i = cpu.uncore0.vcu_cr_core_cpuid
            i.get_value()
            return i
        except Exception as e:
            error_msg = r'Error getting CPUID -  {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            return ''

    def _get_current_cstate(self):
        try:
            logger.info("Get current Cstate")
            import components.socket
            cpus = components.socket.getAll()
            for cpu in cpus:
                socket = cpus.index(cpu)
                cpu_command = str(cpus[socket].uncores.pcu_cr_dfx_ctrl_unprotected.core_cstate_limit[0])  # Carlos
                logger.info(f"Getting current CState value from socket {cpus.index(cpu)}")
                current_c_state_value = eval(cpu_command)
                logger.info("Current CState value is {}".format(str(current_c_state_value)))
            return current_c_state_value
        except Exception as e:
            error_msg = r"_get_current_cstate exception on ADL:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            return None

    def _set_cstate(self, cstate):
        try:
            logger.info("Setting CState value = {}".format(str(cstate)))
            loggerHelper.initilaizeLoggerAgain()
            import components.socket
            cpu = components.socket.getAll()
            cpu[0].uncores.pcu_cr_dfx_ctrl_unprotected.core_cstate_limit = cstate  # Carlos
            logger.info("Successfully changed CState value to {}".format(str(cstate)))
        except Exception as e:
            error_msg = r"_set_cstate exception on CPX:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)


    def limit_cstate(self, itp, value, previous):
        try:
            if itp.uncores.precondition.packageawake.defaultstate != value:
                itp.uncores.precondition.packageawake.defaultstate = value
                itp.uncores.precondition.packageawake.require(value)
            if itp.uncores.precondition.packageandcoresawake.defaultstate != value:
                itp.uncores.precondition.packageandcoresawake.defaultstate = value
                itp.uncores.precondition.packageandcoresawake.require(value)
            self._set_cstate(previous, 1)
        except Exception as e:
            error_msg = r"limit_cstate exception on ADL:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            raise e

    def read_current_cstate_limitation_status(self, itp):
        try:
            current = {
                'itp.uncores.precondition.packageawake.defaultstate':
                    itp.uncores.precondition.packageawake.defaultstate is True,
                'itp.uncores.precondition.packageandcoresawake.defaultstate':
                    itp.uncores.precondition.packageandcoresawake.defaultstate is True,
            }
            core_cstate_values = self._get_current_cstate()
            current.update(core_cstate_values)
            return current
        except Exception as e:
            error_msg = r"read_current_cstate_limitation_status exception:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)

    def restore_cstate(self, itp, previous):
        try:
            if previous[
                'itp.uncores.precondition.packageawake.defaultstate'] != itp.uncores.precondition.packageawake.defaultstate:
                itp.uncores.precondition.packageawake.defaultstate = previous[
                    'itp.uncores.precondition.packageawake.defaultstate']
                itp.uncores.precondition.packageawake.require(
                    previous['itp.uncores.precondition.packageawake.defaultstate'])
            if previous['itp.uncores.precondition.packageandcoresawake.defaultstate'] != bool(
                    itp.uncores.precondition.packageandcoresawake.defaultstate):
                itp.uncores.precondition.packageandcoresawake.defaultstate = previous[
                    'itp.uncores.precondition.packageandcoresawake.defaultstate']
                itp.uncores.precondition.packageandcoresawake.require(
                    previous['itp.uncores.precondition.packageandcoresawake.defaultstate'])
            self._set_cstate(previous)
        except Exception as e:
            error_msg = r"restore_cstate exception on ADL:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            raise e
