#!/usr/bin/env python3

import time, signal, sys, math
from rotor.interface import Interface


interface = Interface()


def exit_handler(sig, frame):
    print("Exiting hybrid-rotor calibration")
    interface.close()
    sys.exit(0)

def main():
    print("Starting hybrid-rotor calibration")

    interface.open()

    m_max = [-float('inf'), -float('inf'), -float('inf')]
    m_min = [float('inf'), float('inf'), float('inf')]
    g_max = [-float('inf'), -float('inf'), -float('inf')]
    g_min = [float('inf'), float('inf'), float('inf')]

    m_offset = [0.0, 0.0, 0.0]
    m_scale = [0.0, 0.0, 0.0]
    m_calib = [0.0, 0.0, 0.0]

    while True:
        m = interface.sensor_mag.magnetic
        # for i in range(0, 3):
        #     m_max[i] = max(m_max[i], m[i])
        #     m_min[i] = min(m_min[i], m[i])
        #     m_offset[i] = - m_min[i]
        #     if((m_max[i] - m_min[i]) != 0.0):
        #         m_scale[i] = 2.0 / (m_max[i] - m_min[i])
        #     m_calib[i] = ((m[i] + m_offset[i]) * m_scale[i]) - 1.0

        # print("mag_offset = " + str(m_offset), ", mag_scale = " + str(m_scale) + ", mag_calib = " + str(m_calib))
        mag_len = math.sqrt((m[0] ** 2) + (m[1] ** 2) + (m[2] ** 2))
        # mag_x_norm = m[0] / mag_len
        # mag_y_norm = m[1] / mag_len
        # mag_z_norm = m[2] / mag_le
        
        print("len = " + str(mag_len))

        time.sleep(0.1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    main()
