import HGTesting as Testing
import HGAlgorithms as Algorithms

primeList = Algorithms.primeNumberList(1000)

def hash(data):
    try:
        data = data.decode("utf-16")
    except:
        pass
    total = 0
    for x in range(len(data)):
        try:
            total = total + (ord(str(data[x])) * x)
        except:
            total = total + x
    return total

def sign(data, privateKey):
    n, d = privateKey
    hashVal = hash(data)
    sig = pow(hashVal, d, n)
    return sig

def verify(data, sig, publicKey):
    n, e = publicKey
    hashVal = hash(data)
    checkSig = pow(sig, e, n)
    if hashVal == checkSig:
        return True
    else:
        return False

########

def asymKeyGen(length):
    while True:
        while True: #prime number selection loop
            prime1 = Algorithms.primeNumberGen(length)
            prime2 = Algorithms.primeNumberGen(length)
            if (prime1 != prime2) and (prime1 != 1) and (prime2 != 1):
                break

        n = prime1 * prime2

        phiN = (prime1 - 1) * (prime2 - 1) #Euler's Totient Function
        lambdaN = int(phiN/Algorithms.greatestCommonDivisor(prime1 - 1, prime2 - 2)[0]) #Carmichael's Lambda Function

        first = True
        index = 2
        e = primeList[index]

        while (first == True) or (Algorithms.greatestCommonDivisor(n, e)[0] != 1) or (Algorithms.greatestCommonDivisor(lambdaN, e)[0] != 1):
            first = False
            e = primeList[index]
            index += 1

        publicKey = (n, e)
        d = Algorithms.modularInverse(e, lambdaN)
        privateKey = (n, d)
        if d < 1:
            pass
        elif e != d:
            if Testing.asymmetricEncryption(publicKey, privateKey) == False:
                break
            else:
                pass
    return publicKey, privateKey

def asymEncrypt(data, PublicKey):
    n, e = PublicKey
    data = str(data)
    cipherData = ""
    for x in range(len(data)):
        cipherData = cipherData + chr(Algorithms.modularInverse(ord(data[x]) ** e, n))
    return cipherData

def asymDecrypt(cipherData, PublicKey, PrivateKey):
    n1, e = PublicKey
    n2, d = PrivateKey
    if n1 == n2:
        n = n1
    else:
        print("Error: Keypair does not match!")
        return -1
    data = ""
    for x in range(len(cipherData)):
        data = data + str(chr(Algorithms.modularInverse(ord(cipherData[x]) ** d, n)))
    return data

if __name__ == '__main__':
    print("This module must be run from within the file 'client.py'.")