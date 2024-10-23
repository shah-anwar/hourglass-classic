from ast import Pass
from logging import exception
import socket, threading, select, time, pickle, sqlite3, random, os

import HGCrypto as Cryptography
from structures import LimitlessQueue

serverName = "HGServer" #default name
announcements = "No New Announcements" #default announcement
ProgramQuit = False

choicesIP = []
tempSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tempSock.connect(("10.255.255.255", 80)) #arbitrary IP address used to get local IP address of device rather than loopback
choicesIP.append(tempSock.getsockname()[0])
tempSock.close()
choicesIP.append(socket.gethostbyname(socket.gethostname()))

knownIPs = []
usedCircuits = []
TIMEOUT = 120

####
test = True

def testprint(string): #Console output used for testing
    if test == True:
        print(string)
####
def linearSearch(val, array): #linear search algorithm for finding the index of a specified value within an array, used for unsorted lists
    result = None
    for x in range(len(array)):
        if array[x] == val:
            result = x
    if result == None:
        return -1
    else:
        return result

def updateGlobalConfig(): #creates or updates the global config file if data is altered in the program
    globalFile = open("Global.hg", "w")
    lines = ["[N]", str(myPublicKey[0]), "[PUBLIC KEY E]", str(myPublicKey[1]), "[PRIVATE KEY D]", str(myPrivateKey[1])]
    for x in range(len(lines)):
        globalFile.writelines(lines[x] + "\n")

def globalConfig(): #subroutine for accessing data in the global config file 'Global.hg'
    global myPublicKey, myPrivateKey
    try: #Try creating a global file, redirects to read if exists
        globalFile = open("Global.hg", "x") #creates the specified file
        globalFile.close() #closes the file to enable access to writing/appending mode
        myPublicKey, myPrivateKey = Cryptography.asymKeyGen(100)
        updateGlobalConfig()
    except: #Read global file
        lines = []
        globalFile = open("Global.hg", "r")
        for x in globalFile.readlines():
            lines.append(x.strip()) #remove new line at end of each string
        myPublicKey = (int(lines[1]), int(lines[3]))
        myPrivateKey = (int(lines[1]), int(lines[5]))

class TempCircuit():
    def __init__(self):
        fail = True
        self.__CircuitID = None
        self.__Complete = False
        while fail == True:
            try:
                self.internal_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.__IP = (currentIP[0], random.randint(300, 1000))
                self.internal_sock.bind(self.__IP)
                fail = False
            except:
                fail = True
        threading.Thread(target = self.internal_recv).start()

    def internal_recv(self):
        while True:
            try:
                data, sender = self.internal_sock.recvfrom(1024)
                threading.Thread(target = self.internal_packetHandler, args=(data, sender)).start()
                if ProgramQuit == True:
                    break
            except:
                break
    
    def internal_packetHandler(self, data, sender):
        try:
            data = pickle.loads(data)
            timestamp = data[0]
            header = data[1]
            if time.time() > timestamp + TIMEOUT: 
                pass # do nothing as packet has timed out
            elif header == "MSG":
                self.sendUp(pickle.dumps(data))
            elif (header == "LOGIN") or (header == "REGISTER") or (header == "NODEINFO"): #to server
                self.sendDown(pickle.dumps(data))
            elif header == "DATA": #to/from anyone
                status = self.checkOwnership(data)
                if status == "IN_SENDER":
                    self.sendDown(pickle.dumps(data))
                elif status == "IN_RECIPIENT":
                    self.sendUp(pickle.dumps(data))
            
            elif header[:5] == 'REPLY':
                msgID = header[6:] #get characters after 'REPLY:'
                if msgID == "JOINCIRCUIT":
                    #[timestamp, header, CircuitID, recipientIP]
                    if (data[2] == self.__CircuitID) and (data[3] == self.__IP):
                        msgID = data[2] #stop asking nodes to join

                elif msgID == "ENDCIRCUIT":
                    #[timestamp, header, CircuitID, endIP, recipientIP]
                    if data[2] == self.__CircuitID:
                        self.sendUp(pickle.dumps(data))
                        return

                index = linearSearch(msgID, self.__ongoingPackets)
                
                if index != -1:
                    self.__ongoingPackets.pop(index)

            elif header[:7] == 'REQUEST':
                self.requestHandler(data, sender)
        except:
            print("ERROR: Packet incorrectly formatted!")
    
    def requestHandler(self, data, sender):
        #[timestamp, "REQUEST:type", ----]
        header = data[1]
        requestType = header[8:]
        if requestType == "JOINCIRCUIT":
            #[timestamp, "REQUEST:JOINCIRCUIT", CircuitID, PublicKey, Signature]
            key = data[3]
            signature = data.pop(4)
            if data[2] == self.__CircuitID:
                return
            if Cryptography.verify(pickle.dumps(data), signature, key) == True:
                if random.randint(1,3) == 1: 
                    end = True #1/3 chance of becoming the end node
                else: 
                    end = False
                data.append(signature)
                self.setup(data[2], key, end, sender, pickle.dumps(data))

    def checkOwnership(self, data):
        #[timestamp, "DATA", destinationID, [msgID, originID, publicKey], payload, signature]
        destinationID = data[2]
        originID = data[3][1]

        found = False
        inSenderCircuit = False

        if originID == self.__CircuitID: #is sill on the sender's circuit
            found = True
            inSenderCircuit = True
        elif destinationID == self.__CircuitID: #is on the recipient's circuit
            found = True

        if found == True: #packet is on correct route
            if inSenderCircuit == True: # packet is still on the sender's circuit
                return 'IN_SENDER'
            else: # packet is on the recipient's circuit
                return 'IN_RECIPIENT'
        else: #packet is random
            return 'RANDOM'

    def getIP(self):
        return self.__IP

    def setup(self, CircuitID, PublicKey, EndStatus, UpNode, Full):
        if self.__Complete == False:
            self.__CircuitID = CircuitID
            self.__publicKey = PublicKey
            self.__EndStatus = EndStatus
            self.__UpNode = UpNode #node towards owner   
            self.__ongoingPackets = []

            reply = [time.time(), "REPLY:JOINCIRCUIT", self.__CircuitID, self.__UpNode]
            self.sendUp(pickle.dumps(reply))

            Transmission.moveCircuit(CircuitID)

            if self.__EndStatus == True:
                self.__DownNode = None      
            else:
                #get new node for down node
                Nodes = Transmission.getNodes(self.__IP, True)
                x = 0
                while True:
                    selectedNode = Nodes[x]
                    self.internal_sock.sendto(Full, selectedNode)
                    self.__ongoingPackets.append(self.__CircuitID)
                    sendWait = self.wait(time.time(), self.__CircuitID, 8)
                    if sendWait == True:
                        self.__DownNode = selectedNode
                        break
                    else:
                        x += 1

                    if x == len(Nodes):
                        break            
            if self.__EndStatus == True:
                time.sleep(1) #wait to avoid out of sequence packets
                endReply = [time.time(), "REPLY:ENDCIRCUIT", self.__CircuitID, self.__IP]
                self.sendUp(pickle.dumps(endReply))
            try:
                knownIPs.remove(self.__IP)
            except:
                pass

            self.__Complete = True

    def getCircuitID(self):
        return self.__CircuitID

    def sendUp(self, data): #sends data up the circuit (to the owner)
        print(self.__UpNode)
        self.internal_sock.sendto(data, self.__UpNode)

    def sendDown(self, data): #sends data out of the circuit or down the circuit (towards the end node)
        if self.__EndStatus != True:
            self.internal_sock.sendto(data, self.__DownNode)
        else: #get IP of next
            #[timestamp, header, destinationID, [msgID, circuitID, publicKey], payload, signature]
            tempData = pickle.loads(data)
            destinationID = tempData[2]
            if destinationID == "SERVER":
                self.internal_sock.sendto(data, currentIP) #serverIP for clients
            else:
                destination = database.getCircuitIP(destinationID)
                try:
                    self.internal_sock.sendto(data, destination)
                except:
                    pass

    def wait(self, startTime, msgID, length=30):
        while (startTime + length) > time.time():    
            for x in range(4):
                if (startTime + length) < time.time():
                    return 'TIMEOUT'
                elif msgID not in self.__ongoingPackets:
                    return True
                time.sleep(0.5)
        index = linearSearch(msgID, self.__ongoingPackets)
        if index != -1:
            self.__ongoingPackets.pop(index) #to avoid double messageID occurrence after timeout
        return False

    def quit(self, sender = None):
        quitMessage = [time.time(), "QUIT", self.__CircuitID]
        quitMessage = pickle.dumps(quitMessage)
        if sender == None:
            self.sendUp(quitMessage)
            self.sendDown(quitMessage)

        elif sender == self.__UpNode:
            self.sendDown(quitMessage)
            
        elif sender == self.__DownNode:
            self.sendUp(quitMessage)

class Database():
    def __init__(self):
        self.connection = sqlite3.connect('database.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        
        self.knownInit()
        self.onlineInit()

        self.cursor.execute("DELETE FROM online") #empty online database on exit
        self.cursor.execute(f"""UPDATE known SET Online = 0""")
        self.connection.commit()

        threading.Thread(target = self.timeBasedLogout).start()

    def quit(self):
        self.cursor.execute("DELETE FROM online") #empty online database on exit
        self.cursor.execute(f"""UPDATE known SET Online = 0""")
        self.connection.commit()
        self.connection.close()

    def timeBasedLogout(self):
        global ProgramQuit
        while ProgramQuit == False:
            self.cursor.execute(f"""UPDATE known SET Online = 0 WHERE LastOnline < {time.time() - 600}""")
            time.sleep(5)

    def knownInit(self):
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS known (
            Hash text NOT NULL PRIMARY KEY,
            NodeID text,
            PublicKeyN int,
            PublicKeyE int,
            Online int,
            LastOnline int
            )""")
            self.connection.commit()
        except:
            print("ERROR: Database Error")

    def onlineInit(self):
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS online (
            Hash text NOT NULL PRIMARY KEY,
            CircuitID text,
            ExitIP text,
            ExitPort int,
            NodeID text,
            FOREIGN KEY (NodeID) REFERENCES known(NodeID)
            )""")
            self.connection.commit()
        except:
            print("ERROR: Database Error")
    
    def getKeys(self, NodeID):
        hashID = Cryptography.hash(NodeID)
        self.cursor.execute(f"SELECT PublicKeyN, PublicKeyE FROM known WHERE Hash='{hashID}'")
        data = self.cursor.fetchall()
        if data != []:
            return data[0]
        else:
            return (None, None)

    def getLocation(self, NodeID):
        self.cursor.execute(f"SELECT ExitIP, ExitPort FROM online WHERE NodeID='{NodeID}'")
        data = self.cursor.fetchall()
        if data != []:
            ipAddr = data[0]
        else:
            ipAddr = (None, None)

        self.cursor.execute(f"SELECT CircuitID FROM online WHERE NodeID='{NodeID}'")
        data = self.cursor.fetchall()
        try:
            CircuitID = data[0][0]
        except:
            CircuitID = None
        return [CircuitID, ipAddr]

    def getCircuitIP(self, CircuitID):
        circuitHash = Cryptography.hash(CircuitID)
        self.cursor.execute(f"SELECT ExitIP, ExitPort FROM online WHERE Hash='{circuitHash}'")
        data = self.cursor.fetchall()
        if data != []:
            ipAddr = data[0]
        else:
            ipAddr = (None, None)
        return ipAddr

    def register(self, NodeID, PublicKey, CircuitID, EndIP):
        self.cursor.execute(f"SELECT * FROM known WHERE NodeID='{NodeID}'")
        data = self.cursor.fetchall()
        if data != []:
            return False
        else:
            self.cursor.execute(f"""INSERT or IGNORE INTO known VALUES (
            '{Cryptography.hash(NodeID)}', 
            '{NodeID}', 
            {int(PublicKey[0])}, 
            {int(PublicKey[1])}, 
            1,
            {int(time.time())}
            )""")

            self.cursor.execute(f"""INSERT or IGNORE INTO online VALUES (
            '{Cryptography.hash(CircuitID)}', 
            '{CircuitID}', 
            '{EndIP[0]}', 
            {EndIP[1]},
            '{NodeID}'
            )""")
            knownIPs.append(EndIP)
            self.connection.commit()
            return True
    
    def login(self, timestamp, NodeID, CircuitID, ExitIP, signature, toVerify):
        self.cursor.execute(f"SELECT * FROM known WHERE NodeID='{NodeID}'")
        data = self.cursor.fetchall()

        key = self.getKeys(NodeID)

        if data == []:
            return False
        else:
            print(data)
            if Cryptography.verify(toVerify, signature, key) == True:
                nodeIDHash = Cryptography.hash(NodeID)
                self.cursor.execute(f"""UPDATE known SET Online = 1, 
                                        LastOnline = {int(timestamp)} 
                                        WHERE Hash = '{nodeIDHash}'""")

                self.cursor.execute(f"""INSERT or IGNORE INTO online VALUES (
                '{Cryptography.hash(CircuitID)}', 
                '{CircuitID}', 
                '{ExitIP[0]}', 
                {ExitIP[1]},
                '{NodeID}'
                )""")

                self.connection.commit()
                knownIPs.append(ExitIP)
                return True
            else:
                return False
                
        #self.cursor.execute(f"UPDATE known SET Online = 1, LastOnline = {int(timestamp)} WHERE Hash = '{nodeIDHash}'")
        #self.cursor.execute(f"INSERT or IGNORE INTO online VALUES ('{circuitHash}', '{CircuitID}', '{ExitIP[0]}', {ExitIP[1]}, '{NodeID}')")
        #self.connection.commit()

DBQueue = LimitlessQueue()

def serialDatabaseExecution():
    while ProgramQuit == False:
        if DBQueue.isEmpty() == False:
            command = DBQueue.dequeue()
            if command[0] == 'login':
                Transmission.login(command[1], command[2])
                time.sleep(1.5)
            elif command[0] == 'register':
                Transmission.register(command[1], command[2])
                time.sleep(1.5)
            elif command[0] == 'nodeInfo':
                Transmission.nodeInfo(command[1], command[2])
                time.sleep(1.5)

class Transmission():
    def interfaceInit():
        global choicesIP, sock, database, currentIP, tempCircuits
        validChoices = []
        print("Network Interface Selection")
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        for x in range(len(choicesIP)):
            validChoices.append(str(x + 1))
            print(str(x + 1) + ". " + choicesIP[x])
        while True:
            choice = input("Please select the network interface you wish to use: ")
            if choice in validChoices:
                while True:
                    portChoice = input("Please enter the port you wish to use [Default: 107]: ")
                    try:
                        if portChoice == '':
                            portChoice = 107
                            break
                        else:
                            portChoice = int(portChoice)
                            break
                    except:
                        print("ERROR: Invalid Port Number")
                currentIP = (choicesIP[int(choice) - 1], portChoice)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #configures socket as UDP socket
                sock.bind(currentIP) #binds the specified IP address as the IP of the packet
                threading.Thread(target = Transmission.receiveAgent).start()
                break
            else:
                print("ERROR: Invalid Choice")
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print("")
        tempCircuits = [None] * 60

        for x in range(25):
            newCircuit = TempCircuit()
            knownIPs.append(newCircuit.getIP())
            tempCircuits[x] = newCircuit

        database = Database()

    def moveCircuit(circuitID):
        global usedCircuits, tempCircuits
        for x in range(len(tempCircuits)):
            if tempCircuits[x].getCircuitID() == circuitID:
                usedCircuits.append(tempCircuits.pop(x))
                break

    def send(msg, recipient):
        sock.sendto(msg, recipient)

    def receiveAgent():
        while True:
            try:
                data, sender = sock.recvfrom(1024)
                threading.Thread(target = Transmission.packetHandler, args=(data, sender)).start()
                if ProgramQuit == True:
                    break
            except:
                break

    def packetHandler(data, sender): #[timestamp, "DATA", destinationID, [msgID, circuitID, publicKey], payload, signature]
        global DBQueue
        data = pickle.loads(data)
        timestamp = data[0]
        header = data[1]
        if time.time() > timestamp + 100:
            pass #timeout, pass
        #circuit-routed packets
        elif header == "LOGIN": #format: [timestamp, "LOGIN", "SERVER", [msgID, circuitID, publicKey], login_payload, signature]
            DBQueue.enqueue(['login', data, sender])
        elif header == "REGISTER": #format: [timestamp, "REGISTER", "SERVER", [msgID, circuitID, publicKey], register_payload, signature]
            DBQueue.enqueue(['register', data, sender])
        elif header == "NODEINFO": #format: [timestamp, "NODEINFO", "SERVER", [msgID, circuitID, publicKey], info_payload, signature]
            DBQueue.enqueue(['nodeInfo', data, sender])
        
        #direct packets
        elif header == "TEST": #format: [timestamp, "TEST"]
            Transmission.test(sender)
        elif header == "GETNODES": #format: [timestamp, "GETNODES"]
            Transmission.getNodes(sender)

    def login(data, sender):
        #[timestamp, "LOGIN", "SERVER", [msgID, circuitID, publicKey], login_payload, signature]
        #login_payload(unencrypted) = NodeID
        
        login_payload = data[4]
        NodeID = Cryptography.asymDecrypt(login_payload, myPublicKey, myPrivateKey)
        
        CircuitID = data[3][1]
        key = data[3][2]
        signature = data.pop(5)
        result = database.login(data[0], NodeID, CircuitID, sender, signature, pickle.dumps(data))

        if result == True:
            payload = ["SERVER", ["SERVERREPLY", Cryptography.asymEncrypt("LOGIN:SUCCESS", key)]]
        else:
            payload = ["SERVER", ["SERVERREPLY", Cryptography.asymEncrypt("LOGIN:FAIL", key)]]

        msg = [time.time(), "DATA", CircuitID, ["FROMSRV", "SERVER", myPublicKey], payload]
        
        tempMsg = pickle.dumps(msg)
        sig = Cryptography.sign(tempMsg, myPrivateKey)
        msg.append(sig)
        msg = pickle.dumps(msg)
        Transmission.send(msg, sender)
        
    def register(data, sender):
        #[timestamp, "REGISTER", "SERVER", [msgID, circuitID, publicKey], register_payload, signature]
        #register_payload(unencrypted) = NodeID
        register_payload = data[4]
        NodeID = Cryptography.asymDecrypt(register_payload, myPublicKey, myPrivateKey)
        
        CircuitID = data[3][1]
        key = data[3][2]
        result = database.register(NodeID, key, CircuitID, sender)

        if result == True:
            payload = ["SERVER", ["SERVERREPLY", Cryptography.asymEncrypt("REGISTER:SUCCESS", key)]]
        else:
            payload = ["SERVER", ["SERVERREPLY", Cryptography.asymEncrypt("REGISTER:FAIL", key)]]

        msg = [time.time(), "DATA", CircuitID, ["FROMSRV", "SERVER", myPublicKey], payload]
        
        tempMsg = pickle.dumps(msg)
        sig = Cryptography.sign(tempMsg, myPrivateKey)
        msg.append(sig)
        msg = pickle.dumps(msg)
        Transmission.send(msg, sender)

    def getNodes(sender, internal=False):
        testprint("SENDING: GETNODE REPLY")
        NodeA = knownIPs[random.randint(0, len(knownIPs) - 1)]
        while True:
            NodeB = knownIPs[random.randint(0, len(knownIPs) - 1)]
            NodeC = knownIPs[random.randint(0, len(knownIPs) - 1)]
            if ((NodeA != NodeB) and (NodeA != NodeC) and (NodeB != NodeC)) or (len(knownIPs) < 3):
                break
        NodeList = [NodeA, NodeB, NodeC]
        for x in range(len(NodeList)):
            if NodeList[x] == sender:
                NodeList.pop(x)
                break

        if internal == False:
            msg = [time.time(), "REPLY:GETNODES", NodeList]
            sig = Cryptography.sign(pickle.dumps(msg), myPrivateKey)
            msg.append(sig)
            msg = pickle.dumps(msg)
            Transmission.send(msg, sender)

            #knownIPs.append(sender)
        elif internal == True:
            return NodeList

    def nodeInfo(data, sender): 
        #format: [timestamp, "NODEINFO", "SERVER", [msgID, circuitID, publicKey], info_payload, signature]
        CircuitID = data[3][1]
        info_payload = data[4]
        NodeID = Cryptography.asymDecrypt(info_payload, myPublicKey, myPrivateKey)
        key = database.getKeys(NodeID)
        location = database.getLocation(NodeID)
        payload = [key, location[0], location[1]]
        payload = ["SERVER", ["INFO", payload]]

        msg = [time.time(), "DATA", CircuitID, ["FROMSRV", "SERVER", myPublicKey], payload]
        
        tempMsg = pickle.dumps(msg)
        sig = Cryptography.sign(tempMsg, myPrivateKey)
        msg.append(sig)
        msg = pickle.dumps(msg)
        Transmission.send(msg, sender)

    def test(sender):
        testprint("SENDING: TEST REPLY")
        msg = [time.time(), "REPLY:TEST", serverName, announcements, myPublicKey]
        msg = pickle.dumps(msg)
        Transmission.send(msg, sender)

if __name__ == '__main__':
    try:
        globalConfig()
        serverName = input("Enter the name of the server: ")
        announcements = input("Enter any announcements you wish to send: ")
        threading.Thread(target = serialDatabaseExecution).start()
        Transmission.interfaceInit()
    except KeyboardInterrupt:
        exit()