import socket, threading, time, os, pickle, random, time, sqlite3

from threading import Thread
from logging import exception
from requests import get

###OWN MODULES###

import HGHelp as Help
from structures import Queue
from structures import LimitlessQueue
import HGCrypto as Cryptography
import HGTesting as Testing
from HGMessenger import Messenger

###END###

###SERVER DEFAULTS###

serverIP = ("192.168.0.1", 107) #Default address of the specified data server until the global config is setup
serverName = "EMPTY" #Default name of the specified data server until the global config is setup
serverOnline = False #indicates whether or not the specified server is online, found by sending a test packet and waiting for a reply with the server's name
#serverName is chosen by the server itself rather than the user
serverAnnouncements = ''
serverKey = (0, 0)

###END###

loginStatus = False
registerStatus = False
packetFailure = False

myPublicKey = () #sets own public/private key as empty until user is configured
myPrivateKey = ()
ProgramQuit = False
hexChars = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"] #all valid hexadecimal characters

base64Chars = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
                "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z",
                "0","1","2","3","4","5","6","7","8","9","+","/","="] #all valid base64 characters, '=' is padding

users = []
configFiles = []
username = ""

primeList = None

nonOwnCircuits = [] #circuits that this instance has no control of
ownCircuit = None #same as above but with control
ongoingPackets = [] #packets that are awaiting replies
joinableNodes = []

TIMEOUT = 120 #two minute timeout
RANDOM_CONST = 3

choicesIP = []

try:
    tempSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tempSock.connect(("10.255.255.255", 80)) #arbitrary IP address used to get local IP address of network rather than loopback
    choicesIP.append(tempSock.getsockname()[0])
    tempSock.close()
except:
    print("ERROR: Not connected to any networks!")
    ProgramQuit = True

choicesIP.append(socket.gethostbyname(socket.gethostname()))

messenger = None
ownCircuit = None

temp_pubKey, temp_CircuitID, temp_ExitIP = None, None, None

"""
Packet Layouts:

##General Layout
    [timestamp, header, destinationID, [msgID, circuitID, publicKey], payload, signature]
    payload = encrypted byte(pickle) dump
    payload(unencrypted, non-byte form) = [sender, data] #where sender is the nodeID of the sender
    data = ["APP_TYPE", APP_DATA] #example: ["MSG", message]

##To Server
    via Circuit: [timestamp, header, "SERVER", [msgID, circuitID, publicKey], payload, signature] #login, register, nodeInfo
    direct: [timestamp, header] #getNodes & test

    login:
        [timestamp, "LOGIN", "SERVER", [msgID, circuitID, publicKey], login_payload, signature]
        login_payload(unencrypted) = NodeID
            Enter timestamp, circuitID and endIP to online database if signature is verified

    register:
        [timestamp, "REGISTER", "SERVER", [msgID, circuitID, publicKey], register_payload, signature]
        register_payload(unencrypted) = NodeID
            Check if NodeID already exists in Database
            If it exists: reply with existence error
            Else:
                Verify signature
                Add timestamp, circuitID, publicKey, endIP, and NodeID to database (both online and known)

    nodeInfo:
        [timestamp, "NODEINFO", "SERVER", [msgID, circuitID, publicKey], info_payload, signature]
        info_payload(unencrypted) = NodeID(to be searched)
        Verify Signature and return data
            REPLY:
                [timestamp, "DATA", circuitID, [msgID, "SERVER", publicKey], return_payload, signature]

##To Another User
    data:
        [timestamp, "DATA", destinationID, [msgID, circuitID, publicKey], payload, signature]
        payload = encrypted byte(pickle) dump
        payload(unencrypted, non-byte form) = [sender, data] #where sender is the nodeID of the sender
        data = ["APP_TYPE", APP_DATA] #example: ["MSG", message]
    reply:
        [timestamp, "REPLY:msgID", recipientIP]
        if recipientIP matches own IP: Pop MsgID from ongoingPackets
    request:
        [timestamp, "REQUEST:type" ---] #different depending on case
        [timestamp, "REQUEST:JOINCIRCUIT", circuitID, publicKey, signature]
        Verify signature using publicKey
            Reply:
            [timestamp, "REPLY:circuitID", recipientIP]

"""

try:
    publicIP = get("https://api.ipify.org").text
    inetStatus = True
except:
    print("ERROR: Not connected to Internet")
    publicIP = "Not connected to Internet"
    inetStatus = False

valid = ["c", "C", "n", "N", "q", "Q", "t", "T"]

class Interface():
    def bootstrap():
        global sock, currentIP
        #prints introductory ascii art
        print(""" 
 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@             _____ _           
  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@             |_   _| |      
     @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                  | | | |__   ___  
     @                             @                  | | | '_ \ / _ \ 
     @                             @                  | | | | | |  __/ 
     @                             @                  \_/ |_| |_|\___| 
     @@                           @@      __    __                                          __   
      @@  @@@@@@@@@@@@@@@@@@@@@  @@     /  |  /  |                                        /  |     
        @   @@@@@@@@@@@@@@@@@   @       ██ |  ██ |  ______   __    __   ______    ______  ██ |  ______    _______  _______ 
          @@   @@@@@@@@@@@   @@         ██ |__██ | /      \ /  |  /  | /      \  /      \ ██ | /      \  /       |/       |
             @@   @@@@@   @@            ██    ██ |/██████  |██ |  ██ |/██████  |/██████  |██ | ██████  |/███████//███████/ 
                 @  @  @                ████████ |██ |  ██ |██ |  ██ |██ |  ██/ ██ |  ██ |██ | /    ██ |██      \██      \ 
                 @@   @@                ██ |  ██ |██ \__██ |██ \__██ |██ |      ██ \__██ |██ |/███████ | ██████  |██████  |
                @@     @@               ██ |  ██ |██    ██/ ██    ██/ ██ |      ██    ██ |██ |██    ██ |/     ██//     ██/ 
             @@           @@            ██/   ██/  ██████/   ██████/  ██/        ███████ |██/  ███████/ ███████/ ███████/  
          @@                 @@                                                 /  \__██ |             
      @@                         @@                                             ██    ██/           
     @@             @             @@                                             ██████/       
     @        @@@@@@@@@@@@@        @                    ______          _                  _ 
     @   @@@@@@@@@@@@@@@@@@@@@@@   @                    | ___ \        | |                | |
     @  @@@@@@@@@@@@@@@@@@@@@@@@@  @                    | |_/ / __ ___ | |_ ___   ___ ___ | |
     @                             @                    |  __/ '__/ _ \| __/ _ \ / __/ _ \| |
     @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    | |  | | | (_) | || (_) | (_| (_) | |
  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                 \_|  |_|  \___/ \__\___/ \___\___/|_|
 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    """)
        validChoices = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #configures socket as UDP socket
        print("Network Interface Selection")
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print("Your Public IP Address is:", publicIP)
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        for x in range(len(choicesIP)):
            validChoices.append(str(x + 1))
            print(str(x + 1) + ". " + choicesIP[x])
        while True:
            choice = input("Please select the network interface you wish to use: ")
            if choice in validChoices:
                while True:
                    portChoice = input("Please enter the port you wish to use [Default: 100]: ")
                    try:
                        if portChoice == '':
                            currentIP = (choicesIP[int(choice) - 1], 100)
                            sock.bind(currentIP) #binds the specified IP address as the IP of the packet
                            break
                        else:
                            portChoice = int(portChoice)
                            currentIP = (choicesIP[int(choice) - 1], portChoice)
                            sock.bind(currentIP) #binds the specified IP address as the IP of the packet
                            break
                    except:
                        print("ERROR: Invalid Port Number")
                threading.Thread(target = Transmission.receiveAgent).start()
                break
            else:
                print("ERROR: Invalid Choice")
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print("")
        initAnim() #initialises loading animation
        loadAnim(20) #value '20' indicates that the loading bar is to go through at once
        print("") #print newline
        Interface.login() #login subroutine

    def login():
        global serverName, serverIP, serverOnline, ProgramQuit, users, configFiles
        Config.globalConfig()
        users = os.listdir('./config/') #the users that can access the protocol are the filenames in the ./config directory
        configFiles = users #saves list of files to global variable
        for x in range(len(users)): #removes filename extension from names of users '.hg', all config files end in the same extensions (inclusing global config) to avoid inter-program conflict
            users[x] = (users[x])[:-3]
        print("""
USER SELECT:
____________
        """)

        if users == []: #if no users are in the config directory
            print("No Users Registered")
        else:
            for x in range(len(users)): #prints selection menu for all users in the config directory
                lognum = str(x + 1) + "."
                print(lognum, users[x])
                
                valid.append(str(x + 1)) # adds given selections to the valid options array

        print("---------------------------")
        if serverIP[0] == "EMPTY": #default value for server IP
            print("Server: Not Configured")
        else: #prints the value saved in the global config file
            print(f"Server: {serverName} @ {serverIP[0]}/{serverIP[1]}")
        if serverAnnouncements != '':
            print("Announcements:", serverAnnouncements)
        if serverOnline == True: #the server is set as online if the protocol can successfully send a test packet to the server (and it replies)
            status = "Online"
        else:
            status = "Offline" 
        print("Status:", status)
        print(f"Current IP: {currentIP[0]}/{currentIP[1]}")
        print("---------------------------")
        print("C. Configure Central Server")
        print("T. Test Connection")
        print("N. New User")
        print("Q. Quit\n")
        
        while True:
            choice = input("Please select an option: ")
            if choice in valid: #unless the user option is in the valid options array, the program will display an error
                break
            else:
                inputUnrec()

        if (choice == "q") or (choice == "Q"): #quits program
            ProgramQuit = True #quits program (pass)
        
        elif (choice == "t") or (choice == "T"): #tests connection to server manually, occurs at program bootstrap
            Transmission.testServer()
            Interface.login()

        elif (choice == "c") or (choice == "C"): #configures the IP Address and port of the central data server
            IP = input("Enter IP Address of Server: ")
            PORT = input("Enter Port of Server: ")
            status = Testing.IPValidation(IP, PORT)
            if status == True:
                serverIP = (IP, int(PORT))
            else:
                print("ERROR: Incorrect format for IP Address")
            Config.updateGlobalConfig()
            Interface.login()

        elif (choice == "n") or (choice == "N"): #configures a new user
            if serverOnline == False:
                Transmission.testServer()
            if serverOnline == True:
                Config.newConfig()
            else:
                print("Server is offline, quitting...")
                ProgramQuit = True
        
        else:
            if serverOnline == False:
                Transmission.testServer()
            if serverOnline == True:
                Config.login(choice) #logs into the specified user
            else:
                print("Server is offline, quitting...")
                ProgramQuit = True
    
    def console(): #console code
        global ProgramQuit
        while (ProgramQuit == False): #iterates until the quit flag is put up
            consoleInput = input(f"|{username}| > ") #outputs the console and takes in user input
            Interface.parser(consoleInput) #sends input to parser
    
    def parser(input):
        parsedIn = []
        curWord = ""
        index = 0
        spaces = 0
        for x in range(len(input)): #separates commands and arguments
            if input[x] == " ":
                spaces += 1 #computes the number of spaces in the given input string
        words = spaces + 1 #using the laws of (most) languages that use the latin alphabet, the number of words in a sentence will always be one more than the spaces
        parsedIn = [None] * words #assign Nonetype to all indexes of parsed input array
        
        for x in range(len(input)): #separates words and adds them to the aforementioned array
            if x == (len(input) - 1):
                curWord = curWord + str(input[x])
                parsedIn[index] = curWord
                index += 1
                curWord = ""
            elif input[x] != " ":
                curWord = curWord + str(input[x])
            else:
                parsedIn[index] = curWord
                index += 1
                curWord = ""
        Interface.choicer(parsedIn) #sends parsed input to command choice selection subroutine

    def choicer(input): 
        global ProgramQuit, messenger
        main = input[0]
        if (main == "exit") or (main == "quit"): #executes specified subroutine for chosen command
            ProgramQuit = True #program quit flag
        elif main == None:
            pass
        elif main == "show":
            try: #argument selection
                if input[1] == "known":
                    try:
                        print(database.showKnown(input[2]))
                    except:
                        print(database.showKnown())
                elif input[1] == "-h" or input[1] == "--help":
                    raise
                elif input[1] == "online":
                    try:
                        print(database.showOnline(input[2]))
                    except:
                        print(database.showOnline())
                else:
                    inputUnrec()
            except: #activates help menu for specified command
                Help.show()
        elif main == "help":
            Help.main()
        elif (main == "messenger") or (main == "chat"):
            try:
                NodeID = input[1]
                if NodeID != username:
                    info = database.showOnline(NodeID)
                    if info != []:
                        CircuitID = info[0][0]
                        ipAddr = (info[0][1], info[0][2])
                        info = database.showKnown(NodeID)
                        key = (info[0][1], info[0][2])
                        messageList = database.getMessages(NodeID)
                        messenger = Messenger(username, key, NodeID, messageList)
                        while messenger.quitStatus == False:
                            time.sleep(0.5)
                            nextPacket = messenger.getNextPacket()
                            if nextPacket != None:
                                Transmission.send(nextPacket, ipAddr)
                        database.writeMessages(NodeID, messenger.getMessageList())
                    else:
                        print("ERROR: Either user isn't online or you have not used 'getinfo' first!")
                else:
                    print("ERROR: You cannot chat with yourself!")
            except:
                Help.messenger()
        elif main == "whoami":
            print(username)
        elif main == "getinfo":
            try:
                selectID = input[1]
                ownCircuit.nodeInfo(selectID)
            except:
                Help.getinfo()   
        else: #unrecognised input
            inputUnrec()

class Config():
    def userConfig(): #configures settings for specified user, specifically their database (which contains the friends list) and config file (which contains their public key, locked using AES)
        global database, serverIP, serverName, myPublicKey, myPrivateKey
        database = Database()
        lines = []
        userFile = open("./config/" + str(username) + ".hg", "r")
        for x in userFile.readlines():
            lines.append(x.strip()) #remove new line at end of each string
        n = int(lines[1])
        e = int(lines[3])
        d = int(lines[5])
        myPublicKey = (n, e)
        myPrivateKey = (n, d)

    def newConfig():
        global ownCircuit, username, myPublicKey, myPrivateKey, database
        print("Generating Keypair...")
        myPublicKey, myPrivateKey = Cryptography.asymKeyGen(100)
        ownCircuit = OwnCircuit()
        ownCircuit.buildCircuit()
        if ProgramQuit != True:
            while True:
                username = input("Enter the name of the new user: ")
                ownCircuit.register()
                if registerStatus == True:
                    break
                elif ProgramQuit == True:
                    print("Exit flag raised: Quitting.")
                    return
                else:
                    print("Registration Failed: Try New Username")

            try: #Try creating a global file, redirects to read if exists
                userFile = open("./config/" + str(username) + ".hg", "x") #creates the specified file
                userFile.close() #closes the file to enable access to writing/appending mode
                userFile = open("./config/" + str(username) + ".hg", "w")
                lines = ["[N]", str(myPublicKey[0]), "[PUBLIC KEY E]", str(myPublicKey[1]), "[PRIVATE KEY D]", str(myPrivateKey[1])]
                for x in range(len(lines)):
                    userFile.writelines(lines[x] + "\n")
                userFile.close()
                database = Database()
                Interface.console()
            except:
                print("ERROR: User already exists")

    def updateUserConfig():
        userFile = open("./config/" + str(username) + ".hg", "w")
        lines = ["[N]", str(myPublicKey[0]), "[PUBLIC KEY E]", str(myPublicKey[1]), "[PRIVATE KEY D]", str(myPrivateKey[1])]
        for x in range(len(lines)):
            userFile.writelines(lines[x] + "\n")
    
    def globalConfig(): #subroutine for accessing data in the global config file 'Global.hg'
        global globalFile, serverIP, serverName
        try: #Try creating a global file, redirects to read if exists
            globalFile = open("Global.hg", "x") #creates the specified file
            globalFile.close() #closes the file to enable access to writing/appending mode
            Config.updateGlobalConfig()
        except: #Read global file
            lines = []
            globalFile = open("Global.hg", "r")
            for x in globalFile.readlines():
                lines.append(x.strip()) #remove new line at end of each string
            serverIP = (lines[1], int(lines[3]))
            serverName = str(lines[5])
    
    def updateGlobalConfig(): #creates or updates the global config file if data is altered in the program
        globalFile = open("Global.hg", "w")
        lines = ["[IP]", serverIP[0], "[PORT]", str(serverIP[1]), "[SERVER NAME]", serverName]
        for x in range(len(lines)):
            globalFile.writelines(lines[x] + "\n")
    
    def login(user):
        global username, ownCircuit, ProgramQuit, loginStatus
        #config all from config file
        username = users[int(user) - 1]
        Config.userConfig()
        ownCircuit = OwnCircuit()
        ownCircuit.buildCircuit()
        if ProgramQuit != True:
            ownCircuit.login()
        if loginStatus == False:
            print("Credentials do not match that of the server! Quitting.")
            ProgramQuit = True
        Interface.console()

class Database():
    def __init__(self):
        databases = os.listdir('./databases/')
        for x in range(len(databases)):
            databases[x] = (databases[x])[:-3]

        if username not in databases:
            print("Database doesn't exist for specified user. Creating database.")
        
        self.connection = sqlite3.connect('./databases/' + str(username) + '.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.knownInit()
        self.onlineInit()
        self.messagesInit()

    def quit(self):
        self.cursor.execute("DELETE FROM online") #empty online database on exit
        self.connection.commit()
        self.connection.commit()
        self.connection.close()

    def knownInit(self):
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS known (
            NodeID text NOT NULL PRIMARY KEY,
            PublicKeyN int,
            PublicKeyE int,
            Online int,
            LastOnline text
            )""")

            self.connection.commit()
        except:
            print("ERROR: Database Error")

    def onlineInit(self):
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS online (
            CircuitID text NOT NULL PRIMARY KEY,
            ExitIP text,
            ExitPort int,
            NodeID text,
            FOREIGN KEY (NodeID) REFERENCES known(NodeID)
            )""")
            self.connection.commit()
        except:
            print("ERROR: Database Error")

    def messagesInit(self):
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
            Timestamp int,
            NodeID text,
            Own int,
            Message text,
            FOREIGN KEY (NodeID) REFERENCES known(NodeID)
            )""")
            self.connection.commit()
        except:
            print("ERROR: Database Error")
    
    def getMessages(self, NodeID):
        self.cursor.execute(f"SELECT Timestamp, Own, Message FROM messages WHERE NodeID='{NodeID}' ORDER BY Timestamp ASC")
        data = self.cursor.fetchall()
        return data

    def writeMessages(self, NodeID, MessageList):
        #list layout: [[timestamp, own, message],[timestamp, own, message]]
        try:
            for x in range(len(MessageList)):
                self.cursor.execute(f"""INSERT or IGNORE INTO messages VALUES (
                    {int(MessageList[x][0])},
                    '{NodeID}',
                    {int(MessageList[x][1])},
                    '{MessageList[x][2]}'
                    )""")
                self.connection.commit()
        except:
            pass

    def showKnown(self, NodeID = None):
        if NodeID == None:
            self.cursor.execute(f"SELECT * FROM known")
        else:
            self.cursor.execute(f"SELECT * FROM known WHERE NodeID='{NodeID}'")
        data = self.cursor.fetchall()
        return data

    def showOnline(self, NodeID = None):
        if NodeID == None:
            self.cursor.execute(f"SELECT * FROM online")
        else:
            self.cursor.execute(f"SELECT * FROM online WHERE NodeID='{NodeID}'")
        data = self.cursor.fetchall()
        return data

    def getKeys(self, NodeID):
        hashID = Cryptography.hash(NodeID)
        self.cursor.execute(f"SELECT PublicKeyN, PublicKeyE FROM known WHERE Hash='{hashID}'")
        data = self.cursor.fetchall()
        if data == []:
            return (None, None)
        else:
            return data[0]

    def writeKnown(self, NodeID, PublicKeyN, PublicKeyE, Online, LastOnline):
        self.cursor.execute(f"INSERT or IGNORE INTO known VALUES ('{NodeID}', {PublicKeyN}, {PublicKeyE}, {Online}, '{LastOnline}')")
        self.connection.commit()

    def writeOnline(self, CircuitID, ExitIP, NodeID):
        self.cursor.execute(f"INSERT or IGNORE INTO online VALUES ('{CircuitID}', '{ExitIP[0]}', {ExitIP[1]}, '{NodeID}')")
        self.connection.commit()

    def deleteKnown(self, NodeID):
        self.cursor.execute(f"DELETE FROM known WHERE NodeID='{NodeID}'")
        self.connection.commit()

    def deleteOnline(self, NodeID):
        self.cursor.execute(f"DELETE FROM online WHERE NodeID='{NodeID}'")
        self.connection.commit()

class OwnCircuit():
    def __init__(self):
        global joinableNodes
        self.__idSet = False
        self.__CircuitID = self.__GenerateCircuitID()
        self.__DownNode = ('EMPTY', 0)
        self.__endIP = ('EMPTY', 0)
        
        Transmission.getNodes()
        
    def buildCircuit(self):
        self.__request("JOINCIRCUIT")

    def getCircuitID(self):
        return self.__CircuitID

    def setDownNode(self, IP):
        self.__DownNode = IP

    def getDownNode(self):
        return self.__DownNode

    def setEndNode(self, IP):
        self.__endIP = IP

    def __GenerateCircuitID(self):
        if self.__idSet == False:
            self.__idSet = True
            tempID = ''
            for x in range(8):
                tempID = tempID + base64Chars[random.randint(0, len(base64Chars) - 1)]
            return tempID
        else:
            print("ERROR: CircuitID already set!")

    def __GenerateMsgID(self):
        msgID = ""
        for x in range(8):
            msgID = msgID + base64Chars[random.randint(0, len(base64Chars) - 1)]
        return msgID

    def __send(self, msg):
        Transmission.send(msg, self.__DownNode)

    def login(self):
        print("Logging into server...")
        timestamp = time.time()
        login_payload = username
        login_payload = Cryptography.asymEncrypt(login_payload, serverKey)
        msgID = self.__GenerateMsgID()
        msg = [timestamp, "LOGIN", "SERVER", [msgID, self.__CircuitID, myPublicKey], login_payload]
        signature = Cryptography.sign(pickle.dumps(msg), myPrivateKey)
        msg.append(signature)
        msg = pickle.dumps(msg)

        ongoingPackets.append("LOGIN")
        self.__send(msg)
        timeWait = Transmission.wait(timestamp, "LOGIN")
        if (timeWait == 'TIMEOUT') or (self.__endIP[0] == 'EMPTY'):
            print("Unable to connect to the network, please try again later.")
            ProgramQuit = True

    def register(self):
        global ProgramQuit
        print(f"Registering User: {username}")
        timestamp = time.time()
        register_payload = username
        register_payload = Cryptography.asymEncrypt(register_payload, serverKey)
        msgID = self.__GenerateMsgID()
        msg = [timestamp, "REGISTER", "SERVER", [msgID, self.__CircuitID, myPublicKey], register_payload]
        signature = Cryptography.sign(pickle.dumps(msg), myPrivateKey)
        msg.append(signature)
        msg = pickle.dumps(msg)

        ongoingPackets.append("REGISTER")
        self.__send(msg)
        timeWait = Transmission.wait(timestamp, "REGISTER")
        if (timeWait == 'TIMEOUT') or (self.__endIP[0] == 'EMPTY'):
            ProgramQuit = True

    def nodeInfo(self, NodeID):
        global temp_pubKey, temp_CircuitID, temp_ExitIP
        timestamp = time.time()
        info_payload = Cryptography.asymEncrypt(NodeID, serverKey)
        msgID = self.__GenerateMsgID()
        msg = [timestamp, "NODEINFO", "SERVER", [msgID, self.__CircuitID, myPublicKey], info_payload]
        signature = Cryptography.sign(pickle.dumps(msg), myPrivateKey)
        msg.append(signature)
        msg = pickle.dumps(msg)

        ongoingPackets.append("NODEINFO")
        self.__send(msg)
        timeWait = Transmission.wait(timestamp, "NODEINFO")
        if (timeWait == 'TIMEOUT') or (self.__endIP[0] == 'EMPTY'):
            ProgramQuit = True
        else:
            exists = database.showKnown(NodeID)
            if exists == [] and temp_pubKey != (None, None):
                if temp_CircuitID == None:
                    database.writeKnown(NodeID, temp_pubKey[0], temp_pubKey[1], 0, 0)
                else:
                    database.writeKnown(NodeID, temp_pubKey[0], temp_pubKey[1], 1, time.time())
                    database.writeOnline(temp_CircuitID, temp_ExitIP, NodeID)
            elif temp_pubKey != (None, None):
                database.writeOnline(temp_CircuitID, temp_ExitIP, NodeID)
    
    def __request(self, type):
        global ProgramQuit
        if type == "JOINCIRCUIT":
            print("Setting up circuit...")
            successful = False
            x = 0
            while successful == False:
                timestamp = time.time()
                msg = [timestamp, "REQUEST:JOINCIRCUIT", self.__CircuitID, myPublicKey]
                signMsg = pickle.dumps(msg)
                signature = Cryptography.sign(signMsg, myPrivateKey)
                msg.append(signature)
                msg = pickle.dumps(msg)

                randomNode = joinableNodes[x]
                print(f"Asking {randomNode} to join circuit...")
                ongoingPackets.append(self.__CircuitID)
                Transmission.send(msg, randomNode)
                waitResult = Transmission.wait(timestamp, self.__CircuitID, 10)
                if waitResult == True:
                    successful = True
                    self.setDownNode = randomNode
                    break
                elif waitResult == 'TIMEOUT':
                    print(f"No reply from {randomNode}")
                    x += 1
                elif waitResult == 'PACKET_FAIL':
                    print("ERROR: Request failed to send!")
                    x += 1
                    break
                else:
                    x += 1
                
                if x == (len(joinableNodes)):
                    break
            
            waitResult = False
            ongoingPackets.append(f"END{self.__CircuitID}")
            if successful == True:
                print(f"{self.__DownNode} accepted request!")
                print("Waiting for EndNode...")
                waitResult = Transmission.wait(timestamp, f"END{self.__CircuitID}", 40)
            
            if waitResult == False or waitResult == 'TIMEOUT': 
                successful = False                    
            
            if successful == False:
                print("Failed to connect to any nodes, quitting...")
                ProgramQuit = True
            else:
                print(f"End Node is: {self.__endIP}")

    def quit(self, fromOther=False):
        if fromOther == True:
            pass

class NonOwnCircuit():
    def __init__(self, CircuitID, PublicKey, EndStatus):
        self.__CircuitID = CircuitID
        self.__publicKey = PublicKey
        self.__EndStatus = EndStatus
        if self.__EndStatus == True:
            self.__UpNode = None #node towards owner         
        else:
            self.__DownNode = None #node towards end
            self.__UpNode = None

    def getCircuitID(self):
        return self.__CircuitID

    def sendUp(self, data): #sends data up the circuit (to the owner)
        #[timestamp, header, destinationID, [msgID, circuitID, publicKey], payload, signature]
        destinationID = data[2]
        msgID = data[3][0]
        circuitID = data[3][1]
        data = pickle.dumps(data)
        ongoingPackets.append(msgID) #adds packet to list of packets without reply
        while True:
            Transmission.send(data, self.__UpNode)
            time.sleep(5)
            if msgID not in ongoingPackets:
                break

    def sendDown(self, data): #sends data out of the circuit or down the circuit (towards the end node)
        #get ip of end node of destination from server and send
        #[timestamp, header, destinationID, circuitID, payload, signature]
        destinationID = data[2]
        msgID = data[3][0]
        tempData = data
        signature = tempData.pop(5)
        tempData = pickle.dumps(tempData)
        

    def exit(self, sender = None):
        quitMessage = [time.time(), "QUIT", self.__CircuitID]
        quitMessage = pickle.dumps(quitMessage)
        if sender == None:
            Transmission.send(quitMessage, self.__UpNode)
            Transmission.send(quitMessage, self.__DownNode)
        elif sender == self.__UpNode:
            Transmission.send(quitMessage, self.__DownNode)
        elif sender == self.__DownNode:
            Transmission.send(quitMessage, self.__UpNode)

class Transmission():
### INTERNAL FUNCTIONS
    def send(msg, destination): #sends packet to destination via outgoing UDP socket
        global packetFailure, ProgramQuit
        try:
            sock.sendto(msg, destination)
        except:
            print("ERROR: Could not send packet")
            ProgramQuit = True
            packetFailure = True

    def receiveAgent():
        while True:
            try:
                data, sender = sock.recvfrom(1024)
                threading.Thread(target = Transmission.packetHandler, args=(data, sender)).start()
                if ProgramQuit == True:
                    break
            except:
                break

    def quit():
        sock.close()

    def checkOwnership(data):
        #[timestamp, "DATA", destinationID, [msgID, circuitID, publicKey], payload, signature]
        destinationID = data[2]
        circuitID = data[3][1]
        found = False
        inSenderCircuit = False
        isOwnCircuit = False
        index = 0
        for x in range(len(nonOwnCircuits)): #check if packet is on correct route
            if circuitID == nonOwnCircuits[x].getCircuitID(): #is sill on the sender's circuit
                found = True
                inSenderCircuit = True
                index = x
                break
            elif destinationID == nonOwnCircuits[x].getCircuitID(): #is on the recipient's circuit
                found = True
                index = x
                break
        
        if destinationID == ownCircuit.getCircuitID():
            found = True
            isOwnCircuit = True

        if found == True: #packet is on correct route
            if isOwnCircuit == True: #packet belongs to self
                return 'OWN', ownCircuit
            elif inSenderCircuit == True: # packet is still on the sender's circuit
                return 'IN_SENDER', nonOwnCircuits[x]
            else: # packet is on the recipient's circuit
                return 'IN_RECIPIENT', nonOwnCircuits[x]
        else: #packet is random
            return 'RANDOM', None

    def packetHandler(data, sender):
        try:
            data = pickle.loads(data)
            timestamp = data[0]
            header = data[1]
            if time.time() > timestamp + TIMEOUT: 
                pass # do nothing as packet has timed out
            elif header == "MSG":
                if messenger != None:
                    msg = Cryptography.asymDecrypt(data[3], myPublicKey, myPrivateKey)
                    messenger.printMessage(timestamp, msg, 0, True)
            elif (header == "LOGIN") or (header == "REGISTER") or (header == "NODEINFO"): #to server
                pass
            elif header == "DATA": #to/from anyone
                status, circuit = Transmission.checkOwnership(data)
                if status == "OWN":
                    Transmission.ownPacketHandler(data, sender)
                elif status == "IN_SENDER":
                    pass
                    #circuit.sendDown(data, sender)
                elif status == "IN_RECIPIENT":
                    pass
            elif header[:5] == 'REPLY':
                Transmission.replyHandler(data, sender)
            elif header[:7] == 'REQUEST':
                Transmission.requestHandler(data, sender)
        except:
            print("ERROR: Packet incorrectly formatted!")

    def replyHandler(data, sender):
        global serverName, serverAnnouncements, serverOnline, joinableNodes, serverKey, ownCircuit
        header = data[1]
        msgID = header[6:] #get characters after 'REPLY:'

        if msgID == "TEST":
            #[timestamp, header, servername, announcements]
            serverName = data[2]
            serverAnnouncements = data[3]
            serverKey = data[4]
            serverOnline = True
            Config.updateGlobalConfig()
        elif msgID == "GETNODES":
            #[timestamp, header, [NodeList]]
            joinableNodes = data[2]
        elif msgID == "JOINCIRCUIT": #circuit routed
            #[timestamp, header, CircuitID, recipientIP]
            destination = data[3]
            if destination != currentIP:
                return #exit if reply is not meant for self
            ownCircuit.setDownNode(sender)
            msgID = data[2]
        elif msgID == f"ENDCIRCUIT": #circuit routed
            #[timestamp, header, CircuitID, endIP, recipientIP]
            if data[2] == ownCircuit.getCircuitID():
                ownCircuit.setEndNode(data[3])
                msgID = "END" + data[2]
            else:
                for x in range(len(nonOwnCircuits)):
                    if nonOwnCircuits[x].getCircuitID() == data[2]:
                        nonOwnCircuits[x].handle(data, sender)
                        break
        else:
            destination = data[2]
            if destination != currentIP:
                return #exit if reply is not meant for self
        
        index = DataManipulation.linearSearch(msgID, ongoingPackets)
        if index != -1:
            ongoingPackets.pop(index)

    def requestHandler(data, sender):
        #[timestamp, "REQUEST:type", ----]
        header = data[1]
        requestType = header[8:]
        if requestType == "JOINCIRCUIT":
            Transmission.joinCircuit(data, sender)
            Transmission.reply(requestType, sender)

    def ownPacketHandler(data, sender):
        global temp_pubKey, temp_CircuitID, temp_ExitIP
        #[timestamp, "DATA", destinationID, [msgID, circuitID, publicKey], payload, signature] #from another user
        #[timestamp, "DATA", destinationID, [msgID, "SERVER", serverKey] payload, signature] #from server
        timestamp = data[0]
        messageInfo = data[3]
        payload = data[4] #encrypted payload
        #payload layout [sender, contents]
        try:
            sender = payload[0]
            contents = payload[1]
            if sender == "SERVER":
                senderKeys = serverKey
            else:
                senderKeys = database.getKeys(sender)
            
            if senderKeys == (None, None):
                Transmission.nodeInfo(sender)
            
            if contents[0] == "SERVERREPLY":
                decryptedSection = Cryptography.asymDecrypt(contents[1], myPublicKey, myPrivateKey)
                Transmission.serverReply(decryptedSection)
            elif contents[0] == "INFO":
                temp_pubKey = contents[1][0]
                temp_CircuitID = contents[1][1]
                temp_ExitIP = contents[1][2]
                index = DataManipulation.linearSearch("NODEINFO", ongoingPackets)
                if index != -1:
                    ongoingPackets.pop(index)
                print(contents[1])
            else:
                pass #do nothing as the packet is invalid

        except:
            pass #packet has formatting error
    
    def serverReply(reply):
        global loginStatus, registerStatus
        print('__________' + reply + '__________')
        if reply == "LOGIN:SUCCESS":
            index = DataManipulation.linearSearch("LOGIN", ongoingPackets)
            if index != -1:
                ongoingPackets.pop(index)
            loginStatus = True
        elif reply == "LOGIN:FAIL":
            index = DataManipulation.linearSearch("LOGIN", ongoingPackets)
            if index != -1:
                ongoingPackets.pop(index)
            loginStatus = False
        elif reply == "REGISTER:SUCCESS":
            index = DataManipulation.linearSearch("REGISTER", ongoingPackets)
            if index != -1:
                ongoingPackets.pop(index)
            registerStatus = True
        elif reply == "REGISTER:FAIL":
            index = DataManipulation.linearSearch("REGISTER", ongoingPackets)
            if index != -1:
                ongoingPackets.pop(index)
            registerStatus = False

    def joinCircuit(data, sender):
        #[timestamp, "REQUEST:JOINCIRCUIT", circuitID, publicKey, signature]
        timestamp = data[0]
        CircuitID = data[2]
        publicKey = data[3]
        signature = data.pop(4)
        testData = pickle.dumps(data)
        chance = random.randint(1, RANDOM_CONST)
        if (chance == 1) or (time.time() > timestamp + TIMEOUT - 20):
            nonOwnCircuits.append(NonOwnCircuit(CircuitID, publicKey, True))
        else:
            nonOwnCircuits.append(NonOwnCircuit(CircuitID, publicKey, False))

    def wait(startTime, msgID, length=60):
        global ongoingPackets, packetFailure
        loadingStrings = ["Waiting for reply --- |", "Waiting for reply --- /", "Waiting for reply --- -", "Waiting for reply --- \\"]
        while (startTime + length) > time.time():    
            for x in range(4):
                print(loadingStrings[x], end='\r')
                if (startTime + length) < time.time():
                    print("                        ", end='\r') #clear last line
                    return 'TIMEOUT'
                elif msgID not in ongoingPackets:
                    print("                        ", end='\r') #clear last line
                    return True
                elif packetFailure == True:
                    packetFailure = False
                    print("                        ", end='\r')
                    return 'PACKET_FAIL'
                time.sleep(0.5)
        print("                        ", end='\r') #clear last line
        index = DataManipulation.linearSearch(msgID, ongoingPackets)
        if index != -1:
            ongoingPackets.pop(index) #to avoid double messageID occurrence after timeout
        return False

### DIRECT PACKETS

    def testServer():
        startTime = time.time()
        ongoingPackets.append("TEST")
        Transmission.send(pickle.dumps([time.time(), "TEST"]), serverIP)
        sendWait = Transmission.wait(startTime, "TEST", 10)

    def getCircuitIP(DestinationID):
        pass

    def reply(msgID, sender):
        msg = [time.time(), "REPLY:" + msgID, sender]
        Transmission.send(msg, sender)

    def getNodes():
        global ongoingPackets
        print("Getting Nodes...")
        timestamp = time.time() #unix time
        msg = [timestamp, "GETNODES"]
        msg = pickle.dumps(msg)
        ongoingPackets.append("GETNODES")
        while True:
            Transmission.send(msg, serverIP)
            if Transmission.wait(timestamp, "GETNODES") == True:
                break

class DataManipulation():
    def linearSearch(val, array): #linear search algorithm for finding the index of a specified value within an array, used for unsorted lists
        result = None
        for x in range(len(array)):
            if array[x] == val:
                result = x
        if result == None:
            return -1
        else:
            return result

    def decToBin(val): #converts decimal to binary
        global binresult
        binresult = "" #as the variable is set as global, it must be emptied before each use
        def main(val): #advanced nested function, to allow recursion of a specified part of the code to run while excluding others
            global binresult
            if val > 1:
                main(val//2) #recursive section, continues until a zero is reached
            binresult = binresult + str(val%2)
        main(val) #executes recursive function

        if len(binresult) < 6: #changes the result to a six-bit binary integer, as a minimum
            add = (6 - len(binresult))
            zeroes = ""
            for x in range(add):
                zeroes = zeroes + "0"
            binresult = zeroes + binresult
        return binresult

    def binToDec(val): #converts unsigned integer binary to decimal
        length = len(val)
        result = 0
        for x in range(length): #iterates through each bit in a given binary value
            if val[x] == "1":
                result = result + (2**(length - (x + 1))) #adds the calculated denary value of the point to the result variable
        return result
###  
    def base64ToDec(val): #converts Base64 to Decimal
        global base64Chars
        result = "" #initialise local variable 'result' as empty string to allow concatenation
        for x in range(len(val)): #iterates through all characters in the specified value
            if val[x] == "=": #buffer
                pass
            else:
                temp = DataManipulation.linearSearch(val[x], base64Chars) # get decimal value of base64 character
                result = result + DataManipulation.decToBin(temp)
        result = DataManipulation.binToDec(result)
        return result
###
    def decToHex(val): #converts a decimal value to hexadecimal
        global hexChars
        modVal = val % 16
        tempVal = val // 16
        if tempVal == 0:
            return hexChars[modVal] #the final value is returned if it is divisible by 16 without remainder
        else:
            return DataManipulation.decToHex(tempVal) + hexChars[modVal] #using recursion, the algorithm passes through each hexadecimal digit until the resulting number is divisible by 16 without remainder (and is therefore a hexadecimal)
    
def inputUnrec():
    print("ERROR: Command not recognised, please try again.\n") #exception for when commands are unrecognised by the console

def initAnim(): #to initiate loading bar, use initAnim() followed by a succession of a varied amount of progress based on program execution via loadAnim(x)
    print("|LOADING...          |") #Note: x in loadAnim(x) must add up to 20 for each individual execution of initAnim(), not more, not less
    print(" ", end='', flush=True)
    
def loadAnim(count):
    for x in range(count):
        print("#", end='', flush=True)
        time.sleep(0.075) #sleeps for an arbitrary amount

if __name__ == '__main__':
    try:
        Interface.bootstrap()
        if ProgramQuit == True:
            try:
                database.quit()
            except:
                pass
            Transmission.quit()
            quit()
    except KeyboardInterrupt:
        exit()
