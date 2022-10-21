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
        name    = ""

        if(len(split) > 1):
            name = split[1]

        if request == "Requesting possible connections":
            allOtherClients = self.clients
            if (addr, name) in allOtherClients:
                allOtherClients.remove((addr, name))

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
            self.clients.add((addr, name))

if __name__ == "__main__":
    reactor.listenUDP(9999, Server())
    reactor.run()