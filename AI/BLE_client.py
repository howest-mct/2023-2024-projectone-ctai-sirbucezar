import asyncio
from itertools import count, takewhile
import sys
import time
from datetime import datetime
from typing import Iterator

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

TARGET_DEVICE_ADDRESS = "F6DA5E81-E500-0816-0096-E74E23A7F773"


def sliced(data: bytes, n: int) -> Iterator[bytes]:
    """Slices *data* into chunks of size *n*. The last slice may be smaller than *n*."""
    return takewhile(len, (data[i: i + n] for i in count(0, n)))

async def uart_terminal(rx_q=None, tx_q=None, targetDeviceAddress=None):
    device = await BleakScanner.find_device_by_address(targetDeviceAddress, timeout=10.0)
    if device is None:
        print("No matching device found, ensure the device is advertising.")
        sys.exit(1)

    print(f"Found device: {device.name} ({device.address}), connecting...")

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        for task in asyncio.all_tasks():
            task.cancel()

    def disconnect():
        print("Disconnecting...")

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        print(f"Received: {data}")
        if rx_q is not None:
            rx_q.put(data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        try:
            print("Connected")
            await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
            services = await client.get_services()
            for service in services:
                print(f"[Service] {service.uuid}")
                for characteristic in service.characteristics:
                    print(f"  [Characteristic] {characteristic.uuid}")

            nus = client.services.get_service(UART_SERVICE_UUID)
            rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)
            if tx_q is None:  # DEMO
                time.sleep(1)
                last_dt = ""
                while True:
                    now = datetime.now()
                    time_string = now.strftime("%M%S")
                    if last_dt != time_string:
                        last_dt = time_string
                        data = time_string.encode()
                        for s in sliced(data, rx_char.max_write_without_response_size):
                            await client.write_gatt_char(rx_char, s, response=False)
                        print(f"Sent: {data}")
                    time.sleep(0.2)
            else:
                while True:
                    try:
                        data = tx_q.get_nowait()
                        if data is not None:
                            data = data.encode()
                            for s in sliced(data, rx_char.max_write_without_response_size):
                                await client.write_gatt_char(rx_char, s, response=False)
                            print(f"Sent: {data}")
                    except:
                        time.sleep(0.5)
                        pass
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            disconnect()

def run(rx_q=None, tx_q=None, targetDeviceAddress=None):
    if targetDeviceAddress is None:
        raise ValueError("targetDeviceAddress cannot be None.")
    
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(uart_terminal(
            rx_q=rx_q, tx_q=tx_q, targetDeviceAddress=targetDeviceAddress))
    except asyncio.exceptions.CancelledError:
        pass

if __name__ == '__main__':
    run(targetDeviceAddress=TARGET_DEVICE_ADDRESS)
