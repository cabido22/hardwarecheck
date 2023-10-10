from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import super
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import str
import loggerHelper
import UnitInfo
from DebugSwInterface import IPC
import errors_handler
from UnitInfo import Device
from unit_info import UnitInfo
import logging
import os
import yaml
from yaml import SafeLoader

logger = logging.getLogger('BoardInfoLog')


class ICX(Device.Device):
    def __init__(self, avoid_forcereconfig=False):
        self.avoid_forcereconfig = avoid_forcereconfig
        logger.info("initializing ICX project")
        return None

    def getCpuInfo(self):
        return self.get_unit_info()

    def get_itp(self):
        return IPC.IPC()

    def get_unit_info(self):
        return super(ICX, self).get_unit_info()

    def _get_pch(self, itp):
        pass
        
    def get_straps(self, count):
        try:
            import components.socket
            sockets = components.socket.getAll()
            strap_list = []
            if sockets[count].uncore.pcodeio_map.io_poc_reset_straps.bist_enable != 1:
                strap_list.append('Strap_BIST_ENABLE: OFF')
            else:
                strap_list.append('Strap_BIST_ENABLE: ON')

            if sockets[count].uncore.pcodeio_map.io_poc_reset_straps.safe_mode_boot == 0:
                strap_list.append('Strap_SAFE_MODE_BOOT: OFF')
            else:
                strap_list.append('Strap_SAFE_MODE_BOOT: ON')

            if sockets[count].uncore.pcodeio_map.io_poc_reset_straps.txt_plten != 1:
                strap_list.append('Strap_TXT_PLT_EN: OFF')
            else:
                strap_list.append('Strap_TXT_PLT_EN: ON')

            if sockets[count].uncore.pcodeio_map.io_poc_reset_straps.txt_agent != 1:
                strap_list.append('Strap_TXT_AGENT: OFF')
            else:
                strap_list.append('Strap_TXT_AGENT: ON')
            return strap_list
        except Exception as e:
            error_msg = r'Failed to read platform straps: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Straps', error_msg)

    def get_pcie(self):
        try:
            import icelakex.pcie.ltssm_icx as ltssm
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
            
    # activeMemSize = []        
    # def get_activememsize(self, count):
        # global activeMemSize
        # if count == 0:
            # activeMemSize = []
        # try:
            # logger.info('Scanning Active Memory Size for Unit{}.'.format(count))
            # import pysvtools.bitmanip as bm
            # import icelakex.mc.xnmAddressTranslator as at
            # act_mem_size = at.get_active_memory_size(count)
            # readable_size = bm.number2readable(act_mem_size[0], 'G').coef
            # activeMemSize.append(readable_size)
        # except Exception as e:
            # error_msg = r'Failed to read Active Memory Size: {}'.format(str(e))
            # logger.error(error_msg)
            # errors_handler.ErrorsHandler.add_error('Active Memory Size:', error_msg)
        # self.total_mem_size = sum(activeMemSize)
        # self.total_mem_size = "{:.0f}Gb".format(self.total_mem_size)
        # return self.total_mem_size
        
    def get_activememory(self):
        import pysvtools.bitmanip as bm
        import icelakex.mc.xnmAddressTranslator as at
        super(ICX, self).get_memory()
        activeMemSize = []
        processed_sockets = set()
        for mem_object in self.Memory:
            socket = mem_object.__dict__['socket']
            if socket in processed_sockets:
                continue
            processed_sockets.add(socket)
            try:
                logger.info('Scanning Active Memory Size for Socket{}.'.format(socket))
                act_mem_size = at.get_active_memory_size(socket)
                readable_size = bm.number2readable(act_mem_size[0], 'G').coef
                activeMemSize.append(readable_size)
            except Exception as e:
                error_msg = r'Memory: {}'.format(str(e))
                logger.error(error_msg)
                errors_handler.ErrorsHandler.add_error('Failed to read active memory size:', error_msg)
        self.total_mem_size = sum(activeMemSize)
        self.total_mem_size = "{:.0f}Gb".format(self.total_mem_size)
        return self.total_mem_size

    def _get_cpu(self, itp):
        try:
            logger.info("Get cpu (ICX)")
            unit_info_list = []
            count = -1
            current_c_state_value = self._get_current_cstate()
            if current_c_state_value is None:
                raise Exception("Failed to get Current Cstate")
            logger.info("Current CState value is {}".format(str(current_c_state_value)))
            if current_c_state_value > 1:
                logger.info("Setting current CState value to 1")
                self._set_cstate(1)
            for uncore in itp.uncores:
                count += 1
                unit_info = UnitInfo(uncore.device.stepping, uncore.device.devicetype, None)
                unit_info.socket_number = count
                unit_info.NPKAddress = str(self.getNPKAddress(count))
                unit_info.CpuId = str(self.getCpuId(count))
                new_did = itp.devicelist['ICX{}_AGG0'.format(str(count))].did
                unit_info.Straps = self.get_straps(count)
                if new_did is None:
                    unit_info_list.append(unit_info)
                    continue
                cpu_ult = itp.irdrscan(int(new_did), 0x45, 56, None, itp.BitData(56, 0x00000000000000))
                if cpu_ult == 0x0 or cpu_ult is None:
                    # return unit_info
                    unit_info_list.append(unit_info)
                    continue
                ult_str = self._decode_ult(cpu_ult)
                if ult_str == "":
                    logger.error("can not decode cpu ult info")
                    # return unit_info
                    unit_info_list.append(unit_info)
                    continue
                unit_info.Ult = ult_str
                # return unit_info
                unit_info_list.append(unit_info)
                continue
            self._set_cstate(current_c_state_value)
            return unit_info_list
        except Exception as e:
            error_msg = r"_Get_Cpu exception on ICX:  {}".format(str(e))
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
            logger.info("Getting MicroCodePatch (ICX)")
            from DebugSwInterface.IPC import IPC
            micro = str(IPC.itp.threads[0].crb(1929)).split()[1]
            return micro
        except Exception as e:
            error_msg = r'MicroCodePatch - OpenIPC - {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return ''

    def ensure_unlock(self, itp):
        # device is the parameter for itp unlock()
        icx_device = 'ICX0_CLTAP0'
        return super(ICX, self).ensure_unlock(itp, icx_device)

    def getPlatformInfo(self):
        return super(ICX, self).getPlatformInfo()

    def get_platform_id(self):
        try:
            from namednodes import sv
            cpu = sv.socket.get_all()[0]
            platform_id_cr = cpu.uncore.punit.platform_id
            logger.info(f'Platform ID CR value is {platform_id_cr}')
            return super(ICX, self).get_platform_id(platform_id_cr)
        except Exception as e:
            error_msg = r'Error reading platform_id -  {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return ''

    def getDokPlatformInfo(self):
        return super(ICX, self).getDokPlatformInfo()

    def getIfwiInfo(self):
        return super(ICX, self).getIfwiInfo()

    def getNPKAddress(self, index):
        try:
            from namednodes import sv
            loggerHelper.initilaizeLoggerAgain()
            cpu = sv.socket.get_all()[index]
            i = cpu.uncore.northpeak.scrpd1
            i.get_value()
            return i
        except Exception as e:
            error_msg = r'Error getting NPKAddress -  {}'.format(str(e))
            logger.warn(error_msg)
            return ''

    def getCpuId(self, index):
        try:
            from namednodes import sv
            loggerHelper.initilaizeLoggerAgain()
            cpu = sv.socket.get_all()[index]
            i = cpu.uncore.punit.core_cpuid
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
            from namednodes import sv
            loggerHelper.initilaizeLoggerAgain()
            cpu = sv.socket.get_all()[0]
            logger.info("Getting current CState value")
            current_c_state_value = cpu.uncore.punit.dfx_ctrl_unprotected.core_cstate_limit
            logger.info("Current CState value is {}".format(str(current_c_state_value)))
            return current_c_state_value
        except Exception as e:
            error_msg = r"_get_current_cstate exception on ICX:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            return None

    def _set_cstate(self, cstate):
        try:
            logger.info("Setting CState value = {}".format(str(cstate)))
            from namednodes import sv
            loggerHelper.initilaizeLoggerAgain()
            cpu = sv.socket.get_all()
            cpu[0].uncore.punit.dfx_ctrl_unprotected.core_cstate_limit = cstate
            for socket in cpu:
                socket.fuses.load_fuse_ram()
            logger.info("Successfully changed CState value to {}".format(str(cstate)))
        except Exception as e:
            error_msg = r"_set_cstate exception on ICX:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
