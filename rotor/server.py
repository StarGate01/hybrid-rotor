import socket 
from threading import Thread 
from socketserver import ThreadingMixIn 


# Handles a client tcp connection
class ClientThread(Thread): 
 
    def __init__(self, server, conn, ip, port): 
        Thread.__init__(self) 
        self.server = server
        self.conn = conn
        self.ip = ip 
        self.port = port 
        self.running = False
        print("Started client thread for " + self.ip + ":" + str(self.port))
 
    def _respond(self, code):
        resp = "RPRT " + str(code) + "\n"
        self.conn.send(resp.encode("ascii"))

    def run(self):
        self.server.threads.append(self) 
        self.running = True
        while self.running: 
            try:
                data = self.conn.recv(2048)
            except socket.timeout:
                pass
            except:
                raise
            else:
                if(data == None): pass
                data = data.decode('ascii').strip().split()
                if(len(data) >= 1):
                    cmd = data[0]
                    args = data[1:]
                    if(cmd == "p"):
                        resp = '{0:.2f}\n{1:.2f}\n'.format(self.server.azm_is_cache, self.server.elv_is_cache)
                        self.conn.send(resp.encode("ascii"))
                    elif(cmd == "P"):
                        if(len(args) >= 2):
                            self.server.azm_must = float(data[1].replace(',','.'))
                            self.server.elv_must = float(data[2].replace(',','.'))
                            self._respond(0)
                        else: self._respond(-1)
                    elif(cmd == "S"):
                        self._respond(0)
                    elif(cmd == "q"):
                        self._respond(0)
                        print("Client " + self.ip + " quits")
                        break
                    else:
                        self._respond(-2)
        self.conn.close()
        self.server.threads.remove(self) 
        print("Exiting client thread for " + self.ip)

# Provides a subset of the rotctld protocol for gpredict
# See https://manpages.ubuntu.com/manpages/xenial/man8/rotctld.8.html
# gpredict only uses p, P, S and q
class Server:

    def __init__(self, ip, port):
        self.ip = ip 
        self.port = port 
        self.azm_must = 0.0
        self.elv_must = 0.0
        self.azm_is_cache = 0.0
        self.elv_is_cache = 0.0
        self._do_listen = False
        socket.setdefaulttimeout(3.0)

    def _listen(self):
        print("Starting server thread")
        while self._do_listen:  
            try: 
                self.tcpServer.listen(4)
                (conn, (ip, port)) = self.tcpServer.accept() 
            except socket.timeout:
                pass
            except:
                raise
            else:
                newthread = ClientThread(self, conn, ip, port) 
                newthread.start()    
        print("Exiting server thread")

    def start(self):
        self.tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.tcpServer.bind((self.ip, self.port)) 
        self.threads = [] 
        self.listen_thread = Thread(target = self._listen)
        self._do_listen = True
        self.listen_thread.start()
        print("Started server")

    def stop(self):
        print("Stopping server")
        self._do_listen = False
        if(self.listen_thread != None):
            self.listen_thread.join()
        for client in self.threads:
            client.running = False
        for client in self.threads:
            client.join()
        print("Stopped server")

    def update(self, azm_is, elv_is):
        self.azm_is_cache = azm_is
        self.elv_is_cache = elv_is