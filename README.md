# Hybrid Satellite Antenna Rotor

This system receives antenna rotation data from a satellite tracking application such as [gPredict](http://gpredict.oz9aec.net/), or any other program that implements the [rotctld](https://manpages.ubuntu.com/manpages/xenial/en/man8/rotctld.8.html) protocol. It measures the orientation and elevation of a dish using a sensor, and displays the necessary adjustments on a LCD screen. The user then has to adjust the dish manually.

## Hardware
 - Raspberry Pi 4
 - 2004A v2.0 LCD (4 * 20 dot-matrix characters)
 - GY-511 Sensor (LSM303DLH acceleration and magnetometer IC)

## Software Dependencies
 - APT: python3
 - APT: python3-rpi.gpio
 - PIP: [adafruit_lsm303dlh_mag](https://github.com/adafruit/Adafruit_CircuitPython_LSM303DLH_Mag)
 - PIP: [adafruit_lsm303_accel](https://github.com/adafruit/Adafruit_CircuitPython_LSM303_Accel)
 - PIP: [RPLCD](https://github.com/dbrgn/RPLCD)