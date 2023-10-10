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
import pcie
import yaml
from yaml.loader import SafeLoader
import os

logger = logging.getLogger('BoardInfoLog')


class SPR(Device.Device):
    def __init__(self, avoid_forcereconfig=False):
        self.pcie = []
        self.avoid_forcereconfig = avoid_forcereconfig
        logger.info("initializing SPR project")
        return None

    def getCpuInfo(self):
        return self.get_unit_info()

    def get_itp(self):
        return IPC.IPC()

    def get_unit_info(self):
        return super(SPR, self).get_unit_info_lock_device()

    def _get_pch(self, itp):
        try:
            logger.info("Get pch (SPR)")
            if hasattr(itp.chipsets[0], 'stepping'):
                step = itp.chipsets[0].stepping
            elif hasattr(itp.chipsets[0].device, 'stepping'):
                step = itp.chipsets[0].device.stepping
            if hasattr(itp.chipsets[0], 'devicetype'):
                typ = itp.chipsets[0].devicetype
            elif hasattr(itp.chipsets[0].device, 'devicetype'):
                typ = itp.chipsets[0].device.devicetype
            unit_info = UnitInfo(step, typ, "")
            import namednodes
            loggerHelper.initilaizeLoggerAgain()
            from ipccli import BitData
            if typ is not None and typ.lower() == 'adp':
                adl_instance = ADL.ADL()
                return adl_instance._get_pch(itp)
            namednodes.settings.PROJECT = "emmitsburg"
            namednodes.sv.initialize(True)
            pch = namednodes.sv.pch.get_all()[0]
            qdf_value = pch.taps.dfx_secagg0.qdf
            if qdf_value:
                import binascii
                unit_info.qdf = binascii.unhexlify('%08x' % qdf_value).decode('utf8')
            from ipccli import BitData
            ult_fuses = BitData(56, 0)
            ult_fuses[55:32] = int(pch.taps.dfx_secagg0.ult_1)
            ult_fuses[31:0] = int(pch.taps.dfx_secagg0.ult_0)
            if ult_fuses == 0 or ult_fuses is None:
                raise Exception("Failed to read pch ult tap registers.")
            fab_id = [("D2", '2'), ("11", 'E'), ("12", 'F'), ("20", 'Y'), ("IFO", 'G'), ("68", 'U'),
                      ("24", 'H'), ("17", 'X'), ("18", 'K'), ("22", 'A'), ("D1C", 'Z'), ("11X", 'W'),
                      ("D1D", 'D'), ("F28", 'N'), ("F32", 'L'), ("Reserved", 'R')]
            ult_fab = fab_id[(ult_fuses >> 52) & 0xF][1]
            ult_yr = '{0:01d}'.format(((ult_fuses >> 48) & 0xF).ToUInt32())
            ult_ww = '{0:02d}'.format(((ult_fuses >> 42) & 0x3F).ToUInt32())
            ult_lot = '{0:03d}'.format(((ult_fuses >> 32) & 0x3FF).ToUInt32())
            ult_eid = chr(((ult_fuses >> 26) & 0x3F) + 0x30) if (((ult_fuses >> 26) & 0x3F) < 10) else chr(
                ((ult_fuses >> 26) & 0x3F) + 0x41 - 0xA)
            ult_waf = '{0:03d}'.format(((ult_fuses >> 16) & 0x3FF).ToUInt32())
            ult_x = (ult_fuses >> 8) & 0xFF
            ult_y = (ult_fuses >> 0) & 0xFF
            sample_lot = ult_fab + ult_yr + ult_ww + ult_lot + ult_eid
            wafer = ult_waf
            x_loc = "-" if (ult_x & 0x80 != 0) else "+"
            x_loc = x_loc + str(ult_x.ToUInt32() & 0x7f)
            y_loc = "-" if (ult_y & 0x80 != 0) else "+"
            y_loc = y_loc + str(ult_y.ToUInt32() & 0x7f)
            ult = sample_lot + '_' + wafer + '_' + (x_loc) + '_' + str(y_loc)
            pch_ult = ult.replace('_', ' ').replace('+', '')
            unit_info.Ult = pch_ult
            return unit_info
        except Exception as e:
            error_msg = r"_Get_Pch exception on SPR:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('PCH', error_msg)
            return None
        finally:
            try:
                namednodes.settings.PROJECT = "__PYSVCONFIG__"
                namednodes.sv.initialize(True)
            except Exception as e:
                error_msg = r"_Get_Pch failed to restore namednodes to pythonsv default:  {}".format(str(e))
                logger.error(error_msg)
                errors_handler.ErrorsHandler.add_error('PCH', error_msg)

    def get_straps(self, count):
        try:
            import namednodes
            sv = namednodes.sv
            sockets = sv.socket.get_all()
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
            
    def get_memory(self):
        super(SPR, self).get_memory()
        self.get_activememory()
        
    def get_activememory(self):
        import pysvtools.bitmanip as bm
        import sapphirerapids.mc.sprAddressTranslator as at
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
        
        
    def get_pcie(self):
        try:
            logger.info('Scanning All PCIe cards.')
            import pysvtools.pciedebug.ltssm as ltssm
            from common import baseaccess
            base = baseaccess.baseaccess()
            cards_mapping_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pcie', 'cards_mapping.yaml')
            list_items = ['Socket', 'Slot', 'Width', 'Gen', 'SecBus', 'SubBus']
            list_pcie = []
            with open(cards_mapping_path) as f:
                pcieconf = yaml.load(f, Loader=SafeLoader)
            pcie = ltssm.getavailableports()
            for item in pcie:
                dct_pcie = dict((key, value) if type(value) in [int, str] else (key, value.value) for (key, value) in
                                zip(list_items, item))
                revid = hex(base.pcicfg(dct_pcie['SecBus'], 0, 0, 8, 2))
                devid = hex(base.pcicfg(dct_pcie['SecBus'], 0, 0, 2, 2))
                if 'dmi' in dct_pcie['Slot']: continue
                else:
                    recognized = False
                    for i in pcieconf:
                        if i['DeviceID'] == devid and i['RevID'] == revid:
                            dct_pcie.update(i)
                            recognized = True
                            break
                    if not recognized:
                        dct_pcie.update({'CardName': 'Unknown'})
                        logger.warning(f'Failed to find card name for DeviceID: {devid} and RevID: {revid} in the pcie mapping config file')
                dct_pcie['SecBus'] = hex(dct_pcie['SecBus'])
                dct_pcie['SubBus'] = hex(dct_pcie['SubBus'])
                list_pcie.append(dct_pcie)
            self.pcie = list_pcie
        except Exception as e:
            error_msg = r'Failed to read PCIe cards: {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('PCIe', error_msg)

    def _get_cpu(self, itp):
        try:
            unit_info_list = []
            count = -1
            logger.info("Get cpu (SPR)")
            for uncore in itp.uncores:
                try:
                    count += 1
                    import namednodes
                    loggerHelper.initilaizeLoggerAgain()
                    unit_info = UnitInfo(uncore.device.stepping, uncore.device.devicetype, None)
                    fuse_obj = namednodes.sv.socket.getAll()[count].tiles[0].fuses
                    fuse_obj.load_fuse_ram()
                    cpu_ult = fuse_obj.dfxagg.ult_fuse
                    qdf = fuse_obj.dfxagg.qdf_fuse
                    unit_info.Straps = self.get_straps(count)
                    if qdf:
                        qdf = _binascii.unhexlify('%08x' % qdf).decode('utf8')
                        unit_info.qdf = qdf
                    unit_info.socket_number = count
                    unit_info.NPKAddress = str(self.getNPKAddress(count))
                    unit_info.CpuId = str(self.getCpuId(count))
                    if cpu_ult == 0x0 or cpu_ult is None:
                        unit_info_list.append(unit_info)
                        continue
                    ult_str = self._decode_ult(cpu_ult)
                    if ult_str == "":
                        logger.error("can not decode cpu ult info")
                        unit_info_list.append(unit_info)
                        continue
                    unit_info.Ult = ult_str
                    unit_info_list.append(unit_info)
                    continue
                except Exception as e:
                    unit_info_list.append(unit_info)
                    error_msg = r"Failed to detect CPU{}: {}".format(str(count), e)
                    logger.error(error_msg)
            return unit_info_list
        except Exception as e:
            error_msg = r"_Get_Cpu exception on SPR:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            unit_info_list = [UnitInfo("", "", "", "")]
            return unit_info_list

    def getMicroCodePatch(self):
        try:
            logger.info("Getting MicroCodePatch (SPR)")
            from DebugSwInterface.IPC import IPC
            micro = str(IPC.itp.threads[0].crb(1929)).split()[1]
            return micro
        except Exception as e:
            error_msg = r'MicroCodePatch - OpenIPC - {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return ''

    def ensure_unlock(self, itp):
        spr_device = ''
        return super(SPR, self).ensure_unlock(itp, spr_device)

    def getPlatformInfo(self):
        return super(SPR, self).getPlatformInfo()

    def getDokPlatformInfo(self):
        return super(SPR, self).getDokPlatformInfo()

    def get_platform_id(self):
        try:
            from namednodes import sv
            cpu = sv.socket.get_all()[0]
            platform_id_cr = cpu.uncore.punit.platform_id
            logger.info(f'Platform ID CR value is {platform_id_cr}')
            return super(SPR, self).get_platform_id(platform_id_cr)
        except Exception as e:
            error_msg = r'Error reading platform_id -  {}'.format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('Board', error_msg)
            return ''

    def getIfwiInfo(self):
        return super(SPR, self).getIfwiInfo()

    def getNPKAddress(self, index):
        try:
            from namednodes import sv
            cpu = sv.socket.get_all()[index]
            i = cpu.uncore.northpeak0.scrpd1
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
            cpus = sv.socket.get_all()
            currentCStateValue = {}
            for cpu in cpus:
                socket = cpus.index(cpu)
                cpu_command = f'cpus[{socket}].uncore.punit.dfx_ctrl_unprotected.core_cstate_limit'
                logger.info(f"Getting current CState value from socket {cpus.index(cpu)}")
                currentCStateValue[cpu_command] = eval(cpu_command)
                logger.info("Current CState value is {}".format(str(currentCStateValue[cpu_command])))
            return currentCStateValue
        except Exception as e:
            error_msg = r"_get_current_cstate exception on ADL:  {}".format(str(e))
            logger.error(error_msg)
            errors_handler.ErrorsHandler.add_error('CPU', error_msg)
            return None

    def _set_cstate(self, cstate, required_value=None):
        try:
            logger.info("Setting CState value = {}".format(str(cstate)))
            from namednodes import sv
            loggerHelper.initilaizeLoggerAgain()
            cpus = sv.socket.get_all()
            for key, value in cstate.items():
                if key.startswith('cpu'):
                    if required_value is None:
                        command_str = f'{key}={value}'
                    else:
                        command_str = f'{key}={required_value}'
                    exec(command_str)
            logger.info("Successfully changed CState value to {}".format(str(cstate)))
        except Exception as e:
            error_msg = r"_set_cstate exception on SPR:  {}".format(str(e))
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
