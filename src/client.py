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
        self.Address = None
        self.Username = None

        print("Client has been created with ID:", self.Id)
    
    def startProtocol(self):
        self.transport.write("ready".encode('utf-8'), self.Server)

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode('utf-8')
        
        # TODO: base this around username instead
        if addr == self.Server:
            print("Choose a client from these: \n", datagram)
            self.Address = input("Write host:"), int(input("Write port:"))
            reactor.callInThread(self.sendMessage)
        else:
            print(addr, ":", datagram )
        
    def sendMessage(self):
        try:
            while True:
                self.transport.write(input(":::").encode('utf-8'), self.Address)
        finally:
            # Some code to inform server that this client has lost connection

    
if __name__ == "__main__":
    Port = randint(4000, 5000)
    Client = Client("localhost", Port)
    reactor.listenUDP(Port, Client)
    reactor.run()