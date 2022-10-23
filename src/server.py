from unicodedata import name
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = set()
    
    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode('utf-8')

        split = datagram.split('*')
        request = split[0]
        name = ""
        publicKey = ""

        if(len(split) > 1):
            name = split[1]
            publicKey = split[2]

        if request == "Requesting possible connections":
            allOtherClients = self.clients
            # A person shouldn't be able to talk to themselves (schizophrenia)
            if (addr, name, publicKey) in allOtherClients:
                allOtherClients.remove((addr, name, publicKey))

            addresses = ""

            counter = 0;

            for client in self.clients:
                addresses += "\n"
                addresses += "Connection with ID " + str(counter) + ": "
                addresses += str(client)
                counter   += 1

            print(name + " has requested access to all known connections")

            # TODO: also include username here
            self.transport.write(addresses.encode('utf-8'), addr)
            self.clients.add((addr, name, publicKey))

if __name__ == "__main__":
    reactor.listenUDP(9999, Server())
    reactor.run()