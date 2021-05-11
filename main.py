#!/usr/bin/env python3

import time, signal, sys
from rotor.interface import Interface
from rotor.server import Server


server_ip = "0.0.0.0"
server_port = 4533

azm_offset = 180.0
elv_offset = 0 # -8.0

server = Server(server_ip, server_port)
interface = Interface()


def exit_handler(sig, frame):
    print("Exiting hybrid-rotor")
    server.stop()
    sys.exit(0)

def main(calibrate):
    print("Starting hybrid-rotor")

    interface.open()

    if(calibrate):
        print("Starting calibration")
        interface.calibrate()
    else:
        interface.load_calibration()
        server.start()

        while True:
            (azm_is, elv_is) = interface.read()
            azm_is = (azm_is + azm_offset) % 360.0
            elv_is += elv_offset
            server.update(azm_is, elv_is)
            interface.display(azm_is, server.azm_must, elv_is, server.elv_must)
            time.sleep(0.2)


if __name__ == "__main__":
    calib = (len(sys.argv) >= 2) and sys.argv[1] == "calibrate"
    if(not calib):
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)
    main(calib)
