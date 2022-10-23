from logging import exception
import random
import time
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint

# cryptology shit
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

ServerPort = 9999

class Client(DatagramProtocol):
    def __init__(self, host, port, theirPort, sk, pk, theirPK, myName, theirName):
        if host == "localhost":
            host = "127.0.0.1"

        self.Id = host, port
        self.Server = "127.0.0.1", ServerPort
        self.Connection = "127.0.0.1", int(theirPort)
        self.ConnectionName = theirName
        self.ConnectionPublicKey = theirPK

        self.ProtocolActive = False
        self.Commitment = None
        self.RandomString = None
        self.MyRoll = None
        self.TheirRoll = None

        self.Username = myName
        self.PublicKey = pk
        self.PrivateKey = sk

        print("Client has been created with ID:", self.Id)

    def datagramReceived(self, datagram: bytes, addr):
        datagram = self.decryptRecievedMessage(datagram)
        
        # Commands which are only possible within the protocol
        if self.ProtocolActive:
            # Bob recieves Alice's Commitment (step 3) and sends his own roll (step 4)
            if "/step3" in datagram:
                commitment = self.removeCommand("/step3", datagram)
                self.Commitment = commitment

                self.step4()

            # 'Alice' recieves 'Bob''s roll. No fancy tricks
            if "/step4" in datagram:
                diceRoll = self.removeCommand("/step4", datagram)
                self.TheirRoll = int(diceRoll)
                print(f"{self.Username}: Recieved roll: {self.TheirRoll} from {self.ConnectionName}")
                self.step5()
                # 'Alice' doesn't have to check if she herself cheated, and jumps straight to step 7
                self.step7() 
                self.ProtocolActive = False
            
            # 'Bob' recieves 'Alice''s roll and random string. Time to check for cheating
            if "/step5" in datagram:
                diceRoll = self.removeCommand("/step5", datagram)
                split = diceRoll.split(",")
                self.TheirRoll = int(split[0])
                self.RandomString = split[1]
                self.step6()
                self.step7()
                self.ProtocolActive = False

        else:
            # This client has been told to initate dice protocol as reciever
            if "/init diceProtocol" in datagram:
                self.ProtocolActive = True;
                print(f"{self.Username}: Dice protocol has been activated")
                print(f"{self.Username}: Waiting for {self.ConnectionName} to send their initial commitment")
                return
                
            print("(" + self.ConnectionName + "): ", datagram )

    def removeCommand(self, cmd, msg):
        split = msg.split(cmd)
        split.pop(0)
        command = split[0]
        command = command.strip()
        return command

    def step3_initiateProtocol(self):
        print(f"{self.Username}: Beginning protocol")
        self.ProtocolActive = True

        msg = "/init diceProtocol"
        self.sendEncryptedMessage(msg)

        time.sleep(1)

        self.rollDice()

        self.RandomString = self.random_commit_int = str(randint(1, 1000))
        self.Commitment = self.createCommitment(self.MyRoll, self.RandomString)

        print(f"{self.Username}: Sending roll with commitment {self.MyRoll} to {self.ConnectionName}")
        print(f"{self.Username}: Commitment is: {self.Commitment}")

        msg = "/step3 " + self.Commitment
        self.sendEncryptedMessage(msg)

    # Bob sends his dice roll to Alice
    def step4(self):
        print(f"{self.Username}: Recieved commitment: {self.Commitment}")

        #send roll to other person
        self.rollDice()
        print(f"{self.Username}: Sending roll {self.MyRoll} to {self.ConnectionName}")

        msg = "/step4 " + str(self.MyRoll)
        self.sendEncryptedMessage(msg)

    # Alice sends her roll and random string to Bob
    def step5(self):
        msg = "/step5 " + str(self.MyRoll) + "," + self.RandomString
        self.sendEncryptedMessage(msg)

        print(f"{self.Username}: Sending roll without commitment to {self.ConnectionName}")

    def step6(self):
        print(f"{self.Username}: Got roll from {self.ConnectionName}: {self.TheirRoll}")
        print(f"{self.Username}: Their initial commitment: {self.Commitment}")

        newCommitment = self.createCommitment(self.TheirRoll, self.RandomString) #here hash self.TheirRoll, self.RandomString
        print(f"{self.Username}: Their new commitment: {newCommitment}")

        if newCommitment != self.Commitment:
            print(f"{self.Username}: {self.ConnectionName} has cheated! \n Their mother is a hamster and their father smells of elderberries!")
        else:
            print(f"{self.Username}: {self.ConnectionName} hasn't changed their roll!")

    def step7(self):
        combined = self.MyRoll ^ self.TheirRoll # XOR
        roll = (combined % 6) + 1

        print(f"{self.Username}: You have agreed that the roll was...")
        time.sleep(2) # drumroll please
        print(f"{self.Username}: {int(roll)}!")

    def rollDice(self):
        diceRoll = random.randint(1,6) #number between 1 and 6
        self.MyRoll = diceRoll
        print(f"{self.Username}: You rolled: " + str(diceRoll))
    
    # msg: the message to commit
    # r: random k-bit string
    def createCommitment(self, msg, rnd):
        toCommit = str(msg) + str(rnd)
        toCommit = toCommit.encode('utf-8')
        commit = SHA256.new(toCommit)
        return commit.hexdigest()

    def computeDice(self, roll1 : int, roll2 : int):
        combined = roll1 ^ roll2 # XOR
        roll = (combined % 6) + 1

        print("You have agreed that the roll was...")
        time.sleep(2) # drumroll please
        print(f"{int(roll)}!")

    # Order: Encode, sign, encrypt
    def sendEncryptedMessage(self, msg):
        msg = msg.encode('utf-8')
        #msg = self.sign(msg)
        msg = self.encrypt(msg)
        self.transport.write(msg, self.Connection)

    # Order: Decrypt, verify, decode
    def decryptRecievedMessage(self, msg):
        msg = self.decrypt(msg)

        # valid_signature = self.verify(self.currentCipher, msg)
        # if valid_signature != "Valid Signature":
        #     raise exception(f"Message recieved from {self.ConnectionName} has an invalid signature!")
        
        msg = msg.decode('utf-8')

        return msg
        
    def encrypt(self, message):
        cipher = PKCS1_OAEP.new(self.ConnectionPublicKey)
        return cipher.encrypt(message)

    def decrypt(self, ciphertext):
        cipher = PKCS1_OAEP.new(self.PrivateKey)
        return cipher.decrypt(ciphertext)

    def sign(self, message):
        h = SHA256.new(message)
        return pss.new(self.PrivateKey).sign(h)

    def verify(self, message, signature):
        h = SHA256.new(message)
        verifier = pss.new(self.ConnectionPublicKey)
        try:
            verifier.verify(h, signature)
            return "Valid Signature"
        except (ValueError, TypeError):
            return "Invalid Signature"


if __name__ == "__main__":
    if False:
        Port = randint(4000, 5000)
        Client = Client("localhost", Port)

        Client.Username = input("Choose username:")

        Client.SecretKey = RSA.generate(2048)
        Client.PublicKey = RSA.RsaKey.publickey(Client.SecretKey)

        test = Client.PublicKey.encode('utf-8')

        reactor.listenUDP(Port, Client)
        reactor.run()
