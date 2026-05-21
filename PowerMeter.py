# -*- coding: utf-8 -*-
import struct
import time
import logging
from pymodbus.client import ModbusSerialClient

# 日誌配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODBUS_BAUDRATE = 9600
MODBUS_PARITY = "N"
MODBUS_STOPBITS = 1
MODBUS_BYTESIZE = 8
MODBUS_TIMEOUT = 1

# 設備配置參數
DEVICE_CONFIGS = {
    "dae_PM210": {
        "registers": {
            "voltage_r_s": (26, 2, 0.1),
            "voltage_s_t": (28, 2, 0.1),
            "voltage_t_r": (30, 2, 0.1),
            "current_r": (32, 2, 0.001),
            "current_s": (34, 2, 0.001),
            "current_t": (36, 2, 0.001),
            "frequency": (44, 2, 0.1),
            "power": (38, 2, 0.001),
            "power_kva": (40, 2, 0.001),
            "pf": (123, 1, 0.001),
            "energy": (86, 2, 0.01),
            "immediate_demand": (52, 2, 0.001),
        },
        "decimals": {
            "voltage_r_s": 1, "voltage_s_t": 1, "voltage_t_r": 1,
            "current_r": 1, "current_s": 1, "current_t": 1,
            "frequency": 1, "power": 1, "power_kva": 1,
            "pf": 1, "energy": 1, "immediate_demand": 2,
        }
    },
    "adtek_cpm12d": {
        "registers": {
            "voltage_r_s": (0x0131, 2, 0.1),  # 32-bit unsigned，需要除以 10
            "voltage_s_t": (0x0133, 2, 0.1),
            "voltage_t_r": (0x0135, 2, 0.1),
            "current_r": (0x0141, 2, 0.001),  # 需要除以 1000
            "current_s": (0x0143, 2, 0.001),
            "current_t": (0x0145, 2, 0.001),
            "frequency": (0x0130, 1, 0.01),
            "power": (0x0151, 2, 0.001, "signed"),  # 32-bit signed，需要除以 1000
            "power_kva": (0x0161, 2, 0.001, "signed"),
            "pf": (0x0166, 1, 0.001, "signed"),  # 有符號，需要除以 1000
            "energy": (0x0185, 2, 0.1),  # 需要除以 100
            "immediate_demand": (0x016A, 2, 0.001),
        },
        "decimals": {
            "voltage_r_s": 1, "voltage_s_t": 1, "voltage_t_r": 1,
            "current_r": 2, "current_s": 2, "current_t": 2,
            "frequency": 2, "power": 2, "power_kva": 2,
            "pf": 3, "energy": 2, "immediate_demand": 3,
        }
    }
}

class MeterReader:
    def __init__(
        self,
        baudrate=MODBUS_BAUDRATE,
        parity=MODBUS_PARITY,
        stopbits=MODBUS_STOPBITS,
        bytesize=MODBUS_BYTESIZE,
        timeout=MODBUS_TIMEOUT,
        serial_config_getter=None,
    ):
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.clients = {}
        self.serial_config_getter = serial_config_getter

    def _get_client(self, port):
        if port not in self.clients:
            cfg = self.serial_config_getter(port) if self.serial_config_getter else {}
            self.clients[port] = ModbusSerialClient(
                port=port,
                baudrate=cfg.get('baudrate', self.baudrate),
                parity=cfg.get('parity', self.parity),
                stopbits=cfg.get('stopbits', self.stopbits),
                bytesize=cfg.get('bytesize', self.bytesize),
                timeout=cfg.get('timeout', self.timeout),
            )
        return self.clients[port]

    def _read_holding_registers(self, port, address, count, slave_id):
        client = self._get_client(port)

        try:
            if not client.connect():
                return None

            response = client.read_holding_registers(
                address=address,
                count=count,
                device_id=slave_id
            )

            if response.isError():
                return None

            return response.registers

        except Exception as e:
            logger.error(f"讀取暫存器錯誤 (port={port}, addr={address}): {e}")
            return None

    def read_data2byte(self, port, add, count, slave_id):
        registers = self._read_holding_registers(port, add, count, slave_id)
        if registers is None or len(registers) < 2:
            return None
        return (registers[1] << 16) + registers[0]

    def read_data1byte(self, port, add, count, slave_id):
        registers = self._read_holding_registers(port, add, count, slave_id)
        if registers is None or len(registers) < 1:
            return None
        return registers[0]

    def read_data1byte_signed(self, port, add, count, slave_id):
        """讀取有符號的單字節數據"""
        registers = self._read_holding_registers(port, add, count, slave_id)
        if registers is None or len(registers) < 1:
            return None
        # 將 16-bit unsigned 轉換為 signed
        value = registers[0]
        if value > 32767:  # 2^15 - 1
            value -= 65536  # 2^16
        return value

    def read_uint32(self, port, add, count, slave_id):
        """讀取 32-bit 無符號整數 (兩個 16-bit 暫存器合併)"""
        registers = self._read_holding_registers(port, add, count, slave_id)
        if registers is None or len(registers) < 2:
            return None
        # 將兩個 16-bit 無符號整數合併為 32-bit 無符號整數
        # High Word 在前，Low Word 在後 (Big-Endian)
        return (registers[0] << 16) + registers[1]

    def read_int32(self, port, add, count, slave_id):
        """讀取 32-bit 有符號整數 (兩個 16-bit 暫存器合併)"""
        registers = self._read_holding_registers(port, add, count, slave_id)
        if registers is None or len(registers) < 2:
            return None
        # 將兩個 16-bit 無符號整數合併為 32-bit 有符號整數
        # High Word 在前，Low Word 在後 (Big-Endian)
        unsigned_32bit = (registers[0] << 16) + registers[1]
        # 轉換為 signed
        if unsigned_32bit > 2147483647:  # 2^31 - 1
            unsigned_32bit -= 4294967296  # 2^32
        return unsigned_32bit

    def read_float32(self, port, add, count, slave_id):
        """用於解析採用 IEEE 754 浮點數格式的雙暫存器資料"""
        registers = self._read_holding_registers(port, add, count, slave_id)
        if registers is None or len(registers) < 2:
            return None
        try:
            packed_string = struct.pack('>HH', registers[0], registers[1])
            unpacked_float = struct.unpack('>f', packed_string)[0]
            return round(unpacked_float, 2)
        except Exception as e:
            logger.error(f"解析 float32 錯誤: {e}")
            return None

    def _read_with_retry(self, port, slave_id, device_type, test_key, test_address, test_count):
        """通用的重試讀取邏輯"""
        default_data = {
            "voltage_r_s": 0.0, "voltage_s_t": 0.0, "voltage_t_r": 0.0,
            "current_r": 0.0, "current_s": 0.0, "current_t": 0.0,
            "frequency": 0.0, "power": 0.0, "power_kva": 0.0,
            "pf": 0.0, "energy": 0.0, "immediate_demand": 0.0,
            "alive": 0
        }
        
        device_config = DEVICE_CONFIGS.get(device_type)
        if not device_config:
            logger.error(f"未知的設備類型: {device_type}")
            return default_data

        for attempt in range(3):
            try:
                # 測試連通性
                test_val = self._read_register_value(port, test_address, test_count, slave_id, device_type)
                if test_val is None:
                    logger.info(f"第 {attempt + 1} 次嘗試失敗，稍後重試...")
                    time.sleep(0.5)
                    continue

                # 連通成功，讀取所有寄存器
                data = default_data.copy()
                config = device_config["registers"]
                decimals = device_config["decimals"]

                for key, reg_config in config.items():
                    if len(reg_config) == 4:
                        addr, count, factor, signed_flag = reg_config
                        signed = (signed_flag == "signed")
                    else:
                        addr, count, factor = reg_config
                        signed = False
                    
                    value = self._read_register_value(port, addr, count, slave_id, device_type, signed)
                    if value is not None:
                        if factor is not None:
                            value = value * factor
                        data[key] = round(value, decimals.get(key, 2))

                data["alive"] = 1
                logger.info(f"成功讀取 {device_type} 資料 (埠={port}, 從機ID={slave_id})")
                return data

            except Exception as e:
                logger.error(f"讀取 {device_type} 異常 (attempt {attempt + 1}): {e}")
                time.sleep(0.5)
                continue

        logger.warning(f"無法讀取 {device_type}，已重試 3 次")
        return default_data

    def _read_register_value(self, port, address, count, slave_id, device_type, signed=False):
        """根據設備類型讀取寄存器值"""
        if device_type == "adtek_cpm12d":
            if count == 1:
                if signed:
                    # ADTEK 的有符號單字節數據
                    return self.read_data1byte_signed(port, address, count, slave_id)
                else:
                    # ADTEK 的無符號單字節數據
                    return self.read_data1byte(port, address, count, slave_id)
            else:
                if signed:
                    # ADTEK 的有符號雙字節數據 (32-bit signed)
                    return self.read_int32(port, address, count, slave_id)
                else:
                    # ADTEK 的無符號雙字節數據 (32-bit unsigned)
                    return self.read_uint32(port, address, count, slave_id)
        elif count == 1:
            return self.read_data1byte(port, address, count, slave_id)
        else:
            return self.read_data2byte(port, address, count, slave_id)

    def read_dae_PM210(self, port, slave_id):
        """DAE PM210 電表讀取 (含 3 次重試機制)"""
        return self._read_with_retry(port, slave_id, "dae_PM210", 
                                     "voltage_r_s", 26, 2)

    def read_adtek_cpm12d(self, port, slave_id):
        """ADTEK CPM-12D 電表讀取 (含 3 次重試機制)"""
        return self._read_with_retry(port, slave_id, "adtek_cpm12d", 
                                     "voltage_r_s", 0x0131, 2)

    def close_all(self):
        for client in self.clients.values():
            try:
                client.close()
            except Exception as e:
                logger.error(f"關閉連接時發生錯誤: {e}")


if __name__ == "__main__":
    reader = MeterReader()

    test_devices = [
        {"name": "meter_01", "slave_id": 1, "port": "COM4", "type": "adtek_cpm12d"},
        {"name": "meter_02", "slave_id": 101, "port": "COM4", "type": "dae_PM210"},
    ]

    try:
        for dev in test_devices:
            if dev["type"] == "dae_PM210":
                data = reader.read_dae_PM210(dev["port"], dev["slave_id"])
            elif dev["type"] == "adtek_cpm12d":
                data = reader.read_adtek_cpm12d(dev["port"], dev["slave_id"])
            else:
                logger.warning(f"未知的設備類型: {dev['type']}")
                continue
            
            print(f"\n[{dev['name']}] 讀取結果:")
            for k, v in data.items():
                status = "✓" if data.get("alive", 0) else "✗"
                print(f"  {status} {k}: {v}")
            print("-" * 40)
    finally:
        reader.close_all()