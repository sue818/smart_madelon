from pymodbus.client import ModbusTcpClient
from pymodbus import (
    ExceptionResponse,
    ModbusException,
    pymodbus_apply_logging_config,
)
import logging

# Enable logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.WARNING)

class ModbusClient:
    def __init__(self, host, port=8899):
        self.client = ModbusTcpClient(host=host, port=port)

    def read_registers(self, start_address, count):
        """Read multiple holding registers using FC03."""
        try:
            self.client.connect()
            response = self.client.read_holding_registers(start_address, count, slave=1)
            if response.isError():
                print(f"Error reading registers: {response}")
                return None
            return response.registers
        finally:
            self.client.close()

    def write_single_register(self, address, value):
        """Write a single register using FC06."""
        try:
            self.client.connect()
            response = self.client.write_register(address, value, slave=1)
            if response.isError():
                print(f"Error writing register: {response}")
        finally:
            self.client.close()
