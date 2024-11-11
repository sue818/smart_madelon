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
log.setLevel(logging.DEBUG)

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
            response = self.client.write_register(address, value)
            if response.isError():
                print(f"Error writing register: {response}")
        finally:
            self.client.close()

# Test the functions
def test_modbus_client():
    # host = "localhost"
    host = "192.168.6.137"

    client = ModbusClient(host)

    # Test reading registers
    print("Reading registers:")
    registers = client.read_registers(start_address=0, count=5)
    print(f"Registers: {registers}")

    # Test writing a single register
    # print("Writing a single register:")
    # client.write_single_register(address=0, value=1)


if __name__ == "__main__":
    test_modbus_client()
