import board, busio, math, time
import adafruit_lsm303dlh_mag, adafruit_lsm303_accel
from RPLCD.gpio import CharLCD
from RPi import GPIO

# Provides methods to access the sensor and the LCD
class Interface:

    def open(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor_mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(self.i2c)
        self.sensor_accel = adafruit_lsm303_accel.LSM303_Accel(self.i2c)
        self.lcd = CharLCD(pin_rs=22, pin_rw=24, pin_e=23, pins_data=[9, 11, 25, 8],
            numbering_mode=GPIO.BCM, cols=20, rows=4, dotsize=8, charmap='A02', auto_linebreaks=True, compat_mode=True)
        
        self.lcd.cursor_mode = "hide"
        self.lcd.clear()
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string("AZM IS")
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string("    MST NA")
        self.lcd.cursor_pos = (2, 0)
        self.lcd.write_string("ELV IS")
        self.lcd.cursor_pos = (3, 0)
        self.lcd.write_string("    MST NA")

        print("Opened interface")

    def read(self):
        # Read sensors
        acc_x, acc_y, acc_z = self.sensor_accel.acceleration
        mag_x, mag_y, mag_z = self.sensor_mag._raw_magnetic

        # Normalize acceleration
        acc_len = math.sqrt((acc_x ** 2) + (acc_y ** 2) + (acc_z ** 2))
        acc_x_norm = acc_x / acc_len
        acc_y_norm = acc_y / acc_len
        acc_z_norm = acc_z / acc_len
        # Compute eulers
        pitch = math.asin(-acc_x_norm)
        roll = math.asin(acc_y_norm / math.cos(pitch))
      
        # Calibate magnetic
        mag_offset = [-369, -80, -118]
        mag_scale = [0.0025575447570332483, 0.0034423407917383822, 0.003105590062111801]
        mag_x = ((mag_x + mag_offset[0]) * mag_scale[0]) - 1.0
        mag_y = ((mag_y + mag_offset[1]) * mag_scale[1])  - 1.0
        mag_z = ((mag_z + mag_offset[2]) * mag_scale[2])  - 1.0
        # Normalize magnetic
        mag_len = math.sqrt((mag_x ** 2) + (mag_y ** 2) + (mag_z ** 2))
        mag_x_norm = mag_x / mag_len
        mag_y_norm = mag_y / mag_len
        mag_z_norm = mag_z / mag_len
        # Compute tilt corrected heading
        mag_y_comp = (mag_y_norm * math.cos(roll)) + (mag_z_norm * math.sin(roll))
        mag_x_comp = (mag_x_norm * math.cos(pitch)) + \
            (mag_y_norm * math.sin(roll) * math.sin(pitch)) - \
            (mag_z_norm * math.cos(roll) * math.sin(pitch))
        heading_comp = 180.0 * math.atan2(mag_x_comp, mag_y_comp) / math.pi
        if (heading_comp < 0): heading_comp += 360.0

        # heading = 180.0 * math.atan2(mag_y_norm, mag_x_norm) / math.pi
        # if heading < 0: heading += 360

        return (heading_comp, -180.0 * roll / math.pi)

    def update(self, azm_is, azm_must, elv_is, elv_must):
        azm_diff = azm_must - azm_is
        azm_diff = (azm_diff + 180.0) % 360.0 - 180.0
        hint_azm = '<<' if azm_diff > 0 else '>>'
        hint_elv = '^^' if elv_must > elv_is else 'vv'
        self.lcd.cursor_pos = (0, 11)
        self.lcd.write_string('{:.2f}  '.format(azm_is))
        self.lcd.cursor_pos = (1, 8)
        self.lcd.write_string((hint_azm + ' {:.2f}  ').format(azm_must))
        self.lcd.cursor_pos = (2, 11)
        self.lcd.write_string('{:.2f}  '.format(elv_is))
        self.lcd.cursor_pos = (3, 8)
        self.lcd.write_string((hint_elv + ' {:.2f}  ').format(elv_must))

    def close(self):
        if(self.lcd != None): self.lcd.close(clear=True)
        if(self.i2c != None): self.i2c.deinit()
        print("Closed interface")

