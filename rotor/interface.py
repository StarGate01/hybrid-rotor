import board, busio, math, time, sys
import adafruit_lsm303dlh_mag, adafruit_lsm303_accel
from luma.core.interface.serial import i2c as luma_i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import ImageFont
import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt

# Provides methods to access the sensor and the LCD
class Interface:

    def __init__(self):
        self.F   = 1.0
        self.b   = np.zeros([3, 1])
        self.A_1 = np.eye(3)

    def open(self):
        i2c_busio = busio.I2C(board.SCL, board.SDA)
        self.sensor_mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(i2c_busio)
        self.sensor_accel = adafruit_lsm303_accel.LSM303_Accel(i2c_busio)
        i2c_luma = luma_i2c(port=1, address=0x3c)
        self.lcd = sh1106(i2c_luma, width=128, height=64)
        self.font = ImageFont.truetype("FreeSans.ttf", 16)
        print("Opened interface")

    def read(self):
        # Calibrate magnetic
        mag_x, mag_y, mag_z = self.sensor_mag.magnetic;
        mag_raw = np.array([mag_x, mag_y, mag_z]).reshape(3, 1)
        mag_raw = np.dot(self.A_1, mag_raw - self.b)
        mag_x_calib = -mag_raw[1,0]
        mag_y_calib = -mag_raw[0,0]
        mag_z_calib = -mag_raw[2,0]

        # Normalize acceleration
        acc_x, acc_y, acc_z = self.sensor_accel.acceleration
        acc_len = math.sqrt((acc_x ** 2) + (acc_y ** 2) + (acc_z ** 2))
        acc_x_norm = acc_y / acc_len
        acc_y_norm = acc_x / acc_len
        acc_z_norm = acc_z / acc_len

        # Compute eulers
        roll = math.atan2(acc_y_norm, acc_z_norm)
        pitch = math.atan(-acc_x_norm / ((acc_y_norm * math.sin(roll)) + (acc_z_norm * math.cos(roll))))

        # Compute tilt corrected heading
        # See https://www.mikrocontroller.net/attachment/292888/AN4248.pdf
        mag_y_comp = (mag_x_calib * math.sin(roll)) - (mag_y_calib * math.cos(roll))
        mag_x_comp = (mag_x_calib * math.cos(pitch)) + (mag_y_calib * math.sin(pitch) * math.sin(roll)) + (mag_z_calib * math.sin(pitch) * math.cos(roll))
        heading_comp = 180.0 * math.atan2(mag_y_comp, mag_x_comp) / math.pi
        if (heading_comp < 0): heading_comp += 360.0

        return (heading_comp, 180.0 * roll / math.pi)


    def calibrate(self):
        print('Collecting samples ... press Ctrl-C to stop')
        try:
            s = []
            n = 0
            while True:
                s.append(self.sensor_mag.magnetic)
                n += 1
                sys.stdout.write('\rTotal: %d' % n)
                sys.stdout.flush()
        except KeyboardInterrupt:
            pass
        print(" Done")
        
        # Ellipsoid fit
        # See https://teslabs.com/articles/magnetometer-calibration/
        raw = s
        s = np.array(s).T

        # D (samples)
        D = np.array([s[0]**2., s[1]**2., s[2]**2.,
                      2.*s[1]*s[2], 2.*s[0]*s[2], 2.*s[0]*s[1],
                      2.*s[0], 2.*s[1], 2.*s[2], np.ones_like(s[0])])

        # S, S_11, S_12, S_21, S_22 (eq. 11)
        S = np.dot(D, D.T)
        S_11 = S[:6,:6]
        S_12 = S[:6,6:]
        S_21 = S[6:,:6]
        S_22 = S[6:,6:]

        # C (Eq. 8, k=4)
        C = np.array([[-1,  1,  1,  0,  0,  0],
                      [ 1, -1,  1,  0,  0,  0],
                      [ 1,  1, -1,  0,  0,  0],
                      [ 0,  0,  0, -4,  0,  0],
                      [ 0,  0,  0,  0, -4,  0],
                      [ 0,  0,  0,  0,  0, -4]])

        # v_1 (eq. 15, solution)
        E = np.dot(linalg.inv(C),
                   S_11 - np.dot(S_12, np.dot(linalg.inv(S_22), S_21)))

        E_w, E_v = np.linalg.eig(E)

        v_1 = E_v[:, np.argmax(E_w)]
        if v_1[0] < 0: v_1 = -v_1

        # v_2 (eq. 13, solution)
        v_2 = np.dot(np.dot(-np.linalg.inv(S_22), S_21), v_1)

        # quadric-form parameters
        M = np.array([[v_1[0], v_1[3], v_1[4]],
                      [v_1[3], v_1[1], v_1[5]],
                      [v_1[4], v_1[5], v_1[2]]])
        n = np.array([[v_2[0]],
                      [v_2[1]],
                      [v_2[2]]])
        d = v_2[3]

        # calibration parameters
        # note: some implementations of sqrtm return complex type, taking real
        M_1 = linalg.inv(M)
        self.b = -np.dot(M_1, n)
        self.A_1 = np.real(self.F / np.sqrt(np.dot(n.T, np.dot(M_1, n)) - d) *
                           linalg.sqrtm(M))
        print("b: " + str(self.b))
        print("A_1: " + str(self.A_1))
        print("Saving calibration data")
        np.save("calibration/" + "b.npy", self.b)
        np.save("calibration/" + "a1.npy", self.A_1)

        # Plot raw and calibrated data
        calib = []
        for dat in raw:
            rdat = np.array(dat).reshape(3, 1)
            cal = np.dot(self.A_1, rdat - self.b)
            calib.append([cal[0,0], cal[1,0], cal[2,0]])
        fig, axs = plt.subplots(2, 3)
        xs = [x[0] for x in raw]
        ys = [x[1] for x in raw]
        zs = [x[2] for x in raw]
        axs[0, 0].scatter(ys, zs)
        axs[0, 0].axis('equal')
        axs[0, 0].set_title("X Raw")
        axs[0, 1].scatter(xs, zs)
        axs[0, 1].axis('equal')
        axs[0, 1].set_title("Y Raw")
        axs[0, 2].scatter(xs, ys)
        axs[0, 2].axis('equal')
        axs[0, 2].set_title("Z Raw")
        xs = [x[0] for x in calib]
        ys = [x[1] for x in calib]
        zs = [x[2] for x in calib]
        axs[1, 0].scatter(ys, zs)
        axs[1, 0].axis('equal')
        axs[1, 0].set_title("X Calib")
        axs[1, 1].scatter(xs, zs)
        axs[1, 1].axis('equal')
        axs[1, 1].set_title("Y Calib")
        axs[1, 2].scatter(xs, ys)
        axs[1, 2].axis('equal')
        axs[1, 2].set_title("Z Calib")
        plt.savefig('calibration/result.png')

    def load_calibration(self):
        print("Loading calibration data")
        self.b = np.load("calibration/" + "b.npy")
        self.A_1 = np.load("calibration/" + "a1.npy")

    def display(self, azm_is, azm_must, elv_is, elv_must):
        azm_diff = azm_must - azm_is
        azm_diff = (azm_diff + 180.0) % 360.0 - 180.0
        hint_azm = 'Left' if azm_diff > 0 else 'Right'
        hint_elv = 'Up' if elv_must > elv_is else 'Down'
        with canvas(self.lcd) as draw:
            draw.rectangle(self.lcd.bounding_box, fill="black")

            draw.text((0, 0), 'Azimuth' , fill="white", font=self.font)
            t = '{:.2f}°'.format(azm_is)
            ts = self.font.getsize(t)
            draw.text((self.lcd.bounding_box[2] - ts[0], 0), t , fill="white", font=self.font)

            draw.text((10, 15), hint_azm + ' to', fill="white", font=self.font)
            t = '{:.2f}°'.format(azm_must)
            ts = self.font.getsize(t)
            draw.text((self.lcd.bounding_box[2] - ts[0], 15), t , fill="white", font=self.font)

            draw.text((0, 30), 'Elevation' , fill="white", font=self.font)
            t = '{:.2f}°'.format(elv_is)
            ts = self.font.getsize(t)
            draw.text((self.lcd.bounding_box[2] - ts[0], 30), t , fill="white", font=self.font)

            draw.text((10, 45), hint_elv + ' to', fill="white", font=self.font)
            t = '{:.2f}°'.format(elv_must)
            ts = self.font.getsize(t)
            draw.text((self.lcd.bounding_box[2] - ts[0], 45), t , fill="white", font=self.font)
