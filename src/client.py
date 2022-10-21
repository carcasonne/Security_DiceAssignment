import atexit
import random
import time
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint
from threading import Thread

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
        self.ProtocolActive = False
        self.Commitment = None
        self.RandomString = None
        self.MyRoll = None
        self.TheirRoll = None

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
                print("To initiate dice roll protocol, write: /dice")

                # infinte loop in a thread to keep checking for user input
                reactor.callInThread(self.sendMessage)

        # Commands which are only possible within the protocol
        elif self.ProtocolActive:
            # Bob recieves Alice's Commitment (step 3) and sends his own roll (step 4)
            if "/step3" in datagram:
                commitment = self.removeCommand("/step3", datagram)
                self.Commitment = commitment
                self.step4()

            # 'Alice' recieves 'Bob''s roll. No fancy tricks
            if "/step4" in datagram:
                diceRoll = self.removeCommand("/step4", datagram)
                self.TheirRoll = int(diceRoll)
                print(f"Recieved roll: {self.TheirRoll} from {self.ConnectionName}")
                self.step5()
                # 'Alice' doesn't have to check if she herself cheated, and jumps straight to step 7
                self.step7() 
            
            # 'Bob' recieves 'Alice''s roll and random string. Time to check for cheating
            if "/step5" in datagram:
                diceRoll = self.removeCommand("/step5", datagram)
                split = diceRoll.split(",")
                self.TheirRoll = int(split[0])
                self.RandomString = split[1]
                self.step6()

        else:
            # This client has been told to initate dice protocol as reciever
            if "/init diceProtocol" in datagram:
                self.ProtocolActive = True;
                print("Dice protocol has been activated")
                print(f"Waiting for {self.ConnectionName} to send their initial commitment")
                
            print("(" + self.ConnectionName + "): ", datagram )

    def trim(self, name):
        name = name.strip()
        name = name.strip('(')
        name = name.strip(')')
        name = name.strip("'")
        return name;
    
    def removeCommand(self, cmd, msg):
        split = msg.split(cmd)
        split.pop(0)
        command = split[0]
        command = command.strip()
        return command

    def sendMessage(self):
        while True:
            msg = input()
            print("\033[A                             \033[A")  #hack to remove the users own input from terminal
                                                                #done just to make it prettier
            print("(You): " + msg)

            # This client has initiated the dice roll protocol
            if "/dice" in msg:
                self.AntiTrustProtocol_inititater()
                self.ProtocolActive = True
                continue

            self.transport.write(msg.encode('utf-8'), self.Connection)

    # Bob sends his dice roll to Alice
    def step4(self):
        print(f"Recieved commitment: {self.Commitment}")

        #send roll to other person
        self.rollDice()
        print(f"Sending roll {self.MyRoll} to {self.ConnectionName}")
        self.transport.write(("/step4 " + str(self.MyRoll)).encode('utf-8'), self.Connection)

    def step5(self):
        #send encrypted dice roll to other person NO COMMITMENT
        self.RandomString = "string"
        self.transport.write((("/step5 " + str(self.MyRoll) + "," + self.RandomString)).encode('utf-8'), self.Connection)
        print(f"Sending roll without commitment to {self.ConnectionName}")

    def step6(self):
        print(f"Got roll from {self.ConnectionName}: {self.TheirRoll}")
        print(f"Their initial commitment: {self.Commitment}")

        newCommitment = "hashed" #here hash self.TheirRoll, self.RandomString
        print(f"Their new commitment: {newCommitment}")

        if newCommitment != self.Commitment:
            print(f"{self.ConnectionName} has cheated! \n Their mother was a hamster and their father smelt of elderberries")
        else:
            print(f"{self.ConnectionName} hasn't changed their roll!")

        #calculate roll
        self.step7()


    def step7(self):
        combined = self.MyRoll ^ self.TheirRoll # XOR
        roll = (combined % 6) + 1

        print("You have agreed that the roll was...")
        time.sleep(2) # drumroll please
        print(f"{int(roll)}!")
        self.ProtocolActive = False

    # This is basically step 3
    def AntiTrustProtocol_inititater(self):
        print("Beginning protocol")
        self.transport.write(("/init diceProtocol").encode('utf-8'), self.Connection)

        time.sleep(1)

        self.rollDice()
        # send encrypted dice roll to other person COMMITMENT
        self.Commitment = self.createCommitment(self.MyRoll, "string")
        hashedCommitment = "hashed" #TODO
        print(f"Sending roll with commitment {self.MyRoll} to {self.ConnectionName}")
        print(f"Commitment is: {hashedCommitment}")
        self.transport.write(("/step3 " + hashedCommitment).encode('utf-8'), self.Connection)

    def rollDice(self):
        diceRoll = random.randint(1,6) #number between 1 and 6
        self.MyRoll = diceRoll
        print("You rolled: " + str(diceRoll))
    
    # msg: the message to commit
    # r: random k-bit string
    def createCommitment(self, msg, r):
        return 0;

    def computeDice(self, roll1 : int, roll2 : int):
        combined = roll1 ^ roll2 # XOR
        roll = (combined % 6) + 1

        print("You have agreed that the roll was...")
        time.sleep(2) # drumroll please
        print(f"{int(roll)}!")

if __name__ == "__main__":
    Port = randint(4000, 5000)
    Client = Client("localhost", Port)

    Client.Username = input("Choose username:")

    reactor.listenUDP(Port, Client)
    reactor.run()