import asyncio
from pymodbus.server.async_io import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import logging

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Create a Modbus data store with some initial values
store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [0]*100)  # 100 holding registers initialized to 0
)
context = ModbusServerContext(slaves=store, single=True)

# Set up server identity
identity = ModbusDeviceIdentification()
identity.VendorName = 'pymodbus'
identity.ProductCode = 'PM'
identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
identity.ProductName = 'pymodbus Server'
identity.ModelName = 'pymodbus Server'
identity.MajorMinorRevision = '1.0'

# Start the Modbus server
async def run_server():
    await StartAsyncTcpServer(
        context=context,
        identity=identity,
        address=("localhost", 5020)
    )

if __name__ == "__main__":
    asyncio.run(run_server())
