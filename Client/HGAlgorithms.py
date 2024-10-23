from random import randint

def primeNumberList(limit): #Sieve of Eratosthenes, prime number generation algorithm
    n = limit
    numList = [True] * int(n + 1) #creates an array with all values set to true, length of array is specified as variable 'limit'
    for x in range(int(n**0.5) - 2): #iterates through half the indexes in the list
        x = x + 2 
        if numList[x] == True:
            y = 0
            z = 0
            while True: #using indefinite iteration, the algorithm calculates whether or not a number is prime by cycling through each multiplication combination
                z = (x + y) * x
                if z < n:
                    numList[z] = False #if said number, z, has a multiple (and is therefore a non-prime) it is set to False
                    y += 1
                else:
                    break
    primeList = []
    for a in range(len(numList)): #all indexes in the list that have the value 'True' are appended to a list of prime numbers
        if numList[a] == True:
            primeList.append(a)
    primeList.remove(n)
    n = len(primeList)
    return (primeList)

primeList = primeNumberList(5000)

def primeNumberGen(limit): #selects a random prime number from the list
    global primeList
    if primeList == None:
        primeList = primeNumberList(5000)
    index = randint(3, limit - 1) #selects a random index
    return (primeList[index])

def greatestCommonDivisor(x, y): #function to return the greatest common divisor between two numbers, x and y
    if x > y: #as the function requires y to be larger than x, swap the two in case the order is opposite
        temp = y
        y = x
        x = temp
    if x == 0: #uses recursion to calculate the modulo of y against x until a result is found (when x equals zero)
        return y, 0, 1
    else:
        result, xNew, yNew = greatestCommonDivisor(y % x, x)
        return result, yNew - (y // x) * xNew, xNew

def modularInverse(x, y): #modular inverse calculation  
    try:
        result = pow(x, -1, y)
    except:
        result = ord("#")
    return result

if __name__ == '__main__':
    print("This module must be run from within the file 'client.py'.")