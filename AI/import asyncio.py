import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover(timeout=10)
    for device in devices:
        print(f"Device: {device.name}, Address: {device.address}, RSSI: {device.rssi}")

    if not devices:
        print("No BLE devices found.")

if __name__ == "__main__":
    asyncio.run(scan())
