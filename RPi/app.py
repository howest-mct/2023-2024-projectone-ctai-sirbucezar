import threading
import queue
from RPLCD.i2c import CharLCD
from bluetooth_uart_server.bluetooth_uart_server import ble_gatt_uart_loop

# Initialize the LCD (adjust I2C address and dimensions as needed)
try:
    lcd = CharLCD(i2c_expander='PCF8574', address=0x3f, port=1,
                  cols=16, rows=2, charmap='A00', auto_linebreaks=True)
    lcd.write_string("LCD Initialized")
except Exception as e:
    print(f"Failed to initialize LCD: {e}")

def display_message(message):
    try:
        lcd.clear()
        lcd.write_string(message)
    except Exception as e:
        print(f"Failed to display message on LCD: {e}")

def main():
    rx_q = queue.Queue()
    tx_q = queue.Queue()
    device_name = "penjamin_pi"

    def extended_ble_gatt_uart_loop(rx_q, tx_q, device_name):
        ble_gatt_uart_loop(rx_q, tx_q, device_name)
        from bluetooth_uart_server.bluetooth_uart_server import BLE_UART_SERVICE_UUID, BLE_UART_RX_CHAR_UUID, BLE_UART_TX_CHAR_UUID
        print(f"Service UUID: {BLE_UART_SERVICE_UUID}")
        print(f"RX Characteristic UUID: {BLE_UART_RX_CHAR_UUID}")
        print(f"TX Characteristic UUID: {BLE_UART_TX_CHAR_UUID}")

    threading.Thread(target=extended_ble_gatt_uart_loop, args=(rx_q, tx_q, device_name), daemon=True).start()
    
    while True:
        try:
            incoming = rx_q.get(timeout=1)
            if incoming:
                message = format(incoming)  # Assuming the data is encoded as utf-8
                print(f"In main loop: {message}")
                display_message(message)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in main loop: {e}")

if __name__ == '__main__':
    main()


