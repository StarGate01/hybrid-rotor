#!/usr/bin/env python3

import time, signal, sys
from rotor.interface import Interface
from rotor.server import Server


server_ip = "0.0.0.0"
server_port = 4533

azm_offset = 0.0
elv_offset = 0.0

server = Server(server_ip, server_port)
interface = Interface()


def exit_handler(sig, frame):
    print("Exiting hybrid-rotor")
    server.stop()
    interface.close()
    sys.exit(0)

def main():
    print("Starting hybrid-rotor")

    interface.open()
    server.start()

    while True:
        (azm_is, elv_is) = interface.read()
        azm_is += azm_offset
        elv_is += elv_offset
        server.update(azm_is, elv_is)
        interface.update(azm_is, server.azm_must, elv_is, server.elv_must)
        time.sleep(1.0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    main()
