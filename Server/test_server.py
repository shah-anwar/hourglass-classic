from logging import exception
import socket, threading, select, time, os, pickle, sqlite3, random

ProgramQuit = False
serverName = "TestServer"
currentIP = ("192.168.0.10", 107)
#currentIP = (socket.gethostbyname(socket.gethostname()), 107)

outSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

inSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
inSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inSock.bind(currentIP)

knownIPs = [("192.168.0.1", 107),("192.168.0.10", 107),("192.168.0.21", 107)]

class Transmission():
    def send(msg, recipient):
        outSock.sendto(msg, recipient)

    def receiveAgent():
        try:
            while True:
                data, sender = inSock.recvfrom(1024)
                sender = (sender[0], 107)
                print(sender)
                #Transmission.packetHandler(data, sender)
                if ProgramQuit == True:
                    inSock.close()
                    break
        except KeyboardInterrupt:
            inSock.close()
    
    def packetHandler(data, sender): #general packet format: [timestamp, header, destinationNode, circuitID, sig, Encrypted Section]
        data = pickle.loads(data)
        header = data[1]
        if header == "LOGIN": #format: [timestamp, "LOGIN", NodeID, circuitID, EndIP, sig] (once a circuit has been initialised, the end of the circuit sends its own IP to the owner so that they may create a signature of it)
            Transmission.login(data)
        elif header == "REGISTER": #format: [timestamp, "REGISTER", NodeID, Public Key, circuitID, EndIP, sig]
            Transmission.register(data)
        elif header == "GETNODES": #format: [timestamp, "GETNODES"]
            Transmission.getNodes(sender)
        elif header == "GETINFO": #format: [timestamp, "GETINFO", SERVER, circuitID, EndIP, sig]
            Transmission.getInfo(data)
        elif header == "TEST": #format: [timestamp, "TEST", number]
            print(data[2])

    def login():
        pass

    def register():
        pass

    def getNodes(sender):
        print("Sending!")
        NodeA = knownIPs[random.randint(0, len(knownIPs) - 1)]
        while True:
            NodeB = knownIPs[random.randint(0, len(knownIPs) - 1)]
            NodeC = knownIPs[random.randint(0, len(knownIPs) - 1)]
            if ((NodeA != NodeB) and (NodeA != NodeC) and (NodeB != NodeC)) or (len(knownIPs) < 3):
                break
        NodeList = [NodeA, NodeB, NodeC]
        timestamp = 0 #current time (unix time)
        sig = 0 #server's signature
        msg = [timestamp, "REPLY:GETNODES",  NodeList, sig]
        print(msg)
        #msg = pickle.dumps(msg)
        #Transmission.send(msg, sender)

    def getInfo():
        pass

class Circuit():
    def __init__(self, own=True):
        if own == True:
            pass
        else:
            pass

if __name__ == '__main__':
    print(currentIP)
    threading.Thread(target = Transmission.receiveAgent).start()
    x = 0
    while True:
        x += 1
        time.sleep(2)
        print("TEST", x)

