import atexit
import time
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint

ServerPort = 9999

class Client(DatagramProtocol):
    def __init__(self, host, port):
        if host == "localhost":
            host = "127.0.0.1"

        self.Id = host, port
        self.Server = "127.0.0.1", ServerPort
        self.Connection = None
        self.ConnectionName = None
        self.Username = None

        print("Client has been created with ID:", self.Id)
    
    def startProtocol(self):
        self.transport.write(("Requesting possible connections*" + self.Username).encode('utf-8'), self.Server)

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode('utf-8')
        
        # This is how the client connects to other clients (by getting a list from a central server)
        # Note: This assignment is not about making a pretty, efficient, or sane client-server connection... :) 
        if addr == self.Server:
            print("Choose a client from these: \n", datagram)

            if(datagram == ""):
                print("No possible connections exists")
                print("Attempting to find connections again in 5 seconds...")
                time.sleep(5)
                self.startProtocol()
            else:
                # All of this would be much prettier if I just sent structs instead of raw strings
                split = datagram.split("\n")
                split.pop(0)
                connection = -1

                while True:
                    connection = input("Write ID of connection to use: ")
                    if 0 <= int(connection) < len(split):
                        break
                
                splitMessage = split[int(connection)].split(',')
                port = splitMessage[1]
                name = splitMessage[2]
                port = self.trim(port)
                name = self.trim(name)

                self.Connection = "127.0.0.1", int(port)
                self.ConnectionName = name

                print("Connected to: " + name)

                # infinte loop in a thread to keep checking for user input
                reactor.callInThread(self.sendMessage)
        else:
            print("(" + self.ConnectionName + "): ", datagram )

    def trim(self, name):
        name = name.strip()
        name = name.strip(')')
        name = name.strip("'")
        return name;
    
    def sendMessage(self):
        while True:
            msg = input()
            print("\033[A                             \033[A") #hack to remove the users own input from terminal
                                                                #done just to make it prettier
            print("(You): " + msg)
            self.transport.write(msg.encode('utf-8'), self.Connection)

if __name__ == "__main__":
    Port = randint(4000, 5000)
    Client = Client("localhost", Port)

    Client.Username = input("Choose username:")

    reactor.listenUDP(Port, Client)
    reactor.run()