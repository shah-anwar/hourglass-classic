import time, datetime, HGHelp, threading, pickle, random
import HGCrypto as Cryptography

base64Chars = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
                "a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z",
                "0","1","2","3","4","5","6","7","8","9","+","/","="] #all valid base64 characters, '=' is padding

class Messenger():
    def __init__(self, username, publicKey, destination, messageList):
        self.__lastDate = ''
        
        self.__username = username
        self.__publicKey = publicKey
        self.__destination = destination
        self.__messageList = messageList
        self.__restoreMessages()

        self.__nextPacket = None

        self.quitStatus = False
        print("""
 _________________________________________________
|       WELCOME TO THE HOURGLASS MESSENGER        |
|-=-=-=-=-=-=-=-=-=-=-=-=-=-=--=-=-=-=-=-=-=-=-=-=|
|Precede input with a '/' to use commands.        |
|Use '/help' to access a list of useable commands.|
|_________________________________________________|
        """)
        
        self.inputThread = threading.Thread(target = self.__getInput)
        self.inputThread.start()

    def __getInput(self):
        while self.quitStatus == False:
            #userInput = input('\033[1A' + f"|To {self.__destination}| > " + '\033[K')
            userInput = input("")
            if userInput == "":
                pass
            elif userInput[0] == "/":
                userInput = userInput[1 : : ] #remove / from start of string
                self.__command(userInput)
            else:
                self.__sendMessage(userInput)

    def __sendMessage(self, message):
        timestamp = time.time()
        self.printMessage(timestamp, message, 1)
        msg = [timestamp, "MSG", Cryptography.asymEncrypt(self.__username, self.__publicKey), Cryptography.asymEncrypt(message, self.__publicKey)]
        msg = pickle.dumps(msg)
        self.__nextPacket = msg

    def getNextPacket(self):
        temp = self.__nextPacket
        self.__nextPacket = None
        return temp

    def __command(self, command):
        print('\033[1A' + f"Running command: {command}" + '\033[K')
        #print(f"Running command: {command}")
        if (command == "quit") or (command == "exit"):
            self.__quit()
        elif command == "help":
            HGHelp.messenger_main()
        elif command == "whoami":
            print(self.__username)

    def getMessageList(self):
        return self.__messageList

    def printMessage(self, timestamp, msg, own, external=False):
        self.__messageList.append([timestamp, own, msg])
        msgTime = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%H:%M:%S')
        if own == 1:
            sender = self.__username
        else:
            sender = self.__destination
        if external == True:
            #print('\033[1A' + f"[{msgTime}] {sender}| {msg}"+ '\033[K', end='\n')
            print(f"[{msgTime}] {sender}| {msg}", end='\n')
            #print(f"|To {self.__destination}| > ")
            print("")
        else:
            print(f"[{msgTime}] {sender}| {msg}", end='\n')
            print("")
            #print('\033[1A' + f"[{msgTime}] {sender}| {msg}"+ '\033[K',  end='\n')

    def __restoreMessages(self):
        currentDate = ''
        if self.__messageList != []:
            for x in range(len(self.__messageList)):
                timestamp = self.__messageList[x][0]
                currentTime = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%H:%M:%S')
                
                ownCheck = self.__messageList[x][1]
                if ownCheck == 1:
                    sender = self.__username
                else:
                    sender = self.__destination

                message = self.__messageList[x][2]
                if currentDate != datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%A %d %B %Y'):
                    print("")
                    currentDate = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%A %d %B %Y')
                    print(f"|<==============>|{currentDate}|<==============>|")
                
                print(f"[{currentTime}] {sender}| {message}")
        self.__lastDate = currentDate

        if self.__lastDate != datetime.datetime.utcfromtimestamp(time.time()).strftime('%A %d %B %Y'):
            print("")
            self.__lastDate = datetime.datetime.utcfromtimestamp(time.time()).strftime('%A %d %B %Y')
            print(f"|<==============>|{self.__lastDate}|<==============>|")

        self.__clearMessages()

    def __clearMessages(self):
        self.__messageList = []

    def __quit(self):
        self.quitStatus = True

if __name__ == '__main__':
    print("This module must be run from within the file 'client.py'.")