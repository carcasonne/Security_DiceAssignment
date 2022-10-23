from twisted.internet import reactor
from client import Client
from server import Server
import time
from Crypto.PublicKey import RSA

Client1_Name = input("Name of first user:")

Client1_PrivateKey = RSA.generate(2048)
Client1_PublicKey = RSA.RsaKey.publickey(Client1_PrivateKey)
print(f"Keys generated for {Client1_Name}")

Client2_Name = input("Name of second user:")

Client2_PrivateKey = RSA.generate(2048)
Client2_PublicKey = RSA.RsaKey.publickey(Client2_PrivateKey)
print(f"Keys generated for {Client2_Name}")

Client1_Port = 4300
Client2_Port = 4400

Client1 = Client("localhost", Client1_Port, Client2_Port, Client1_PrivateKey, Client1_PublicKey, Client2_PublicKey, Client1_Name, Client2_Name)
Client2 = Client("localhost", Client2_Port, Client1_Port, Client2_PrivateKey, Client2_PublicKey, Client1_PublicKey, Client2_Name, Client1_Name)

time.sleep(0.5)
reactor.listenUDP(Client1_Port, Client1)

time.sleep(0.25)
reactor.listenUDP(Client2_Port, Client2)

inp = ""
while True:
    inp = input("'/dice' to start protocol\n")
    if "/dice" in inp:
        break

Client1.step3_initiateProtocol()

reactor.run()
