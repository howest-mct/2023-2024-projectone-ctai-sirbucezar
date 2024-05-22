from RPLCD.i2c import CharLCD
import time

# Initialize the LCD
lcd = CharLCD(i2c_expander='PCF8574', address=0x3f, port=1,
              cols=16, rows=2, charmap='A00', auto_linebreaks=True)

# Display a test message
lcd.clear()
lcd.write_string("Hello, World!")

# Wait for 5 seconds to observe the message
time.sleep(5)

# Clear the display
lcd.clear()
