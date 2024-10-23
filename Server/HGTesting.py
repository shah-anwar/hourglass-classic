import HGCrypto as Cryptography

def asymmetricEncryption(publicKey, privateKey):
    fail = False
    TEST1 = "abcdefghijklmnopqrstuvwxyz" #alphabetical character test (uppercase not required as their character code is lower than lowecase)
    TEST2 = "1234567890" #numerical character test
    TEST3 = "!£$%^&*()-_=+}{[];:''@#~,<>./?" #symbol test
    if TEST1 != Cryptography.asymDecrypt(Cryptography.asymEncrypt(TEST1, publicKey), publicKey, privateKey):
        fail = True
    if TEST2 != Cryptography.asymDecrypt(Cryptography.asymEncrypt(TEST2, publicKey), publicKey, privateKey):
        fail = True
    if TEST3 != Cryptography.asymDecrypt(Cryptography.asymEncrypt(TEST3, publicKey), publicKey, privateKey):
        fail = True
    return fail

def IPValidation(IP, PORT):
    try: #try to change port (potentially in string form) to integer
        PORT = int(PORT)
    except: #invalid port value error, the port provided has an non-numerical character within it (and cannot be converted into an integer)
        return False
    section = 0
    separatedIP = [""] * 4
    for x in range(len(IP)):
        if IP[x] == ".": #every time a dot is encountered, the algorithm begins a new section
            section += 1
        else:
            separatedIP[section] = separatedIP[section] + IP[x]
    try:
        for x in range(len(separatedIP)):
            separatedIP[x] = int(separatedIP[x]) #convert all sections of the separated IP address from string to integer form
            if (separatedIP[x] > 255) or (separatedIP[x] < 0): #checks if value within IP exceeds limit
                return False
        return True #if all checks are passed, return True (address and port are valid)
    except: #invalid character in IP address
        return False

if __name__ == '__main__':
    print("This module must be run from within the file 'client.py'.")